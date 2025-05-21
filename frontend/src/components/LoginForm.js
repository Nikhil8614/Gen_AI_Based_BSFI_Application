import React, { useState } from 'react';
import axios from 'axios';

function LoginForm({ setPage }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(
        'http://127.0.0.1:5000/login',
        { email, password },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
  
      if (res.data.token) {
        localStorage.setItem('accessToken', res.data.token);
        setPage('dashboard');
      }
    } catch (err) {
      console.error('Login error:', err);
      if (err.response?.status === 401) {
        alert('Invalid credentials');
      } else {
        alert('Login failed: ' + (err.response?.data?.error || err.message));
      }
    }
  };
  

  return (
    <form className="form-container" onSubmit={handleLogin}>
      <h3>Email</h3>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

      <h3>Password</h3>
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />

      <button type="submit">Login</button>

      <p>New user? <span onClick={() => setPage('signup')} className="link">Sign Up</span></p>
    </form>
  );
}

export default LoginForm;