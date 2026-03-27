from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime

class EmployeeBase(BaseModel):
    employeeId: str
    name: str
    email: EmailStr
    department: str
    position: str
    status: str
    salary: Optional[float] = None

class EmployeeCreate(EmployeeBase):
    createdAt: Optional[datetime.datetime] = None

class EmployeeResponse(EmployeeBase):
    createdAt: Optional[datetime.datetime] = None