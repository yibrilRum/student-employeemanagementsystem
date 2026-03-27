from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError

async def insert_user(collection: AsyncIOMotorCollection, user_data: dict):
    try:
        result = await collection.insert_one(user_data)
        return result.inserted_id
    except DuplicateKeyError:
        raise ValueError("Username already exists")

async def get_user_by_username(collection: AsyncIOMotorCollection, username: str):
    return await collection.find_one({"username": username})

async def update_user_activity(collection: AsyncIOMotorCollection, username: str, action: str):
    return await collection.update_one(
        {"username": username},
        {"$push": {"activitylog": {"action": action, "timestamp": datetime.now(timezone.utc)}}}
    )