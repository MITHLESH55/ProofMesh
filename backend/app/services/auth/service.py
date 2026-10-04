import re
from typing import List, Optional
from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import Organization, User, UserOrganizationMembership, UserRole
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import MembershipResponse, TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.audit.service import AuditService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.audit_service = AuditService(db)

    def register(self, req: UserRegisterRequest) -> TokenResponse:
        existing = self.user_repo.get_by_email(req.email)
        if existing:
            raise ConflictError("A user with this email already exists", code="USER_ALREADY_EXISTS")

        # Create user
        user = User(
            email=req.email.lower().strip(),
            password_hash=hash_password(req.password),
            full_name=req.full_name.strip(),
            role=UserRole.ADMIN.value if req.organization_name else UserRole.ENGINEER.value,
        )
        self.user_repo.create(user)

        # If org name provided, create or attach
        org = None
        if req.organization_name:
            slug = slugify(req.organization_name)
            org = self.org_repo.get_by_slug(slug)
            if not org:
                org = Organization(name=req.organization_name.strip(), slug=slug)
                self.org_repo.create(org)

            membership = UserOrganizationMembership(
                user_id=user.id,
                organization_id=org.id,
                role=UserRole.ADMIN.value,
            )
            self.org_repo.add_member(membership)

        self.audit_service.log(
            action="USER_REGISTERED",
            entity_type="USER",
            entity_id=user.id,
            organization_id=org.id if org else None,
            actor_user_id=user.id,
            metadata={"email": user.email},
        )
        self.db.commit()

        token = create_access_token(subject=user.id, extra_claims={"role": user.role, "email": user.email})
        return TokenResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=self._build_user_response(user),
        )

    def login(self, req: UserLoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password", code="INVALID_CREDENTIALS")

        if not user.is_active:
            raise ForbiddenError("User account is deactivated", code="ACCOUNT_INACTIVE")

        self.audit_service.log(
            action="LOGIN",
            entity_type="USER",
            entity_id=user.id,
            actor_user_id=user.id,
            metadata={"email": user.email},
        )
        self.db.commit()

        token = create_access_token(subject=user.id, extra_claims={"role": user.role, "email": user.email})
        return TokenResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=self._build_user_response(user),
        )

    def get_current_user_from_token(self, token: Optional[str]) -> User:
        if not token:
            raise UnauthorizedError("Missing authentication token", code="MISSING_TOKEN")

        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise UnauthorizedError("Invalid or expired authentication token", code="INVALID_TOKEN")

        user_id = payload["sub"]
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive", code="USER_INACTIVE")

        return user

    def _build_user_response(self, user: User) -> UserResponse:
        memberships = []
        for m in user.memberships:
            if m.organization:
                memberships.append(
                    MembershipResponse(
                        organization_id=m.organization.id,
                        organization_name=m.organization.name,
                        organization_slug=m.organization.slug,
                        role=m.role,
                    )
                )

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            memberships=memberships,
        )


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    service = AuthService(db)
    return service.get_current_user_from_token(token)


class RequireRole:
    """RBAC Guard dependency"""
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenError(
                f"Insufficient privileges. Allowed roles: {', '.join(self.allowed_roles)}",
                code="INSUFFICIENT_PERMISSIONS"
            )
        return current_user
