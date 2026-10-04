from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, UserRole
from app.schemas.change import ChangeDetailResponse, ChangeResponse, ChangeStatusResponse, ReanalyzeRequest
from app.schemas.common import SuccessEnvelope
from app.services.auth.service import RequireRole, get_current_user
from app.services.changes.service import ChangesService

router = APIRouter(prefix="/changes", tags=["Changes"])


@router.get("", response_model=SuccessEnvelope[List[ChangeResponse]])
def list_changes(
    request: Request,
    repository_id: Optional[str] = Query(None, description="Filter by repository ID"),
    status: Optional[str] = Query(None, description="Filter by change status (QUEUED, RUNNING, COMPLETED, FAILED)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ChangesService(db)
    changes, _ = service.list_changes(repository_id=repository_id, status=status, limit=limit, offset=offset)
    return SuccessEnvelope(
        data=changes,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/{id}", response_model=SuccessEnvelope[ChangeDetailResponse])
def get_change(
    id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ChangesService(db)
    change = service.get_change_by_id(id)
    return SuccessEnvelope(
        data=change,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/{id}/status", response_model=SuccessEnvelope[ChangeStatusResponse])
def get_change_status(
    id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ChangesService(db)
    status_resp = service.get_change_status(id)
    return SuccessEnvelope(
        data=status_resp,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.post("/{id}/reanalyze", response_model=SuccessEnvelope[ChangeDetailResponse])
def reanalyze_change(
    id: str,
    request: Request,
    req_body: Optional[ReanalyzeRequest] = None,
    current_user: User = Depends(RequireRole([UserRole.ADMIN, UserRole.ENGINEER])),
    db: Session = Depends(get_db),
):
    service = ChangesService(db)
    reason = req_body.reason if req_body else "Manual reanalysis"
    change = service.reanalyze(change_id=id, actor_user=current_user, reason=reason)
    return SuccessEnvelope(
        data=change,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )
