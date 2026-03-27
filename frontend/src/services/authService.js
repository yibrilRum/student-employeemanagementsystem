import axios from "axios";

const api = axios.create({
    baseURL: "",
    headers: {
        "Content-Type": "application/json",
    },
});

function decodeToken(token) {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch (e) {
    return null;
  }
}

export async function login(username, password) {
    try {
        const response = await api.post("/auth/login", { username, password });
        const token = response.data.access_token;
        localStorage.setItem('access_token', token);
        const decoded = decodeToken(token);
        if (decoded && typeof decoded.is_admin !== 'undefined') {
            localStorage.setItem('is_admin', decoded.is_admin);
        }
        return response.data;
    } catch (error) {
        throw new Error(
            error.response?.data?.detail || "Login failed. Please try again."
        );
    }
}

export async function register(username, email, password) {
    try {
        const response = await api.post("/auth/register", { username, email, password });
        return response.data;
    } catch (error) {
        throw new Error(
            error.response?.data?.detail || "Registration failed. Please try again."
        );
    }
}
