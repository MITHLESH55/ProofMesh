import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.models.entities import User, UserRole
from app.core.security import hash_password, create_access_token

# Use SQLite in-memory for fast unit/integration testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_admin_user(db_session):
    user = User(
        email="admin@test.com",
        password_hash=hash_password("Password123!"),
        full_name="Test Admin",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_token(test_admin_user):
    return create_access_token(
        subject=test_admin_user.id,
        extra_claims={"role": test_admin_user.role, "email": test_admin_user.email}
    )


@pytest.fixture
def test_engineer_user(db_session):
    user = User(
        email="engineer@test.com",
        password_hash=hash_password("Password123!"),
        full_name="Test Engineer",
        role=UserRole.ENGINEER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_engineer_token(test_engineer_user):
    return create_access_token(
        subject=test_engineer_user.id,
        extra_claims={"role": test_engineer_user.role, "email": test_engineer_user.email}
    )
