from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.entities import AnalysisRun


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, run_id: str) -> Optional[AnalysisRun]:
        return self.db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()

    def get_latest_for_change(self, change_id: str) -> Optional[AnalysisRun]:
        return (
            self.db.query(AnalysisRun)
            .filter(AnalysisRun.change_id == change_id)
            .order_by(AnalysisRun.created_at.desc())
            .first()
        )

    def list_by_change(self, change_id: str) -> List[AnalysisRun]:
        return (
            self.db.query(AnalysisRun)
            .filter(AnalysisRun.change_id == change_id)
            .order_by(AnalysisRun.created_at.desc())
            .all()
        )

    def create(self, run: AnalysisRun) -> AnalysisRun:
        self.db.add(run)
        self.db.flush()
        return run

    def update(self, run: AnalysisRun) -> AnalysisRun:
        self.db.flush()
        return run
