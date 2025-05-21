import React, { useState } from 'react';
import axios from 'axios';

function SignupForm({ setPage }) {
  const [form, setForm] = useState({
    name: '',
    dob: '',
    email: '',
    phone: '',
    password: '',
    aadhar: null,
    pan: null,
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');


  const validateForm = () => {
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(form.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    
    // Phone validation (basic, assumes 10 digits)
    const phoneRegex = /^\d{10}$/;
    if (!phoneRegex.test(form.phone)) {
      setError('Please enter a valid 10-digit phone number');
      return false;
    }
    
    // Password strength (at least 8 characters with letters and numbers)
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;
    if (!passwordRegex.test(form.password)) {
      setError('Password must be at least 8 characters and include letters and numbers');
      return false;
    }
    
    // File size validation (max 5MB each)
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (form.aadhar && form.aadhar.size > maxSize) {
      setError('Aadhaar file size must be less than 5MB');
      return false;
    }
    if (form.pan && form.pan.size > maxSize) {
      setError('PAN file size must be less than 5MB');
      return false;
    }
    
    return true;
  };


  const handleChange = (e) => {
    const { name, value, files } = e.target;
    setForm({ ...form, [name]: files ? files[0] : value });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    console.log('Signup successful:');
    // Form validation
    if (!validateForm()) {
      setLoading(false);
      return;
    }
    console.log('Signup successful-1:');
    const formData = new FormData();
    Object.entries(form).forEach(([key, value]) => {
      if (value !== null) {
        formData.append(key, value);
      }
    });
    
    alert('Signup successful-2:');
    try {
        const response = await axios.post('http://127.0.0.1:5000/signup', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        console.log('Signup successful:', response.data);
        setSuccess('Account created successfully! Redirecting to login...');
        
        // Redirect to login page after 2 seconds
        setTimeout(() => {
          setPage('login');
        }, 2000);
        
      } catch (err) {
        console.error('Signup error:', err); // Full error for developer
      
        // Try to show a specific backend error if it exists
        const backendError = err.response?.data?.error;
      
        if (backendError) {
          setError(backendError);
        } else if (err.message) {
          // Show JS/network error to dev in dev mode
          setError(`Unexpected error: ${err.message}`);
        } else {
          // Fallback for totally unknown issues
          setError('Failed to sign up. Please try again.');
        }
      }
    };
  
  return (
    <div className="signup-page">
      
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <form className="form-container" onSubmit={handleSubmit}>
        <h3>Name</h3>
        <input 
          type="text" 
          name="name" 
          value={form.name}
          onChange={handleChange} 
          required 
        />
        
        <h3>Date of Birth</h3>
        <input 
          type="date" 
          name="dob" 
          value={form.dob}
          onChange={handleChange} 
          required 
        />
        
        <h3>Email</h3>
        <input 
          type="email" 
          name="email" 
          value={form.email}
          onChange={handleChange} 
          required 
        />
        
        <h3>Phone</h3>
        <input 
          type="text" 
          name="phone" 
          value={form.phone}
          onChange={handleChange} 
          required 
        />
        
        <h3>Password</h3>
        <input 
          type="password" 
          name="password" 
          value={form.password}
          onChange={handleChange} 
          required 
        />
        
        <h3>Aadhaar Upload</h3>
        <input 
          type="file" 
          name="aadhar" 
          onChange={handleChange} 
          accept=".pdf,.jpg,.png" 
          required 
        />
        
        <h3>PAN Upload</h3>
        <input 
          type="file" 
          name="pan" 
          onChange={handleChange} 
          accept=".pdf,.jpg,.png" 
          required 
        />
        
        <button type="submit" disabled={loading}>
          {loading ? 'Signing Up...' : 'Sign Up'}
        </button>
        
        <p>
          Already have an account?{' '}
          <span onClick={() => setPage('login')} className="link">
            Login
          </span>
        </p>
      </form>
    </div>
  );
}

export default SignupForm;