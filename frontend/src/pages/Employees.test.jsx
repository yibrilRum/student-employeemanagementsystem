import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import Employees from './Employees';
import * as employeeService from '../services/employeeService';

// Mock the employee service
vi.mock('../services/employeeService', () => ({
  fetchEmployees: vi.fn(),
}));

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

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock axios isAxiosError function
vi.mock('axios', async () => {
  const actual = await vi.importActual('axios');
  return {
    ...actual,
    isAxiosError: vi.fn(),
  };
});

describe('Employees Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  const renderEmployees = () => {
    render(
      <MemoryRouter>
        <Employees />
      </MemoryRouter>
    );
  };

  it('redirects to login when no token', () => {
    localStorageMock.getItem.mockReturnValueOnce(null);
    renderEmployees();
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('shows loading state', async () => {
    localStorageMock.getItem.mockReturnValue('fake-token');
    employeeService.fetchEmployees.mockImplementation(() => new Promise(() => {}));
    renderEmployees();
    expect(screen.getByText(/Loading employees/i)).toBeInTheDocument();
  });

  it('renders employees list on success', async () => {
    const mockEmployees = [
      { employeeId: '1', name: 'John Doe', position: 'Developer', department: 'IT' },
      { employeeId: '2', name: 'Jane Smith', position: 'Manager', department: 'HR' },
    ];
    localStorageMock.getItem.mockReturnValue('fake-token');
    employeeService.fetchEmployees.mockResolvedValue(mockEmployees);

    renderEmployees();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('Developer')).toBeInTheDocument();
      expect(screen.getByText('Manager')).toBeInTheDocument();
    });
  });

  it('shows error message on API failure', async () => {
    localStorageMock.getItem.mockReturnValue('fake-token');
    const errorMessage = 'Failed to fetch employees. Please try again later.';
    employeeService.fetchEmployees.mockRejectedValue(new Error('API error'));

    renderEmployees();

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('handles 401 by redirecting', async () => {
    localStorageMock.getItem.mockReturnValue('fake-token');
    const axiosError = { isAxiosError: true, response: { status: 401 } };
    employeeService.fetchEmployees.mockRejectedValue(axiosError);
    // Import the mocked axios module
    const axios = await import('axios');
    // Set the isAxiosError mock to return true for this error
    axios.isAxiosError.mockReturnValueOnce(true);

    renderEmployees();

    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });
});