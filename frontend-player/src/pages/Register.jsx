import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const Register = () => {
  const [formData, setForm] = useState({ username: '', email: '', password: '' });
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      // Mock Register
      // await api.post('/auth/player/register', formData);
      navigate('/login');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
      <div className="w-full max-w-md p-8 bg-secondary/30 rounded-2xl border border-white/10 backdrop-blur">
        <h1 className="text-3xl font-bold text-center mb-2">Create Account</h1>
        <p className="text-center text-muted-foreground mb-8">Join the action today</p>

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input 
                type="text" 
                value={formData.username}
                onChange={e => setForm({...formData, username: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input 
                type="email" 
                value={formData.email}
                onChange={e => setForm({...formData, email: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input 
                type="password" 
                value={formData.password}
                onChange={e => setForm({...formData, password: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
            />
          </div>
          <button type="submit" className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg transition-colors">
            Create Account
          </button>
        </form>
        
        <p className="text-center mt-6 text-sm text-muted-foreground">
            Already have an account? <a href="/login" className="text-primary hover:underline">Log In</a>
        </p>
      </div>
    </div>
  );
};

export default Register;