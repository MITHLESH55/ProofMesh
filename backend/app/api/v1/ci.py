"""
CI/CD Assurance Gate API Router.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import User
from app.schemas.common import SuccessEnvelope
from app.schemas.runtime import CIAssuranceCheckRequest, CIAssuranceCheckResponse
from app.services.auth.service import get_current_user
from app.services.runtime.github_check_service import GitHubCheckService

router = APIRouter(prefix="/ci", tags=["CI/CD Assurance Gates"])


@router.post("/check", response_model=SuccessEnvelope[CIAssuranceCheckResponse])
def run_ci_gate_check(
    payload: CIAssuranceCheckRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base_url = str(request.base_url).rstrip("/")
    result = GitHubCheckService.evaluate_ci_check(db, payload, base_url=base_url)
    return SuccessEnvelope(
        data=result,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )
