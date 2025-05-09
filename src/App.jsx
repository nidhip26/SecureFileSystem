import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import Login from './pages/Login';
import Register from './pages/Register';
import SecureFileSharingGUI from './pages/SecureFileSharingGUI';
import Files from './pages/Files'; // ✅ Import Files.jsx

export default function App() {
  const [username, setUsername] = useState(localStorage.getItem('username'));
  const [password, setPassword] = useState(localStorage.getItem('password'));

  const handleLogin = (name) => {
    localStorage.setItem('username', name);
    localStorage.setItem('password', password);
    setUsername(name);
    setPassword(password);
  };

  const handleLogout = () => {
    localStorage.removeItem('username');
    setUsername(null);
  };

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            username ? (
              <SecureFileSharingGUI username={username} onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/login"
          element={
            username ? (
              <Navigate to="/" />
            ) : (
              <Login onLogin={handleLogin} />
            )
          }
        />
        <Route
          path="/register"
          element={
            username ? (
              <Navigate to="/" />
            ) : (
              <Register onRegister={handleLogin} />
            )
          }
        />

        {/* ✅ New route for Files page */}
        <Route
          path="/files"
          element={
            username ? (
              <Files />
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}
