import json
import time
from typing import Any, Dict, Optional
import redis
from app.core.config import settings
from app.core.logging import logger

ANALYSIS_QUEUE_NAME = "proofmesh:queue:analysis"


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
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,
                    decode_responses=True,
                )
                self._client.ping()
            except Exception as e:
                logger.warning(f"Could not connect to Redis at {self.redis_url}: {str(e)}. Using fallback in-memory queue.")
                self._client = None
        return self._client

    def ping(self) -> bool:
        try:
            c = self.client
            return c is not None and c.ping()
        except Exception:
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
                logger.info(f"Enqueued analysis job {analysis_run_id} for change {change_id} (attempt {attempt}) to Redis")
                return True
        except Exception as e:
            logger.error(f"Redis enqueue failed: {str(e)}. Pushing to fallback queue.")

        self._fallback_queue.append(job_data)
        logger.info(f"Enqueued analysis job {analysis_run_id} to in-memory fallback queue")
        return True

    def pop_analysis(self, timeout: int = 2) -> Optional[Dict[str, Any]]:
        try:
            if self.client:
                res = self.client.blpop(ANALYSIS_QUEUE_NAME, timeout=timeout)
                if res:
                    _, payload = res
                    return json.loads(payload)
        except Exception as e:
            logger.error(f"Redis pop failed: {str(e)}")

        if self._fallback_queue:
            return self._fallback_queue.pop(0)

        return None


job_queue = JobQueue()
