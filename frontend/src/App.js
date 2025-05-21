import React, { useState } from 'react';
import SignupForm from './components/SignupForm';
import LoginForm from './components/LoginForm';
import Dashboard from './components/Dashboard';
import Footer from './components/Footer';

function App() {
  const [page, setPage] = useState('login');

  return (
    <div className="app-container">
      <h1 className="title">Welcome to Onboarding</h1>
      {page === 'signup' && <SignupForm setPage={setPage} />}
      {page === 'login' && <LoginForm setPage={setPage} />}
      {page === 'dashboard' && <Dashboard />}
      <Footer />
    </div>
  );
}

export default App;
