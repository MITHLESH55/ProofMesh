from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.schemas.common import SuccessEnvelope
from app.services.auth.service import AuthService, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=SuccessEnvelope[TokenResponse], status_code=status.HTTP_201_CREATED)
def register(
    req: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    token_resp = service.register(req)
    return SuccessEnvelope(
        data=token_resp,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.post("/login", response_model=SuccessEnvelope[TokenResponse])
def login(
    req: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    token_resp = service.login(req)
    return SuccessEnvelope(
        data=token_resp,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/me", response_model=SuccessEnvelope[UserResponse])
def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    user_resp = service._build_user_response(current_user)
    return SuccessEnvelope(
        data=user_resp,
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )
