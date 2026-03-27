from motor.motor_asyncio import AsyncIOMotorCollection
from app.model.employees_model import (
    add_employee, get_all_employees, get_employee_by_id,
    get_employees_by_department, update_employee, delete_employee
)
from app.schemas.employee_schema import EmployeeCreate, EmployeeResponse
from datetime import datetime, timezone

async def create_employee(collection: AsyncIOMotorCollection, employee: EmployeeCreate):
    emp_dict = employee.model_dump()
    if "createdAt" not in emp_dict or emp_dict["createdAt"] is None:
        emp_dict["createdAt"] = datetime.now(timezone.utc)
    created = await add_employee(collection, emp_dict)
    return EmployeeResponse(**created)

async def fetch_all_employees(collection: AsyncIOMotorCollection, skip=0, limit=100):
    employees = await get_all_employees(collection, skip, limit)
    return [EmployeeResponse(**emp) for emp in employees]

async def fetch_employee_by_id(collection: AsyncIOMotorCollection, employee_id: str):
    emp = await get_employee_by_id(collection, employee_id)
    if emp:
        return EmployeeResponse(**emp)
    return None

async def fetch_employees_by_department(collection: AsyncIOMotorCollection, department: str):
    employees = await get_employees_by_department(collection, department)
    return [EmployeeResponse(**emp) for emp in employees]

async def update_employee_controller(collection: AsyncIOMotorCollection, employee_id: str, update_data: dict):
    updated = await update_employee(collection, employee_id, update_data)
    if updated:
        return EmployeeResponse(**updated)
    return None

async def delete_employee_controller(collection: AsyncIOMotorCollection, employee_id: str):
    return await delete_employee(collection, employee_id)