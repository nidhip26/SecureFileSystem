// src/App.jsx
import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import Login from './pages/Login';
import Register from './pages/Register';
import SecureFileSharingGUI from './pages/SecureFileSharingGUI';

export default function App() {
  const [username, setUsername] = useState(localStorage.getItem('username'));

  const handleLogin = (name) => {
    localStorage.setItem('username', name);
    setUsername(name);
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
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}
