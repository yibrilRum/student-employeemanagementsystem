from fastapi import APIRouter, HTTPException, Body, Request
from app.schemas.user_schema import UserCreate, UserResponse, UserLogin, Token
from app.controller.user_controller import create_user, authenticate_user
from app.utils.utils import create_access_token

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(request: Request, user: UserCreate = Body(...)):
    collection = request.app.state.users_collection
    return await create_user(collection, user)

@router.post("/login", response_model=Token)
async def login_user(request: Request, credentials: UserLogin = Body(...)):
    collection = request.app.state.users_collection
    user = await authenticate_user(collection, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user["username"], "is_admin": user.get("is_admin", False)})
    return {"access_token": token, "token_type": "bearer"}