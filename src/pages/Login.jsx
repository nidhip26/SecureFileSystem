// src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Login.css';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    localStorage.setItem('username', username); 
    localStorage.setItem('password', password); 
    onLogin(username)
    navigate('/');
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