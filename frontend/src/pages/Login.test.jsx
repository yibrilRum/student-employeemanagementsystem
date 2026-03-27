import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Login from './Login';
import * as authService from '../services/authService';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value; }),
    removeItem: vi.fn((key) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock the auth service
vi.mock('../services/authService', () => ({
  login: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  const renderLogin = () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );
  };

  it('renders the login form correctly', () => {
    renderLogin();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('submits with valid credentials and navigates on success', async () => {
    const mockToken = 'fake-jwt-token';
    authService.login.mockResolvedValue({ access_token: mockToken });

    renderLogin();

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith('testuser', 'password123');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', mockToken);
      expect(mockNavigate).toHaveBeenCalledWith('/employees');
    });
  });

  it('displays error message when login fails', async () => {
    const errorMessage = 'Invalid username or password';
    authService.login.mockRejectedValue(new Error(errorMessage));

    renderLogin();

    await userEvent.type(screen.getByLabelText(/username/i), 'wronguser');
    await userEvent.type(screen.getByLabelText(/password/i), 'wrongpass');
    await userEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
    expect(localStorageMock.setItem).not.toHaveBeenCalled();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('disables the submit button while loading', async () => {
    // Make the login promise never resolve to keep loading state
    authService.login.mockImplementation(() => new Promise(() => {}));

    renderLogin();

    await userEvent.type(screen.getByLabelText(/username/i), 'testuser');
    await userEvent.type(screen.getByLabelText(/password/i), 'pass');
    await userEvent.click(screen.getByRole('button', { name: /login/i }));

    expect(screen.getByRole('button', { name: /logging in.../i })).toBeDisabled();
  });
});