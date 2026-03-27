from motor.motor_asyncio import AsyncIOMotorCollection
from app.model.user_model import insert_user, get_user_by_username
from app.schemas.user_schema import UserCreate, UserResponse
from app.utils.utils import hash_password, verify_password, create_access_token
from fastapi import HTTPException, status

async def create_user(collection: AsyncIOMotorCollection, user: UserCreate) -> UserResponse:
    existing = await get_user_by_username(collection, user.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    user_dict = user.model_dump()
    user_dict["hashed_password"] = hash_password(user_dict.pop("password"))
    user_dict["activitylog"] = []
    await insert_user(collection, user_dict)
    # Return response without password
    user_dict.pop("hashed_password")
    return UserResponse(**user_dict)

async def authenticate_user(collection: AsyncIOMotorCollection, username: str, password: str):
    user = await get_user_by_username(collection, username)
    if not user or not verify_password(password, user.get("hashed_password")):
        return None
    return user