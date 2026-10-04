from typing import List, Optional
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.errors import ConflictError, NotFoundError
from app.db.session import get_db
from app.models.entities import Organization, Repository, User, UserRole
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.common import SuccessEnvelope
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.audit.service import AuditService
from app.services.auth.service import RequireRole, get_current_user

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get("", response_model=SuccessEnvelope[List[RepositoryResponse]])
def list_repositories(
    request: Request,
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = RepositoryRepository(db)
    repos = repo.list_by_organization(organization_id=organization_id)
    return SuccessEnvelope(
        data=[RepositoryResponse.model_validate(r) for r in repos],
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.get("/{id}", response_model=SuccessEnvelope[RepositoryResponse])
def get_repository(
    id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = RepositoryRepository(db)
    r = repo.get_by_id(id)
    if not r:
        raise NotFoundError(f"Repository with ID '{id}' not found", code="REPOSITORY_NOT_FOUND")
    return SuccessEnvelope(
        data=RepositoryResponse.model_validate(r),
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )


@router.post("", response_model=SuccessEnvelope[RepositoryResponse], status_code=status.HTTP_201_CREATED)
def create_repository(
    req: RepositoryCreate,
    request: Request,
    current_user: User = Depends(RequireRole([UserRole.ADMIN])),
    db: Session = Depends(get_db),
):
    repo_repository = RepositoryRepository(db)
    org_repository = OrganizationRepository(db)
    audit_service = AuditService(db)

    # Validate org context
    org_id = req.organization_id
    if not org_id:
        if current_user.memberships:
            org_id = current_user.memberships[0].organization_id
        else:
            default_org = org_repository.get_by_slug("default")
            if not default_org:
                default_org = Organization(name="Default Organization", slug="default")
                org_repository.create(default_org)
                db.flush()
            org_id = default_org.id

    # Check for existing repository
    existing = repo_repository.get_by_github_id(req.github_repository_id)
    if existing:
        raise ConflictError(f"Repository with GitHub ID {req.github_repository_id} already exists", code="REPOSITORY_ALREADY_EXISTS")

    full_name = f"{req.owner}/{req.name}"
    repo = Repository(
        organization_id=org_id,
        github_repository_id=req.github_repository_id,
        owner=req.owner,
        name=req.name,
        full_name=full_name,
        default_branch=req.default_branch,
        is_active=True,
    )
    repo_repository.create(repo)

    audit_service.log(
        action="REPOSITORY_CREATED",
        entity_type="REPOSITORY",
        entity_id=repo.id,
        organization_id=org_id,
        actor_user_id=current_user.id,
        metadata={"full_name": full_name, "github_repository_id": req.github_repository_id},
    )
    db.commit()

    return SuccessEnvelope(
        data=RepositoryResponse.model_validate(repo),
        request_id=getattr(request.state, "request_id", "req_unknown"),
    )
