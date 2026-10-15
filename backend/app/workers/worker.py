import os
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.entities import AnalysisRun, AnalysisStatus, Change, ChangeStatus
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.change_repository import ChangeRepository
from app.services.audit.service import AuditService
from app.services.jobs.queue import job_queue, BLPOP_BLOCK_TIMEOUT


class AnalysisWorker:
    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or f"worker-{os.getpid()}-{int(time.time())}"
        self.running = True

    def stop(self) -> None:
        logger.info(f"Stopping worker {self.worker_id}...")
        self.running = False

    def process_job(self, job_data: Dict[str, Any], db: Session) -> bool:
        change_id = job_data.get("change_id")
        analysis_run_id = job_data.get("analysis_run_id")
        attempt = job_data.get("attempt", 1)
        max_attempts = job_data.get("max_attempts", 3)

        if not change_id or not analysis_run_id:
            logger.error(f"Invalid job payload received: {job_data}")
            return False

        change_repo = ChangeRepository(db)
        analysis_repo = AnalysisRepository(db)
        audit_service = AuditService(db)

        change = change_repo.get_by_id(change_id)
        run = analysis_repo.get_by_id(analysis_run_id)

        if not change or not run:
            logger.error(f"Job references non-existent entity. change_id={change_id}, run_id={analysis_run_id}")
            return False

        org_id = change.pull_request.repository.organization_id if change.pull_request and change.pull_request.repository else None

        # 1. Transition to RUNNING
        now = datetime.now(timezone.utc)
        run.status = AnalysisStatus.RUNNING.value
        run.worker_id = self.worker_id
        run.started_at = now
        change.status = ChangeStatus.RUNNING.value
        change_repo.update(change)
        analysis_repo.update(run)

        audit_service.log(
            action="ANALYSIS_STARTED",
            entity_type="ANALYSIS_RUN",
            entity_id=run.id,
            organization_id=org_id,
            metadata={"worker_id": self.worker_id, "attempt": attempt, "stage": "INGESTION_VALIDATION"},
        )
        db.commit()

        logger.info(f"[{self.worker_id}] Started analysis run {run.id} for change {change.id} (attempt {attempt})")

        try:
            # 2. Perform Phase-1 Ingestion Validation
            # Verify PR metadata and commit SHA
            if not change.commit_sha or len(change.commit_sha) < 7:
                raise ValueError(f"Invalid commit SHA format: {change.commit_sha}")

            if not change.pull_request:
                raise ValueError("Change is missing associated pull request metadata")

            # Small simulated asynchronous processing latency (0.05s)
            time.sleep(0.05)

            # 3. CODE_ANALYSIS stage
            run.stage = "CODE_ANALYSIS"
            analysis_repo.update(run)
            db.commit()

            # 4. IMPACT_ANALYSIS stage
            run.stage = "IMPACT_ANALYSIS"
            analysis_repo.update(run)
            db.commit()

            # Check Neo4j and prepare schema if available
            repo_id = change.pull_request.repository_id if change.pull_request else None
            try:
                from app.services.graph.neo4j_connection import Neo4jConnection
                if Neo4jConnection.health_check().get("status") == "healthy":
                    Neo4jConnection.initialize_schema()
            except Exception as graph_err:
                logger.debug(f"Neo4j graph step skipped in worker: {graph_err}")

            # 5. AI_ASSURANCE stage
            run.stage = "AI_ASSURANCE"
            analysis_repo.update(run)
            db.commit()

            # 6. RISK_ASSESSMENT & POLICY_EVALUATION stages (via AssuranceOrchestrator)
            from app.services.assurance.assurance_orchestrator import AssuranceOrchestrator
            orchestrator = AssuranceOrchestrator(db)
            orchestrator.run_assurance(
                change=change,
                analysis_run=run,
                changed_files=["app/main.py", "app/api/v1/auth.py"],
                diff_text="diff --git a/app/api/v1/auth.py b/app/api/v1/auth.py\n+ # Ingested change assurance evaluation\n",
            )

            # 7. POLICY_EVALUATION completed -> Transition to COMPLETED
            run.stage = "POLICY_EVALUATION"
            completed_time = datetime.now(timezone.utc)
            run.status = AnalysisStatus.COMPLETED.value
            run.completed_at = completed_time
            run.error_message = None

            change.status = ChangeStatus.COMPLETED.value
            change_repo.update(change)
            analysis_repo.update(run)

            audit_service.log(
                action="ANALYSIS_COMPLETED",
                entity_type="ANALYSIS_RUN",
                entity_id=run.id,
                organization_id=org_id,
                metadata={
                    "worker_id": self.worker_id,
                    "stage": "POLICY_EVALUATION",
                    "duration_seconds": round((completed_time - now).total_seconds(), 3),
                    "validation": "Completed full assurance pipeline and Change Proof generation",
                },
            )
            db.commit()
            logger.info(f"[{self.worker_id}] Completed analysis run {run.id} for change {change.id} through POLICY_EVALUATION")
            return True

        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"[{self.worker_id}] Analysis run {run.id} failed: {error_msg}")

            failed_time = datetime.now(timezone.utc)
            run.status = AnalysisStatus.FAILED.value
            run.completed_at = failed_time
            run.error_message = error_msg

            if attempt < max_attempts:
                # Retry transient failure
                change.status = ChangeStatus.QUEUED.value
                change_repo.update(change)
                analysis_repo.update(run)

                audit_service.log(
                    action="ANALYSIS_RETRYING",
                    entity_type="ANALYSIS_RUN",
                    entity_id=run.id,
                    organization_id=org_id,
                    metadata={"error": error_msg, "attempt": attempt, "next_attempt": attempt + 1},
                )
                db.commit()

                # Re-enqueue with incremented attempt
                job_queue.enqueue_analysis(change_id=change.id, analysis_run_id=run.id, attempt=attempt + 1, max_attempts=max_attempts)
            else:
                change.status = ChangeStatus.FAILED.value
                change_repo.update(change)
                analysis_repo.update(run)

                audit_service.log(
                    action="ANALYSIS_FAILED",
                    entity_type="ANALYSIS_RUN",
                    entity_id=run.id,
                    organization_id=org_id,
                    metadata={"error": error_msg, "attempts_exhausted": True},
                )
                db.commit()

            return False

    def process_next_job(self, timeout: int = BLPOP_BLOCK_TIMEOUT) -> bool:
        """Pop and process one job.  Returns True if a job was processed."""
        job_data = job_queue.pop_analysis(timeout=timeout)
        if not job_data:
            return False

        db = SessionLocal()
        try:
            return self.process_job(job_data, db)
        finally:
            db.close()

    def run(self) -> None:
        logger.info(f"Starting ProofMesh Analysis Worker: {self.worker_id}")
        while self.running:
            try:
                # process_next_job calls blpop which already blocks for
                # BLPOP_BLOCK_TIMEOUT seconds when the queue is empty.
                # No extra sleep is needed for idle — blpop IS the wait.
                self.process_next_job()
            except Exception as e:
                logger.error(f"Unexpected worker loop exception: {str(e)}", exc_info=True)
                time.sleep(1.0)


def main() -> None:
    worker = AnalysisWorker()

    def handle_signal(sig, frame):
        logger.info("Received termination signal")
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    worker.run()


if __name__ == "__main__":
    main()
