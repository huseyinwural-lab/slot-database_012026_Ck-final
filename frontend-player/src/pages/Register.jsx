import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const Register = () => {
  const [formData, setForm] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      // Default tenant_id is handled by api.js interceptor or we can pass explicit if needed
      // For now, let's rely on the interceptor header or backend default
      await api.post('/auth/player/register', formData);
      navigate('/login');
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Registration failed. Please try again.';
      // Make 'Player exists' actionable for users.
      if (msg === 'Player exists') {
        setError('This email is already registered. Please log in instead.');
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
      <div className="w-full max-w-md p-8 bg-secondary/30 rounded-2xl border border-white/10 backdrop-blur">
        <h1 className="text-3xl font-bold text-center mb-2">Create Account</h1>
        <p className="text-center text-muted-foreground mb-8">Join the action today</p>

        {error && (
          <div className="bg-red-500/20 text-red-400 p-3 rounded-lg text-sm mb-4">
            <div>{error}</div>
            {error === 'This email is already registered. Please log in instead.' && (
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="mt-2 inline-flex items-center justify-center rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-white hover:bg-primary/90"
              >
                Go to Log In
              </button>
            )}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input 
                type="text" 
                value={formData.username}
                onChange={e => setForm({...formData, username: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
                required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input 
                type="email" 
                value={formData.email}
                onChange={e => setForm({...formData, email: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
                required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input 
                type="password" 
                value={formData.password}
                onChange={e => setForm({...formData, password: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
                required
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
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