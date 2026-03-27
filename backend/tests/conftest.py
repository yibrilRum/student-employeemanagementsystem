import pytest
import pytest_asyncio
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config.settings import settings

# Use a unique test database name to avoid collisions
TEST_DB_NAME = f"{settings.DB_NAME}_test"

@pytest_asyncio.fixture(scope="function")
async def test_db():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[TEST_DB_NAME]
    yield db
    # Cleanup after test
    await client.drop_database(TEST_DB_NAME)
    client.close()

@pytest_asyncio.fixture
async def client(test_db):
    # Override app state with test collections
    app.state.users_collection = test_db["users"]
    app.state.employees_collection = test_db["employees"]

    # Ensure indexes are created for test
    from app.db.indexes import create_indexes
    await create_indexes(app.state.users_collection, app.state.employees_collection)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def admin_token(client):
    # Register an admin user
    admin_data = {
        "username": "admin",
        "password": "adminpass",
        "email": "admin@example.com",
        "is_admin": True
    }
    await client.post("/auth/register", json=admin_data)
    login_resp = await client.post("/auth/login", json=admin_data)
    token = login_resp.json()["access_token"]
    return token

@pytest_asyncio.fixture
async def user_token(client):
    # Register a normal user
    user_data = {
        "username": "user",
        "password": "userpass",
        "email": "user@example.com",
        "is_admin": False
    }
    await client.post("/auth/register", json=user_data)
    login_resp = await client.post("/auth/login", json=user_data)
    token = login_resp.json()["access_token"]
    return token

@pytest.fixture
def sample_employee():
    return {
        "employeeId": "EMP001",
        "name": "John Doe",
        "email": "john@example.com",
        "department": "Engineering",
        "position": "Developer",
        "status": "active",
        "salary": 75000
    }