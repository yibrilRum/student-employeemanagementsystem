import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    data = {
        "username": "newuser",
        "password": "secret",
        "email": "new@example.com"
    }
    resp = await client.post("/auth/register", json=data)
    assert resp.status_code == 201
    assert resp.json()["username"] == "newuser"

@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    data = {
        "username": "duplicate",
        "password": "pass",
        "email": "dup@example.com"
    }
    await client.post("/auth/register", json=data)
    resp = await client.post("/auth/register", json=data)
    assert resp.status_code == 409

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    data = {
        "username": "logintest",
        "password": "pass",
        "email": "login@example.com"
    }
    await client.post("/auth/register", json=data)
    resp = await client.post("/auth/login", json={"username": "logintest", "password": "pass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient):
    resp = await client.post("/auth/login", json={"username": "nonexistent", "password": "wrong"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_create_employee_as_admin(client: AsyncClient, admin_token, sample_employee):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.post("/employees/", json=sample_employee, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["employeeId"] == sample_employee["employeeId"]

@pytest.mark.asyncio
async def test_create_employee_as_user(client: AsyncClient, user_token, sample_employee):
    headers = {"Authorization": f"Bearer {user_token}"}
    resp = await client.post("/employees/", json=sample_employee, headers=headers)
    assert resp.status_code == 403  # Forbidden

@pytest.mark.asyncio
async def test_get_employees(client: AsyncClient, admin_token, sample_employee):
    # Create an employee first
    headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post("/employees/", json=sample_employee, headers=headers)

    # Get all employees (authenticated as admin)
    resp = await client.get("/employees/", headers=headers)
    assert resp.status_code == 200
    employees = resp.json()
    assert len(employees) >= 1
    assert employees[0]["employeeId"] == sample_employee["employeeId"]

@pytest.mark.asyncio
async def test_get_employee_by_id(client: AsyncClient, admin_token, sample_employee):
    headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post("/employees/", json=sample_employee, headers=headers)
    resp = await client.get(f"/employees/{sample_employee['employeeId']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == sample_employee["name"]

@pytest.mark.asyncio
async def test_get_employee_by_id_not_found(client: AsyncClient, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.get("/employees/EMP999", headers=headers)
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_update_employee(client: AsyncClient, admin_token, sample_employee):
    headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post("/employees/", json=sample_employee, headers=headers)
    update_data = {**sample_employee, "name": "Updated Name", "status": "inactive"}
    resp = await client.put(f"/employees/{sample_employee['employeeId']}", json=update_data, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["status"] == "inactive"

@pytest.mark.asyncio
async def test_update_employee_not_found(client: AsyncClient, admin_token, sample_employee):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.put("/employees/EMP999", json=sample_employee, headers=headers)
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_delete_employee(client: AsyncClient, admin_token, sample_employee):
    headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post("/employees/", json=sample_employee, headers=headers)
    resp = await client.delete(f"/employees/{sample_employee['employeeId']}", headers=headers)
    assert resp.status_code == 200
    get_resp = await client.get(f"/employees/{sample_employee['employeeId']}", headers=headers)
    assert get_resp.status_code == 404

@pytest.mark.asyncio
async def test_delete_employee_not_found(client: AsyncClient, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.delete("/employees/EMP999", headers=headers)
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_get_employees_by_department(client: AsyncClient, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    emp1 = {
        "employeeId": "EMP101",
        "name": "Alice",
        "email": "alice@example.com",
        "department": "HR",
        "position": "Recruiter",
        "status": "active"
    }
    emp2 = {
        "employeeId": "EMP102",
        "name": "Bob",
        "email": "bob@example.com",
        "department": "Engineering",
        "position": "Developer",
        "status": "active"
    }
    await client.post("/employees/", json=emp1, headers=headers)
    await client.post("/employees/", json=emp2, headers=headers)

    resp = await client.get("/employees/?department=HR", headers=headers)
    assert resp.status_code == 200
    employees = resp.json()
    assert len(employees) == 1
    assert employees[0]["department"] == "HR"