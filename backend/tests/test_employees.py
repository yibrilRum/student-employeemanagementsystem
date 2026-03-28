import pytest

@pytest.fixture
def admin_token(client):
    """Create an admin user and return its token."""
    # Register admin
    resp = client.post("/auth/register", json={
        "username": "admin_test",
        "email": "admin_test@example.com",
        "password": "adminpass",
        "is_admin": True
    })
    assert resp.status_code == 201
    # Login
    resp = client.post("/auth/login", json={
        "username": "admin_test",
        "password": "adminpass"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_add_employee_success(client, admin_token):
    response = client.post("/employees/",
                           headers={"Authorization": f"Bearer {admin_token}"},
                           json={
                               "employeeId": "EMP001",
                               "name": "Alice Johnson",
                               "email": "alice@example.com",
                               "department": "Engineering",
                               "position": "Frontend Developer",
                               "status": "active",
                               "salary": 75000
                           })
    assert response.status_code == 200
    data = response.json()
    assert data["employeeId"] == "EMP001"
    assert data["name"] == "Alice Johnson"
    assert "createdAt" in data

def test_add_duplicate_employee_fails(client, admin_token):
    # Add first employee
    client.post("/employees/",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "employeeId": "EMP002",
                    "name": "Bob",
                    "email": "bob@example.com",
                    "department": "HR",
                    "position": "Manager",
                    "status": "active"
                })
    # Try duplicate
    response = client.post("/employees/",
                           headers={"Authorization": f"Bearer {admin_token}"},
                           json={
                               "employeeId": "EMP002",
                               "name": "Bob2",
                               "email": "bob2@example.com",
                               "department": "HR",
                               "position": "Manager",
                               "status": "active"
                           })
    assert response.status_code == 409
    assert "Employee ID already exists" in response.json()["detail"]

def test_get_employees_list(client, admin_token):
    # Add two employees
    client.post("/employees/",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "employeeId": "EMP003",
                    "name": "Carol",
                    "email": "carol@example.com",
                    "department": "Engineering",
                    "position": "Backend Dev",
                    "status": "active"
                })
    client.post("/employees/",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "employeeId": "EMP004",
                    "name": "Dave",
                    "email": "dave@example.com",
                    "department": "Marketing",
                    "position": "Specialist",
                    "status": "active"
                })
    response = client.get("/employees/",
                          headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    ids = [e["employeeId"] for e in data]
    assert "EMP003" in ids and "EMP004" in ids

def test_get_employee_by_id(client, admin_token):
    # Ensure employee exists
    client.post("/employees/",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "employeeId": "EMP003",
                    "name": "Carol",
                    "email": "carol@example.com",
                    "department": "Engineering",
                    "position": "Backend Dev",
                    "status": "active"
                })
    response = client.get("/employees/EMP003",
                          headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["employeeId"] == "EMP003"
    assert data["name"] == "Carol"

def test_get_employee_not_found(client, admin_token):
    response = client.get("/employees/NONEXISTENT",
                          headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404

def test_update_employee(client, admin_token):
    # Create the employee first
    client.post("/employees/",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "employeeId": "EMP003",
                    "name": "Carol",
                    "email": "carol@example.com",
                    "department": "Engineering",
                    "position": "Backend Dev",
                    "status": "active"
                })
    # Update with all required fields (since the endpoint expects full EmployeeCreate)
    update_data = {
        "employeeId": "EMP003",
        "name": "Carol Updated",
        "email": "carol@example.com",
        "department": "Engineering",
        "position": "Backend Dev",
        "status": "active",
        "salary": 85000
    }
    response = client.put("/employees/EMP003",
                          headers={"Authorization": f"Bearer {admin_token}"},
                          json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Carol Updated"
    assert data["salary"] == 85000

def test_delete_employee(client, admin_token):
    # Create employee
    client.post("/employees/",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "employeeId": "EMP006",
                    "name": "Grace",
                    "email": "grace@example.com",
                    "department": "Sales",
                    "position": "Rep",
                    "status": "active"
                })
    response = client.delete("/employees/EMP006",
                             headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    # Verify deletion
    resp = client.get("/employees/EMP006",
                      headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404

def test_delete_employee_not_found(client, admin_token):
    response = client.delete("/employees/NONEXISTENT",
                             headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404

def test_filter_employees_by_department(client, admin_token):
    # Add an employee in HR
    client.post("/employees/",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "employeeId": "EMP005",
                    "name": "Eve",
                    "email": "eve@example.com",
                    "department": "HR",
                    "position": "Recruiter",
                    "status": "active"
                })
    response = client.get("/employees/?department=HR",
                          headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["employeeId"] == "EMP005"