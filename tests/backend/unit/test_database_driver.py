"""
tests/backend/unit/test_database_driver.py

Regression tests for the PostgreSQL driver fix:
- psycopg2 package importable
- SQLAlchemy URL uses correct driver
- Alembic configuration loads
- schema validator
- worker DB connection failure handling
"""

import importlib
import os
import sys

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# 1. psycopg2 importable
# ---------------------------------------------------------------------------

class TestPsycopg2Import:
    def test_psycopg2_is_importable(self):
        """psycopg2 (or psycopg2-binary) must be importable inside the test env."""
        psycopg2 = importlib.import_module("psycopg2")
        assert psycopg2 is not None

    def test_psycopg2_has_version(self):
        import psycopg2
        # psycopg2 exposes __version__ or apilevel
        assert hasattr(psycopg2, "__version__") or hasattr(psycopg2, "apilevel")

    def test_psycopg2_connect_callable(self):
        import psycopg2
        assert callable(psycopg2.connect)


# ---------------------------------------------------------------------------
# 2. SQLAlchemy URL uses the correct driver
# ---------------------------------------------------------------------------

class TestSQLAlchemyURL:
    def test_default_config_uses_psycopg2_dialect(self):
        """The default DATABASE_URL must explicitly specify the psycopg2 driver."""
        from app.core.config import Settings
        # Create a fresh settings object without env overrides to check the default
        s = Settings(
            _env_file=None,  # type: ignore[call-arg]
        )
        url = s.DATABASE_URL
        assert "psycopg2" in url or url.startswith("sqlite"), (
            f"Default DATABASE_URL must use psycopg2 dialect, got: {url!r}"
        )

    def test_docker_url_must_not_be_bare_postgresql(self):
        """
        A bare 'postgresql://' URL without a driver suffix causes SQLAlchemy 2.x
        to probe psycopg3 first, which fails if only psycopg2 is installed.
        Ensure the URL set in tests/Docker always includes an explicit driver.
        """
        test_url = os.environ.get("DATABASE_URL", "")
        if test_url.startswith("postgresql"):
            # Must have an explicit driver suffix
            assert "+" in test_url, (
                f"DATABASE_URL must include explicit driver (e.g. postgresql+psycopg2://), "
                f"got bare: {test_url!r}"
            )

    def test_sqlite_url_is_allowed_for_tests(self):
        """Tests using SQLite in-memory are fine and should not fail this check."""
        from tests.conftest import TEST_DATABASE_URL
        assert TEST_DATABASE_URL.startswith("sqlite"), (
            "Test suite must use SQLite in-memory for unit tests"
        )

    def test_sqlalchemy_engine_creates_with_psycopg2_url(self):
        """Verify create_engine accepts a psycopg2 URL without raising ImportError."""
        from sqlalchemy import create_engine
        # We don't actually connect — just confirm the engine can be constructed
        # with a psycopg2 URL (driver registration check)
        try:
            engine = create_engine(
                "postgresql+psycopg2://user:pass@localhost:5432/db",
                # Don't pool, don't connect
                pool_pre_ping=False,
            )
            assert engine.dialect.name == "postgresql"
            assert "psycopg2" in str(type(engine.dialect).__module__)
        except ImportError as e:
            pytest.fail(f"psycopg2 driver not available for SQLAlchemy: {e}")


# ---------------------------------------------------------------------------
# 3. Alembic env.py can load without error
# ---------------------------------------------------------------------------

class TestAlembicEnvLoad:
    def test_alembic_config_loads(self):
        """alembic.ini can be found and parsed from the backend directory."""
        from alembic.config import Config as AlembicConfig
        import os

        backend_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../backend")
        )
        alembic_ini = os.path.join(backend_dir, "alembic.ini")
        assert os.path.exists(alembic_ini), f"alembic.ini not found at {alembic_ini}"

        cfg = AlembicConfig(alembic_ini)
        # The ini should have a sqlalchemy.url option
        url = cfg.get_main_option("sqlalchemy.url")
        assert url is not None and url.startswith("postgresql"), (
            f"alembic.ini sqlalchemy.url should be a postgresql URL, got: {url!r}"
        )

    def test_alembic_metadata_imports_models(self):
        """Importing models should not raise ImportError — all models must be discoverable."""
        try:
            import app.models  # noqa: F401
            from app.db.session import Base
            # All model tables should be registered
            assert len(Base.metadata.tables) > 0, (
                "No tables found in Base.metadata — model import may have failed"
            )
        except ImportError as e:
            pytest.fail(f"Model import failed: {e}")

    def test_alembic_versions_exist(self):
        """At least one migration version file must exist."""
        import os
        backend_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../backend")
        )
        versions_dir = os.path.join(backend_dir, "alembic", "versions")
        assert os.path.isdir(versions_dir), f"Alembic versions dir not found: {versions_dir}"
        migration_files = [
            f for f in os.listdir(versions_dir) if f.endswith(".py") and not f.startswith("_")
        ]
        assert len(migration_files) >= 1, (
            f"Expected at least 1 migration in {versions_dir}, found {migration_files}"
        )

    def test_alembic_revision_identifiers_fit_in_alembic_version_table(self):
        """
        Alembic's default alembic_version.version_num column is VARCHAR(32).
        Any revision string longer than 32 characters causes PostgreSQL to throw:
        psycopg2.errors.StringDataRightTruncation: value too long for type character varying(32)
        All revision IDs and down_revisions MUST be <= 32 characters.
        """
        import os
        import re

        backend_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../backend")
        )
        versions_dir = os.path.join(backend_dir, "alembic", "versions")
        migration_files = [
            f for f in os.listdir(versions_dir) if f.endswith(".py") and not f.startswith("_")
        ]

        for mf in migration_files:
            file_path = os.path.join(versions_dir, mf)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            rev_match = re.search(r'revision\s*:\s*str\s*=\s*["\']([^"\']+)["\']', content)
            if rev_match:
                rev_id = rev_match.group(1)
                assert len(rev_id) <= 32, (
                    f"Migration {mf} has revision {rev_id!r} with length {len(rev_id)} > 32 characters! "
                    f"Must be <= 32 to fit in alembic_version.version_num column."
                )

            down_match = re.search(r'down_revision\s*:\s*Union\[[^\]]+\]\s*=\s*["\']([^"\']+)["\']', content)
            if down_match:
                down_rev = down_match.group(1)
                assert len(down_rev) <= 32, (
                    f"Migration {mf} has down_revision {down_rev!r} with length {len(down_rev)} > 32 characters!"
                )


# ---------------------------------------------------------------------------
# 4. Required schema tables exist (SQLite in-memory)
# ---------------------------------------------------------------------------

class TestSchemaExistence:
    def test_required_tables_exist_in_test_db(self, db_session):
        """After Base.metadata.create_all (done in conftest), key tables must exist."""
        from sqlalchemy import inspect
        inspector = inspect(db_session.bind)
        table_names = inspector.get_table_names()

        required_tables = [
            "changes",
            "organizations",
            "repositories",
            "pull_requests",
            "analysis_runs",
            "users",
            "audit_logs",
        ]
        missing = [t for t in required_tables if t not in table_names]
        assert not missing, (
            f"Required tables missing from schema: {missing}\n"
            f"Existing tables: {table_names}"
        )

    def test_changes_table_has_expected_columns(self, db_session):
        """The changes table must have the core columns the worker queries."""
        from sqlalchemy import inspect, text
        inspector = inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("changes")}

        required_columns = {"id", "pull_request_id", "commit_sha", "status"}
        missing = required_columns - columns
        assert not missing, (
            f"'changes' table missing columns: {missing}\n"
            f"Existing columns: {columns}"
        )


# ---------------------------------------------------------------------------
# 5. Worker handles DB connection failure correctly
# ---------------------------------------------------------------------------

class TestWorkerDBFailureHandling:
    def test_worker_process_job_returns_false_on_missing_entities(self, db_session):
        """Worker returns False gracefully when change/run IDs don't exist."""
        from app.workers.worker import AnalysisWorker

        worker = AnalysisWorker(worker_id="test-db-failure")
        job = {
            "change_id": "nonexistent-change-id",
            "analysis_run_id": "nonexistent-run-id",
            "attempt": 1,
            "max_attempts": 3,
        }
        result = worker.process_job(job, db_session)
        assert result is False

    def test_worker_handles_invalid_job_payload(self, db_session):
        """Worker returns False for completely missing required fields."""
        from app.workers.worker import AnalysisWorker

        worker = AnalysisWorker(worker_id="test-invalid-payload")
        # Missing change_id and analysis_run_id
        result = worker.process_job({}, db_session)
        assert result is False

    def test_worker_handles_malformed_job_payload(self, db_session):
        """Worker handles partial/malformed job data without raising."""
        from app.workers.worker import AnalysisWorker

        worker = AnalysisWorker(worker_id="test-malformed")
        result = worker.process_job({"change_id": None, "analysis_run_id": None}, db_session)
        assert result is False


# ---------------------------------------------------------------------------
# 6. Redis idle polling remains clean (driver fix regression)
# ---------------------------------------------------------------------------

class TestRedisIdlePollAfterDriverFix:
    def test_queue_pop_idle_returns_none_not_error(self):
        """After the driver fix, queue pop on idle queue returns None cleanly."""
        from unittest.mock import MagicMock
        import redis.exceptions
        from app.services.jobs.queue import JobQueue, ANALYSIS_QUEUE_NAME

        mock_client = MagicMock()
        mock_client.blpop.return_value = None  # empty queue

        q = JobQueue(redis_url="redis://redis:6379/0")
        q._client = mock_client

        result = q.pop_analysis(timeout=5)
        assert result is None
        mock_client.blpop.assert_called_once_with(ANALYSIS_QUEUE_NAME, timeout=5)

    def test_queue_pop_job_returns_correct_payload(self):
        """Queued job pop returns the correct deserialized payload."""
        import json
        import time
        from unittest.mock import MagicMock
        from app.services.jobs.queue import JobQueue, ANALYSIS_QUEUE_NAME

        job = {
            "change_id": "c1",
            "analysis_run_id": "r1",
            "attempt": 1,
            "max_attempts": 3,
            "enqueued_at": time.time(),
        }
        mock_client = MagicMock()
        mock_client.blpop.return_value = (ANALYSIS_QUEUE_NAME, json.dumps(job))

        q = JobQueue(redis_url="redis://redis:6379/0")
        q._client = mock_client

        result = q.pop_analysis(timeout=5)
        assert result is not None
        assert result["change_id"] == "c1"
        assert result["analysis_run_id"] == "r1"
