// import { useState } from 'react';
// import axios from 'axios';

// export default function Login({ onLogin }) {
//   const [username, setUsername] = useState('');
//   const [pw, setPw] = useState('');
//   const [msg, setMsg] = useState('');

//   const handleLogin = async () => {
//     try {
//       const res = await axios.post('http://127.0.0.1:5000/login', {
//         username, password: pw
//       });
//       onLogin(res.data.user);
//     } catch (err) {
//       setMsg('Invalid credentials');
//     }
//   };

//   return (
//     <div>
//       <h2>Login</h2>
//       <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
//       <input type="password" placeholder="Password" value={pw} onChange={e => setPw(e.target.value)} />
//       <button onClick={handleLogin}>Login</button>
//       <div>{msg}</div>
//     </div>
//   );
// }

// src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    // Add real auth call here
    onLogin(username);
    navigate('/');
  };

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
        <button type="submit">Login</button>
      </form>
      <p>No account? <Link to="/register">Register</Link></p>
    </div>
  );
}
