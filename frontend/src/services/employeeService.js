import axios from "axios";

const api = axios.create({
    baseURL: "",
    headers: {
        "Content-Type": "application/json",
    },
});

export async function fetchEmployees(token) {
    try {
        const response = await api.get("/employees/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        return response.data;
    } catch (error) {
        throw new Error(
            error.response?.data?.detail || "Failed to fetch employees."
        );
    }
}

export async function createEmployee(token, employeeData) {
    const response = await api.post("/employees/", employeeData, {
        headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
}

export async function updateEmployee(token, employeeId, employeeData) {
    const response = await api.put(`/employees/${employeeId}`, employeeData, {
        headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
}

export async function deleteEmployee(token, employeeId) {
    const response = await api.delete(`/employees/${employeeId}`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
}
