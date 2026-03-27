import pytest
import asyncio
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
import pytest_asyncio
from httpx import AsyncClient
from httpx import ASGITransport
from app.main import app

@pytest_asyncio.fixture(scope="function")
async def async_client_and_token():
    transport = ASGITransport(app=app, lifespan="on")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg_payload = {
            "username": "testuser2",
            "password": "Test1234!",
            "email": "testuser2@example.com"
        }
        await client.post("/auth/register", json=reg_payload)
        login_resp = await client.post("/auth/login", json=reg_payload)
        token = login_resp.json().get("access_token")
        assert token is not None, f"Login failed: {login_resp.text}"
        headers = {"Authorization": f"Bearer {token}"}
        yield client, headers

@pytest.mark.asyncio
async def test_get_employees(async_client_and_token):
    client, headers = async_client_and_token
    response = await client.get("/employees/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_add_employee(async_client_and_token):
    client, headers = async_client_and_token
    payload = {
        "employeeId": "EMP002",
        "name": "Jane Doe",
        "position": "Data Analyst",
        "department": "IT",
        "email": "jane.doe@example.com",
        "status": "active"
    }
    response = await client.post("/employees/", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["employeeId"] == "EMP002"
    assert data["name"] == "Jane Doe"
    assert data["department"] == "IT"

@pytest.mark.asyncio
async def test_add_duplicate_employee(async_client_and_token):
    client, headers = async_client_and_token
    payload = {
        "employeeId": "EMP002",
        "name": "Jane Doe",
        "position": "Data Analyst",
        "department": "IT",
        "email": "jane.doe@example.com",
        "status": "active"
    }
    response = await client.post("/employees/", json=payload, headers=headers)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_get_employee_by_id(async_client_and_token):
    client, headers = async_client_and_token
    response = await client.get("/employees/EMP002", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["employeeId"] == "EMP002"
    assert data["name"] == "Jane Doe"
    assert data["department"] == "IT"

@pytest.mark.asyncio
async def test_get_employee_by_id_not_found(async_client_and_token):
    client, headers = async_client_and_token
    response = await client.get("/employees/EMP999", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_employee(async_client_and_token):
    client, headers = async_client_and_token
    payload = {
        "employeeId": "EMP002",
        "name": "Jane Doe Updated",
        "position": "Senior Data Analyst",
        "department": "IT",
        "email": "jane.doe.updated@example.com",
        "status": "inactive"
    }
    response = await client.put("/employees/EMP002", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe Updated"
    assert data["position"] == "Senior Data Analyst"
    assert data["status"] == "inactive"

@pytest.mark.asyncio
async def test_update_employee_not_found(async_client_and_token):
    client, headers = async_client_and_token
    payload = {
        "employeeId": "EMP999",
        "name": "Ghost Employee",
        "position": "Nobody",
        "department": "Nowhere",
        "email": "ghost@example.com",
        "status": "inactive"
    }
    response = await client.put("/employees/EMP999", json=payload, headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_employee(async_client_and_token):
    client, headers = async_client_and_token
    response = await client.delete("/employees/EMP002", headers=headers)
    assert response.status_code == 200
    get_response = await client.get("/employees/EMP002", headers=headers)
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_delete_employee_not_found(async_client_and_token):
    client, headers = async_client_and_token
    response = await client.delete("/employees/EMP999", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_employees_by_department(async_client_and_token):
    client, headers = async_client_and_token
    response = await client.get("/employees/?department=IT", headers=headers)
    assert response.status_code == 200
    employees = response.json()
    assert isinstance(employees, list)
    assert all(emp["department"] == "IT" for emp in employees)