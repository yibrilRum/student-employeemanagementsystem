from fastapi import APIRouter, HTTPException, Body, Depends, Request
from pymongo.errors import DuplicateKeyError
from app.auth.security import get_current_user, require_admin
from app.controller.employee_controller import (
    fetch_all_employees, create_employee, fetch_employee_by_id,
    fetch_employees_by_department, update_employee_controller,
    delete_employee_controller
)
from app.schemas.employee_schema import EmployeeCreate, EmployeeResponse

router = APIRouter()

@router.get("/", response_model=list[EmployeeResponse])
async def get_employees(
    request: Request,
    department: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    collection = request.app.state.employees_collection
    if department:
        return await fetch_employees_by_department(collection, department)
    return await fetch_all_employees(collection, skip, limit)

@router.get("/{employeeId}", response_model=EmployeeResponse)
async def get_employee(
    request: Request,
    employeeId: str,
    current_user: dict = Depends(get_current_user)
):
    collection = request.app.state.employees_collection
    employee = await fetch_employee_by_id(collection, employeeId)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.post("/", response_model=EmployeeResponse, dependencies=[Depends(require_admin)])
async def add_employee(request: Request, employee: EmployeeCreate):
    collection = request.app.state.employees_collection
    try:
        return await create_employee(collection, employee)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Employee ID already exists")

@router.put("/{employeeId}", response_model=EmployeeResponse, dependencies=[Depends(require_admin)])
async def update_employee(
    request: Request,
    employeeId: str,
    employee: EmployeeCreate = Body(...)
):
    collection = request.app.state.employees_collection
    update_data = employee.model_dump(exclude_unset=True)
    updated = await update_employee_controller(collection, employeeId, update_data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated

@router.delete("/{employeeId}", dependencies=[Depends(require_admin)])
async def delete_employee(request: Request, employeeId: str):
    collection = request.app.state.employees_collection
    deleted = await delete_employee_controller(collection, employeeId)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"detail": "Employee deleted"}