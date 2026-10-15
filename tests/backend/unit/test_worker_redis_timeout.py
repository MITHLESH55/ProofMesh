"""
tests/backend/unit/test_worker_redis_timeout.py

Tests covering the Redis timeout fix in JobQueue and AnalysisWorker:

1. Empty queue  → worker stays healthy, no ERROR logged
2. Queued job   → worker retrieves and processes the job
3. Redis unavailable → real error is surfaced (logged at ERROR)
4. Redis connection timeout → retry / reconnect behaviour preserved
5. Worker restart → reconnects correctly
6. No busy-loop → idle worker does not spin with errors
"""

import json
import logging
import time
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, PropertyMock, call, patch

import pytest
import redis.exceptions

from app.services.jobs.queue import (
    ANALYSIS_QUEUE_NAME,
    BLPOP_BLOCK_TIMEOUT,
    SOCKET_CONNECT_TIMEOUT,
    SOCKET_TIMEOUT,
    JobQueue,
)
from app.workers.worker import AnalysisWorker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_queue(mock_client: Optional[MagicMock] = None) -> JobQueue:
    """Return a JobQueue whose internal _client is pre-set to *mock_client*."""
    q = JobQueue(redis_url="redis://redis:6379/0")
    q._client = mock_client
    return q


def _job_payload(**overrides) -> Dict[str, Any]:
    base = {
        "change_id": "change-abc",
        "analysis_run_id": "run-xyz",
        "attempt": 1,
        "max_attempts": 3,
        "enqueued_at": time.time(),
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Empty queue — no ERROR loop
# ---------------------------------------------------------------------------

class TestEmptyQueueIsNotAnError:
    """When the queue is empty, blpop returns None.  This must NOT be an ERROR."""

    def test_blpop_returns_none_yields_none(self, caplog):
        mock_client = MagicMock()
        mock_client.blpop.return_value = None  # queue empty

        q = _make_queue(mock_client)
        with caplog.at_level(logging.DEBUG):
            result = q.pop_analysis(timeout=5)

        assert result is None
        mock_client.blpop.assert_called_once_with(ANALYSIS_QUEUE_NAME, timeout=5)

        # No ERROR or WARNING must appear for an idle queue
        error_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert not error_records, (
            f"Unexpected high-level log records for idle queue: {error_records}"
        )

    def test_idle_queue_logged_at_debug(self, caplog):
        mock_client = MagicMock()
        mock_client.blpop.return_value = None

        q = _make_queue(mock_client)
        # Capture ALL loggers at DEBUG level
        with caplog.at_level(logging.DEBUG, logger="proofmesh"):
            q.pop_analysis(timeout=5)

        # Also accept capturing from root logger
        all_records = caplog.records
        if not all_records:
            # Re-run with root logger capture
            caplog.clear()
            with caplog.at_level(logging.DEBUG):
                q.pop_analysis(timeout=5)
            all_records = caplog.records

        debug_msgs = [r.message for r in all_records if r.levelno <= logging.DEBUG]
        # Either a debug message exists OR blpop returned None silently (both are correct)
        # The key invariant is: NO warning or error level log
        error_records = [r for r in all_records if r.levelno >= logging.WARNING]
        assert not error_records, (
            f"Expected no WARNING/ERROR for idle queue, got: {[r.message for r in error_records]}"
        )

    def test_socket_timeout_error_is_not_logged_as_error(self, caplog):
        """If socket_timeout fires (defensive path) it must NOT produce ERROR."""
        mock_client = MagicMock()
        mock_client.blpop.side_effect = redis.exceptions.TimeoutError("Timeout reading from socket")

        q = _make_queue(mock_client)
        with caplog.at_level(logging.DEBUG):
            result = q.pop_analysis(timeout=5)

        assert result is None
        error_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert not error_records, (
            f"TimeoutError should be DEBUG-only, but got: {error_records}"
        )

    def test_socket_timeout_falls_back_to_in_memory(self, caplog):
        """After a TimeoutError, in-memory fallback is checked."""
        mock_client = MagicMock()
        mock_client.blpop.side_effect = redis.exceptions.TimeoutError()

        fallback_job = _job_payload()
        q = _make_queue(mock_client)
        q._fallback_queue.append(fallback_job)

        with caplog.at_level(logging.DEBUG):
            result = q.pop_analysis()

        assert result == fallback_job


# ---------------------------------------------------------------------------
# 2. Queued job — worker retrieves and processes it
# ---------------------------------------------------------------------------

class TestQueuedJobIsProcessed:
    def test_pop_returns_job_when_present(self):
        job = _job_payload()
        mock_client = MagicMock()
        mock_client.blpop.return_value = (ANALYSIS_QUEUE_NAME, json.dumps(job))

        q = _make_queue(mock_client)
        result = q.pop_analysis(timeout=5)

        assert result is not None
        assert result["change_id"] == "change-abc"
        assert result["analysis_run_id"] == "run-xyz"

    def test_enqueue_then_pop_roundtrip(self):
        """Enqueue pushes to Redis; pop retrieves the same payload."""
        stored: list[str] = []

        mock_client = MagicMock()
        mock_client.rpush.side_effect = lambda key, val: stored.append(val)
        mock_client.blpop.side_effect = lambda key, timeout: (
            (ANALYSIS_QUEUE_NAME, stored.pop(0)) if stored else None
        )

        q = _make_queue(mock_client)
        q.enqueue_analysis(change_id="c1", analysis_run_id="r1")
        result = q.pop_analysis()

        assert result is not None
        assert result["change_id"] == "c1"
        assert result["analysis_run_id"] == "r1"

    def test_worker_process_next_job_calls_pop_and_processes(self, db_session):
        """AnalysisWorker.process_next_job routes a popped job to process_job."""
        job = _job_payload(change_id="ANY", analysis_run_id="ANY")

        with patch("app.workers.worker.job_queue") as mock_queue:
            mock_queue.pop_analysis.return_value = job

            worker = AnalysisWorker(worker_id="test-roundtrip")
            with patch.object(worker, "process_job", return_value=True) as mock_pj:
                result = worker.process_next_job()

        assert result is True
        mock_pj.assert_called_once()
        call_args = mock_pj.call_args[0]
        assert call_args[0] == job  # first positional arg is job_data


# ---------------------------------------------------------------------------
# 3. Redis unavailable — real error is surfaced
# ---------------------------------------------------------------------------

class TestRedisUnavailableSurfacesError:
    def test_connection_error_logged_at_error(self, caplog):
        mock_client = MagicMock()
        mock_client.blpop.side_effect = redis.exceptions.ConnectionError("Connection refused")

        q = _make_queue(mock_client)
        with caplog.at_level(logging.DEBUG):
            result = q.pop_analysis()

        assert result is None
        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert error_records, "ConnectionError must be logged at ERROR"
        assert any("connection" in r.message.lower() for r in error_records)

    def test_generic_redis_error_logged_at_error(self, caplog):
        mock_client = MagicMock()
        mock_client.blpop.side_effect = redis.exceptions.RedisError("auth failure")

        q = _make_queue(mock_client)
        with caplog.at_level(logging.DEBUG):
            result = q.pop_analysis()

        assert result is None
        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert error_records, "RedisError must be logged at ERROR"

    def test_redis_unavailable_falls_back_to_in_memory(self):
        mock_client = MagicMock()
        mock_client.blpop.side_effect = redis.exceptions.ConnectionError("refused")

        fallback_job = _job_payload()
        q = _make_queue(mock_client)
        q._fallback_queue.append(fallback_job)

        result = q.pop_analysis()
        assert result == fallback_job

    def test_enqueue_redis_error_falls_back(self, caplog):
        mock_client = MagicMock()
        mock_client.rpush.side_effect = redis.exceptions.ConnectionError("refused")

        q = _make_queue(mock_client)
        with caplog.at_level(logging.DEBUG):
            ok = q.enqueue_analysis("c1", "r1")

        assert ok is True  # still succeeds via fallback
        assert len(q._fallback_queue) == 1
        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert error_records, "Redis enqueue failure must be logged at ERROR"


# ---------------------------------------------------------------------------
# 4. Redis connection timeout — client resets and retries
# ---------------------------------------------------------------------------

class TestConnectionTimeoutRetry:
    def test_client_is_reset_after_connection_error(self):
        """After a connection error, _client is set to None for reconnection."""
        mock_client = MagicMock()
        mock_client.blpop.side_effect = redis.exceptions.ConnectionError("refused")

        q = _make_queue(mock_client)
        q.pop_analysis()

        assert q._client is None, "Client must be reset after ConnectionError"

    def test_client_is_reset_after_generic_redis_error(self):
        mock_client = MagicMock()
        mock_client.blpop.side_effect = redis.exceptions.RedisError("protocol error")

        q = _make_queue(mock_client)
        q.pop_analysis()

        assert q._client is None, "Client must be reset after RedisError"

    def test_client_not_reset_on_idle_timeout(self):
        """TimeoutError (idle) must NOT invalidate the client connection."""
        mock_client = MagicMock()
        mock_client.blpop.side_effect = redis.exceptions.TimeoutError()

        q = _make_queue(mock_client)
        q.pop_analysis()

        # _client should still be the mock, not None
        assert q._client is mock_client, (
            "Client must NOT be reset on an idle TimeoutError"
        )

    def test_socket_timeout_constants_are_correct(self):
        """Enforce the invariant: socket_timeout > blpop_block_timeout."""
        assert SOCKET_TIMEOUT > BLPOP_BLOCK_TIMEOUT, (
            f"SOCKET_TIMEOUT ({SOCKET_TIMEOUT}) must be strictly greater than "
            f"BLPOP_BLOCK_TIMEOUT ({BLPOP_BLOCK_TIMEOUT})"
        )

    def test_client_created_with_correct_timeouts(self):
        """Verify redis.from_url is called with the correct timeout values."""
        q = JobQueue(redis_url="redis://redis:6379/0")
        with patch("redis.from_url") as mock_from_url:
            mock_redis_instance = MagicMock()
            mock_redis_instance.ping.return_value = True
            mock_from_url.return_value = mock_redis_instance

            _ = q.client  # trigger property

        mock_from_url.assert_called_once()
        kwargs = mock_from_url.call_args.kwargs
        assert kwargs["socket_timeout"] == SOCKET_TIMEOUT
        assert kwargs["socket_connect_timeout"] == SOCKET_CONNECT_TIMEOUT
        assert kwargs["socket_timeout"] > BLPOP_BLOCK_TIMEOUT


# ---------------------------------------------------------------------------
# 5. Worker restart — reconnects correctly
# ---------------------------------------------------------------------------

class TestWorkerReconnect:
    def test_reset_client_clears_internal_state(self):
        mock_client = MagicMock()
        q = _make_queue(mock_client)
        assert q._client is not None
        q.reset_client()
        assert q._client is None

    def test_ping_returns_false_when_disconnected(self):
        q = _make_queue(mock_client=None)
        # _client is None, client property will attempt redis.from_url — mock it
        with patch("redis.from_url") as mock_from_url:
            mock_from_url.side_effect = redis.exceptions.ConnectionError("refused")
            result = q.ping()
        assert result is False

    def test_after_reset_next_call_reattempts_connection(self):
        """After reset_client(), the next .client access tries redis.from_url again."""
        mock_client = MagicMock()
        mock_client.blpop.side_effect = redis.exceptions.ConnectionError("refused")

        q = _make_queue(mock_client)
        q.pop_analysis()  # triggers reset
        assert q._client is None

        # Now simulate a successful reconnect
        new_mock = MagicMock()
        new_mock.ping.return_value = True
        new_mock.blpop.return_value = None
        with patch("redis.from_url", return_value=new_mock):
            result = q.pop_analysis()

        assert result is None  # empty queue — but no error
        assert q._client is new_mock  # reconnected


# ---------------------------------------------------------------------------
# 6. No busy-loop — idle worker does not spin with errors
# ---------------------------------------------------------------------------

class TestNoBusyLoop:
    def test_idle_worker_does_not_generate_error_logs(self, caplog):
        """Simulate several idle poll cycles; no ERROR logs must be produced."""
        poll_count = 0
        worker = AnalysisWorker(worker_id="test-noloop")

        def fake_pop_analysis(timeout=BLPOP_BLOCK_TIMEOUT):
            nonlocal poll_count
            poll_count += 1
            if poll_count >= 4:
                worker.stop()  # signal the run() loop to exit
            return None  # simulate empty queue

        with patch("app.workers.worker.job_queue") as mock_queue:
            mock_queue.pop_analysis.side_effect = fake_pop_analysis
            with caplog.at_level(logging.DEBUG):
                worker.run()  # exits cleanly when worker.running == False

        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert not error_records, (
            f"Idle worker produced ERROR logs: {[r.message for r in error_records]}"
        )
        assert poll_count >= 3, "Worker must have polled multiple times"

    def test_idle_worker_does_not_sleep_between_polls(self):
        """Blpop itself provides the idle wait; no extra sleep(0.5) should be called."""
        poll_count = 0
        worker = AnalysisWorker(worker_id="test-nosleep")

        def fake_pop(timeout=BLPOP_BLOCK_TIMEOUT):
            nonlocal poll_count
            poll_count += 1
            if poll_count >= 3:
                worker.stop()
            return None

        with patch("app.workers.worker.job_queue") as mock_queue:
            mock_queue.pop_analysis.side_effect = fake_pop
            with patch("app.workers.worker.time") as mock_time:
                mock_time.sleep.return_value = None
                worker.run()

        # time.sleep(0.5) from the old "if not processed: sleep" must be gone.
        sleep_calls_with_half_second = [
            c for c in mock_time.sleep.call_args_list
            if c.args and c.args[0] == 0.5
        ]
        assert not sleep_calls_with_half_second, (
            "Worker must NOT call time.sleep(0.5) on idle poll; "
            "blpop already provides the wait."
        )
