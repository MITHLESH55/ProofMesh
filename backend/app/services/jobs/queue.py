import json
import time
from typing import Any, Dict, Optional

import redis
import redis.exceptions

from app.core.config import settings
from app.core.logging import logger

ANALYSIS_QUEUE_NAME = "proofmesh:queue:analysis"

# ── Timeout constants ──────────────────────────────────────────────────────────
# BLPOP_BLOCK_TIMEOUT: how long Redis holds the connection open while waiting
# for an item.  When the queue is idle this is the normal "polling interval".
BLPOP_BLOCK_TIMEOUT: int = 5

# SOCKET_TIMEOUT must be STRICTLY GREATER than BLPOP_BLOCK_TIMEOUT.
# If socket_timeout <= blpop timeout, the TCP socket fires while Redis is still
# legitimately blocking, producing "Timeout reading from socket" every cycle.
# 30 s gives a comfortable 25 s safety margin.
SOCKET_TIMEOUT: float = 30.0

# Fast initial connection timeout so startup mis-configuration fails quickly.
SOCKET_CONNECT_TIMEOUT: float = 5.0
# ──────────────────────────────────────────────────────────────────────────────


class JobQueue:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._client: Optional[redis.Redis] = None
        self._fallback_queue: list[Dict[str, Any]] = []

    @property
    def client(self) -> Optional[redis.Redis]:
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    socket_timeout=SOCKET_TIMEOUT,
                    socket_connect_timeout=SOCKET_CONNECT_TIMEOUT,
                    decode_responses=True,
                )
                self._client.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
            except redis.exceptions.RedisError as e:
                logger.warning(
                    f"Could not connect to Redis at {self.redis_url}: {e}. "
                    "Using in-memory fallback queue."
                )
                self._client = None
        return self._client

    def reset_client(self) -> None:
        """Force a fresh connection attempt on next access."""
        self._client = None

    def ping(self) -> bool:
        try:
            c = self.client
            return c is not None and bool(c.ping())
        except redis.exceptions.RedisError:
            return False

    def enqueue_analysis(
        self,
        change_id: str,
        analysis_run_id: str,
        attempt: int = 1,
        max_attempts: int = 3,
    ) -> bool:
        job_data = {
            "change_id": change_id,
            "analysis_run_id": analysis_run_id,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "enqueued_at": time.time(),
        }
        payload = json.dumps(job_data)

        try:
            if self.client:
                self.client.rpush(ANALYSIS_QUEUE_NAME, payload)
                logger.info(
                    f"Enqueued analysis job {analysis_run_id} for change {change_id} "
                    f"(attempt {attempt}) to Redis"
                )
                return True
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis enqueue failed: {e}. Pushing to in-memory fallback queue.")
            self.reset_client()

        self._fallback_queue.append(job_data)
        logger.info(f"Enqueued analysis job {analysis_run_id} to in-memory fallback queue")
        return True

    def pop_analysis(self, timeout: int = BLPOP_BLOCK_TIMEOUT) -> Optional[Dict[str, Any]]:
        """
        Blocking pop the next analysis job.

        Normal idle behaviour (empty queue, blpop timeout expires) returns None
        and is logged at DEBUG — NOT an error.

        Real Redis failures (connection refused, auth error, protocol error,
        network split) are logged at ERROR and trigger a client reset so the
        next call attempts reconnection.
        """
        try:
            if self.client:
                res = self.client.blpop(ANALYSIS_QUEUE_NAME, timeout=timeout)
                if res:
                    _, payload = res
                    return json.loads(payload)
                # res is None → blpop timed out; queue is simply empty — normal.
                logger.debug(
                    f"Queue idle: no job in {timeout}s (normal when queue is empty)"
                )
                # Fall through to check in-memory fallback below.

        except redis.exceptions.TimeoutError:
            # socket_timeout fired before blpop returned — should not happen with
            # socket_timeout >> blpop timeout, but handle defensively.
            # This is still normal-idle behaviour, NOT a Redis failure.
            logger.debug(
                "BLPOP socket read timed out (socket_timeout margin hit); "
                "queue considered idle."
            )
            # Fall through to check in-memory fallback below.

        except redis.exceptions.ConnectionError as e:
            # Real connectivity failure — surface it clearly.
            logger.error(f"Redis connection error during pop: {e}")
            self.reset_client()

        except redis.exceptions.RedisError as e:
            # Protocol / auth / other genuine Redis error.
            logger.error(f"Redis error during pop: {e}")
            self.reset_client()

        # Redis unavailable or queue idle — drain in-memory fallback if populated.
        if self._fallback_queue:
            return self._fallback_queue.pop(0)

        return None


job_queue = JobQueue()
