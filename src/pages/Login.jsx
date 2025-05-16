// src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Login.css';
import axios from 'axios';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const response = await axios.post("https://securefilesystem.onrender.com/login", {
          username,
          password
        });
    
        // If login is successful
        localStorage.setItem("username", username);
        localStorage.setItem("password", password);
        onLogin(username);
        navigate('/');
      } catch (err) {
        alert("Login failed: " + (err.response?.data?.error || err.message));
      }
    };
  

  return (
    <div className="login-container">
    <div className="login-card">
      <h2>Login</h2>
      <form onSubmit={handleSubmit} className="login-form">
        <input
          className="login-input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
        />
        <input
          className="login-input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
        />
        <button type="submit" className="login-button">Login</button>
      </form>
      <p className="login-footer">
        No account? <Link to="/register">Register</Link>
      </p>
    </div>
  </div>
    
  );
}
