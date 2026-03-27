import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Employees from './pages/Employees';
import Register from './pages/Register';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/employees" element={<Employees />} />
        <Route path="/" element={<Login />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
