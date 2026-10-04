import os
import sys
from datetime import datetime, timezone

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logging import logger
from app.core.security import hash_password
from app.db.session import SessionLocal, engine, Base
from app.models.entities import (
    AnalysisRun,
    AnalysisStatus,
    AuditLog,
    Change,
    ChangeStatus,
    Organization,
    PullRequest,
    PullRequestState,
    Repository,
    User,
    UserOrganizationMembership,
    UserRole,
)


def seed_database() -> None:
    logger.info("Initializing database tables if not present...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Demo Organization
        org = db.query(Organization).filter(Organization.slug == "proofmesh-demo").first()
        if not org:
            org = Organization(
                name="ProofMesh Demo Enterprise",
                slug="proofmesh-demo",
            )
            db.add(org)
            db.flush()
            logger.info(f"Created demo organization: {org.name} ({org.id})")

        # 2. Demo User (ADMIN)
        demo_email = "demo@example.com"
        user = db.query(User).filter(User.email == demo_email).first()
        if not user:
            user = User(
                email=demo_email,
                password_hash=hash_password("Password123!"),
                full_name="Demo Enterprise Admin",
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            db.add(user)
            db.flush()

            # Membership
            membership = UserOrganizationMembership(
                user_id=user.id,
                organization_id=org.id,
                role=UserRole.ADMIN.value,
            )
            db.add(membership)
            db.flush()
            logger.info(f"Created demo user: {user.email} (Password: Password123!)")

        # 3. Demo Repository
        github_repo_id = "987654321"
        repo = db.query(Repository).filter(Repository.github_repository_id == github_repo_id).first()
        if not repo:
            repo = Repository(
                organization_id=org.id,
                github_repository_id=github_repo_id,
                owner="proofmesh-demo-org",
                name="demo-enterprise",
                full_name="proofmesh-demo-org/demo-enterprise",
                default_branch="main",
                is_active=True,
            )
            db.add(repo)
            db.flush()
            logger.info(f"Created demo repository: {repo.full_name}")

        db.commit()
        logger.info("Database seeding completed successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {str(e)}", exc_info=True)
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
