import pytest
pytestmark = pytest.mark.asyncio
import asyncio
from datetime import datetime, timedelta
import jwt
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Adjust these constants to match your app's settings
MONGO_URI = "mongodb://localhost:27017"
TEST_DB = "test_auth_db"
SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1  # short expiry for tests

# Import your FastAPI app - adjust the import path to your project
from app.main import app

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

import pytest_asyncio

@pytest_asyncio.fixture(scope="module")
async def mongo_client():
    client = AsyncIOMotorClient(MONGO_URI)
    yield client
    await client.drop_database(TEST_DB)
    client.close()

import pytest_asyncio

@pytest_asyncio.fixture
async def db(mongo_client):
    db = mongo_client[TEST_DB]
    await db.users.delete_many({})
    yield db
    await db.users.delete_many({})

@pytest_asyncio.fixture
async def client(db):
    app.state._test_db = db
    async with AsyncClient(base_url="http://testserver") as ac:
        yield ac

# Helpers
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def create_jwt_token(username: str, role: str = "user", expires_delta: timedelta = None):
    now = datetime.utcnow()
    if expires_delta is None:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = now + expires_delta
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Test data
VALID_USER = {"username": "alice", "email": "alice@example.com", "password": "Str0ng!Passw0rd"}
OTHER_USER = {"username": "bob", "email": "bob@example.com", "password": "An0ther$trong1"}
WEAK_PASSWORDS = ["short", "alllowercase", "12345678", "password"]

@pytest.mark.asyncio
async def test_register_user_success(client, db):
    resp = await client.post("/register", json=VALID_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert body.get("username") == VALID_USER["username"]
    user_doc = await db.users.find_one({"username": VALID_USER["username"]})
    assert user_doc is not None
    assert "hashed_password" in user_doc
    assert user_doc["hashed_password"] != VALID_USER["password"]
    assert "role" in user_doc

@pytest.mark.asyncio
async def test_register_duplicate_username_returns_409(client, db):
    await db.users.insert_one({
        "username": VALID_USER["username"],
        "email": VALID_USER["email"],
        "hashed_password": hash_password(VALID_USER["password"]),
        "role": "user",
    })
    resp = await client.post("/register", json={
        "username": VALID_USER["username"],
        "email": "different@example.com",
        "password": VALID_USER["password"],
    })
    assert resp.status_code == 409

@pytest.mark.asyncio
@pytest.mark.parametrize("weak_pw", WEAK_PASSWORDS)
async def test_register_weak_password_returns_422(client, weak_pw):
    payload = {"username": f"user_{weak_pw}", "email": f"{weak_pw}@example.com", "password": weak_pw}
    resp = await client.post("/register", json=payload)
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_login_success_returns_jwt(client, db):
    await db.users.insert_one({
        "username": OTHER_USER["username"],
        "email": OTHER_USER["email"],
        "hashed_password": hash_password(OTHER_USER["password"]),
        "role": "user",
    })
    resp = await client.post("/login", data={"username": OTHER_USER["username"], "password": OTHER_USER["password"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and isinstance(body["access_token"], str)
    decoded = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded.get("sub") == OTHER_USER["username"]
    assert "exp" in decoded

@pytest.mark.asyncio
@pytest.mark.parametrize("username,password", [
    ("nonexistent", "whatever"),
    (OTHER_USER["username"], "wrongpassword"),
])
async def test_login_wrong_password_returns_401(client, db, username, password):
    await db.users.delete_many({})
    await db.users.insert_one({
        "username": OTHER_USER["username"],
        "email": OTHER_USER["email"],
        "hashed_password": hash_password(OTHER_USER["password"]),
        "role": "user",
    })
    resp = await client.post("/login", data={"username": username, "password": password})
    assert resp.status_code == 401
    body = resp.json()
    assert "detail" in body

@pytest.mark.asyncio
async def test_protected_route_without_token_returns_401(client):
    resp = await client.get("/protected")
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_with_valid_token_succeeds(client, db):
    await db.users.insert_one({
        "username": "carol",
        "email": "carol@example.com",
        "hashed_password": hash_password("C@rolStrong1"),
        "role": "user",
    })
    token = create_jwt_token("carol", role="user")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/protected", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("username") == "carol"

@pytest.mark.asyncio
async def test_protected_route_with_expired_token_returns_401(client, db):
    token = create_jwt_token("carol", expires_delta=timedelta(seconds=-10))
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/protected", headers=headers)
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_admin_route_with_user_role_returns_403(client, db):
    await db.users.insert_one({
        "username": "dave",
        "email": "dave@example.com",
        "hashed_password": hash_password("D@veStrong1"),
        "role": "user",
    })
    token = create_jwt_token("dave", role="user")
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/admin-only", headers=headers)
    assert resp.status_code == 403

# Extra coverage
@pytest.mark.asyncio
async def test_register_missing_fields_returns_422(client):
    resp = await client.post("/register", json={"username": "noemail"})
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_login_missing_fields_returns_422(client):
    resp = await client.post("/login", data={"username": "someone"})
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_token_with_invalid_signature_returns_401(client):
    wrong_token = jwt.encode({"sub": "carol", "exp": datetime.utcnow() + timedelta(minutes=5)}, "wrong-key", algorithm=ALGORITHM)
    headers = {"Authorization": f"Bearer {wrong_token}"}
    resp = await client.get("/protected", headers=headers)
    assert resp.status_code == 401
