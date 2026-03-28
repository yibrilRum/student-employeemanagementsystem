import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.db.indexes import create_indexes

os.environ["DB_NAME"] = "test_employee_db"

@pytest.fixture(scope="function")
def client():
    """
    Provides a synchronous test client that connects to the FastAPI app.
    Before each test, it empties the collections and ensures indexes are created.
    """
    with TestClient(app) as test_client:
        async def prepare_db():
            mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
            db = mongo_client[settings.DB_NAME]
            await db.users.delete_many({})
            await db.employees.delete_many({})
            await create_indexes(db.users, db.employees)
            mongo_client.close()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(prepare_db())
        loop.close()
        yield test_client
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(prepare_db())
        loop.close()