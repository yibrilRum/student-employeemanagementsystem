import { useEffect, useState, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchEmployees, createEmployee, updateEmployee, deleteEmployee } from '../services/employeeService';
import axios from 'axios';

const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    employeeId: '',
    name: '',
    email: '',
    department: '',
    position: '',
    status: 'active',
    salary: 0,
  });
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();
  const isAdmin = localStorage.getItem('is_admin') === 'true';
  const token = localStorage.getItem('access_token');
  const canvasRef = useRef(null);

  // Filter employees based on search term
  const filteredEmployees = useMemo(() => {
    if (!searchTerm) return employees;
    const term = searchTerm.toLowerCase();
    return employees.filter(emp =>
      emp.employeeId.toLowerCase().includes(term) ||
      emp.name.toLowerCase().includes(term) ||
      emp.department.toLowerCase().includes(term) ||
      emp.position.toLowerCase().includes(term)
    );
  }, [employees, searchTerm]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('is_admin');
    navigate('/login');
  };

  const fetchData = async () => {
    if (!token) {
      navigate('/login');
      return;
    }
    setLoading(true);
    try {
      const data = await fetchEmployees(token);
      setEmployees(data);
      setError('');
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('is_admin');
        navigate('/login');
      } else {
        setError('Failed to fetch employees. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Draw pie chart
  useEffect(() => {
    if (!employees.length) return;

    const deptCounts = employees.reduce((acc, emp) => {
      const dept = emp.department || 'Other';
      acc[dept] = (acc[dept] || 0) + 1;
      return acc;
    }, {});

    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec489a'];
    const labels = Object.keys(deptCounts);
    const data = Object.values(deptCounts);
    const total = data.reduce((a, b) => a + b, 0);

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 * 0.8;

    ctx.clearRect(0, 0, width, height);
    let startAngle = -Math.PI / 2;
    for (let i = 0; i < data.length; i++) {
      const angle = (data[i] / total) * Math.PI * 2;
      const endAngle = startAngle + angle;
      ctx.beginPath();
      ctx.fillStyle = colors[i % colors.length];
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.fill();
      startAngle = endAngle;
    }
  }, [employees]);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const resetForm = () => {
    setFormData({
      employeeId: '',
      name: '',
      email: '',
      department: '',
      position: '',
      status: 'active',
      salary: 0,
    });
    setEditingId(null);
  };

  const handleAdd = () => {
    resetForm();
    setModalOpen(true);
  };

  const handleEdit = (emp) => {
    setFormData({
      employeeId: emp.employeeId,
      name: emp.name,
      email: emp.email,
      department: emp.department,
      position: emp.position,
      status: emp.status,
      salary: emp.salary || 0,
    });
    setEditingId(emp.employeeId);
    setModalOpen(true);
  };

  const handleDelete = async (employeeId) => {
    if (!window.confirm('Are you sure you want to delete this employee?')) return;
    try {
      await deleteEmployee(token, employeeId);
      await fetchData();
    } catch (err) {
      alert('Delete failed: ' + err.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await updateEmployee(token, editingId, formData);
      } else {
        await createEmployee(token, formData);
      }
      setModalOpen(false);
      resetForm();
      await fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const total = employees.length;
  const deptCounts = employees.reduce((acc, emp) => {
    const dept = emp.department || 'Other';
    acc[dept] = (acc[dept] || 0) + 1;
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-xl">Loading employees...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navbar */}
      <nav className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-800">Employee Management System</h1>
          <div className="flex items-center space-x-4">
            {/* Search input */}
            <input
              type="text"
              placeholder="Search by ID, name, department, position..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="text-gray-500 hover:text-gray-700 text-sm"
              >
                Clear
              </button>
            )}
            {isAdmin && (
              <button
                onClick={handleAdd}
                className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-md text-sm transition"
              >
                + Add Employee
              </button>
            )}
            <button
              onClick={handleLogout}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md text-sm transition"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto p-4">
        {/* Statistics Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Summary Cards without icons */}
          <div className="col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-gray-500 text-sm">Total Employees</p>
              <p className="text-3xl font-bold text-gray-800">{total}</p>
            </div>
            {Object.entries(deptCounts).map(([dept, count]) => (
              <div key={dept} className="bg-white rounded-lg shadow p-4">
                <p className="text-gray-500 text-sm">{dept}</p>
                <p className="text-3xl font-bold text-gray-800">{count}</p>
              </div>
            ))}
          </div>
          {/* Pie Chart */}
          <div className="bg-white rounded-lg shadow p-4 flex flex-col items-center">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Department Distribution</h3>
            <canvas ref={canvasRef} width="200" height="200" className="w-40 h-40"></canvas>
            <div className="flex flex-wrap justify-center gap-2 mt-2">
              {Object.entries(deptCounts).map(([dept, count], idx) => {
                const colors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500', 'bg-purple-500', 'bg-pink-500'];
                return (
                  <div key={dept} className="flex items-center text-xs">
                    <div className={`w-3 h-3 rounded-full ${colors[idx % colors.length]} mr-1`}></div>
                    <span>{dept} ({count})</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Employee Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-b">ID</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-b">Name</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-b">Position</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-b">Department</th>
                  {isAdmin && <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-b">Actions</th>}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredEmployees.map((emp) => (
                  <tr key={emp.employeeId} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-center text-gray-900 border-r border-gray-200">{emp.employeeId}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-center text-gray-900 border-r border-gray-200">{emp.name}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-center text-gray-900 border-r border-gray-200">{emp.position}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-center text-gray-900 border-r border-gray-200">{emp.department}</td>
                    {isAdmin && (
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-center">
                        <button
                          onClick={() => handleEdit(emp)}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(emp.employeeId)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
            <h2 className="text-xl font-bold mb-4">
              {editingId ? 'Edit Employee' : 'Add Employee'}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">Employee ID</label>
                <input
                  type="text"
                  name="employeeId"
                  value={formData.employeeId}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  disabled={!!editingId}
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">Department</label>
                <input
                  type="text"
                  name="department"
                  value={formData.department}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">Position</label>
                <input
                  type="text"
                  name="position"
                  value={formData.position}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">Status</label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              <div className="mb-6">
                <label className="block text-gray-700 text-sm font-bold mb-2">Salary</label>
                <input
                  type="number"
                  name="salary"
                  value={formData.salary}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
                >
                  {editingId ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Employees;