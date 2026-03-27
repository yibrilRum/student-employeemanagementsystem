from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class ActivityLog(BaseModel):
    action: str
    timestamp: datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: Optional[str] = None
    activitylog: Optional[List[ActivityLog]] = []

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str