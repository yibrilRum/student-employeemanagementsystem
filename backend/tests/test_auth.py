import pytest
from app.utils.utils import decode_token

@pytest.fixture
def test_user(client):
    """Create a test user and return its token."""
    # Register a user
    resp = client.post("/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123"
    })
    assert resp.status_code == 201
    # Login to get token
    resp = client.post("/auth/login", json={
        "username": "alice",
        "password": "secret123"
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"username": "alice", "token": token}

def test_register_success(client):
    response = client.post("/auth/register", json={
        "username": "bob",
        "email": "bob@example.com",
        "password": "secret123",
        "is_admin": False
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "bob"
    assert data["email"] == "bob@example.com"
    assert data["is_admin"] is False
    assert "id" in data

def test_register_duplicate_username(client):
    # First registration
    client.post("/auth/register", json={
        "username": "charlie",
        "email": "charlie@example.com",
        "password": "secret"
    })
    # Duplicate
    response = client.post("/auth/register", json={
        "username": "charlie",
        "email": "charlie2@example.com",
        "password": "secret"
    })
    assert response.status_code == 409
    assert "Username already exists" in response.json()["detail"]

def test_register_missing_fields(client):
    response = client.post("/auth/register", json={"username": "dave"})
    assert response.status_code == 422

def test_register_invalid_email(client):
    response = client.post("/auth/register", json={
        "username": "eve",
        "email": "not-an-email",
        "password": "secret"
    })
    assert response.status_code == 422

def test_login_success(client, test_user):
    response = client.post("/auth/login", json={
        "username": "alice",
        "password": "secret123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Verify token contents
    payload = decode_token(data["access_token"])
    assert payload["sub"] == "alice"
    assert payload["is_admin"] is False

def test_login_wrong_password(client, test_user):
    response = client.post("/auth/login", json={
        "username": "alice",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_login_nonexistent_user(client):
    response = client.post("/auth/login", json={
        "username": "ghost",
        "password": "any"
    })
    assert response.status_code == 401

def test_protected_route_without_token(client):
    response = client.get("/employees/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_protected_route_with_valid_token(client, test_user):
    response = client.get("/employees/",
                          headers={"Authorization": f"Bearer {test_user['token']}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)   # may be empty

def test_admin_route_with_user_role(client, test_user):
    # Non-admin user tries to create an employee
    response = client.post("/employees/",
                           headers={"Authorization": f"Bearer {test_user['token']}"},
                           json={
                               "employeeId": "E001",
                               "name": "Test",
                               "email": "test@example.com",
                               "department": "IT",
                               "position": "Dev",
                               "status": "active"
                           })
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"