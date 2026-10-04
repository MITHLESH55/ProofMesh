import pytest
from fastapi.testclient import TestClient


def test_auth_register_and_login(client: TestClient):
    # Register new user
    register_payload = {
        "email": "alice@example.com",
        "password": "StrongPassword123!",
        "full_name": "Alice Engineer",
        "organization_name": "Alice Enterprise",
    }
    resp = client.post("/api/v1/auth/register", json=register_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "data" in data
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "alice@example.com"
    assert "request_id" in data

    # Login with same user
    login_payload = {
        "email": "alice@example.com",
        "password": "StrongPassword123!",
    }
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["data"]["access_token"]
    assert token is not None

    # Get me
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["data"]["email"] == "alice@example.com"
    assert me_data["data"]["full_name"] == "Alice Engineer"


def test_auth_login_invalid_credentials(client: TestClient):
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!",
    }
    resp = client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 401
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
