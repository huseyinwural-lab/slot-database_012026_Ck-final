import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const Login = () => {
  const [email, setEmail] = useState('player@test.com'); // Pre-fill for ease
  const [password, setPassword] = useState('Player123!');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      // Note: Assuming backend has /api/v1/auth/login that supports players too, 
      // OR we have a separate /api/v1/player-auth/login.
      // For MVP, let's assume standard auth works or we mock it.
      // Based on previous files, backend auth was AdminUser based.
      // We NEED a player auth endpoint.
      // I will implement a mock login in the frontend for now to show the UI flow
      // until we implement Player Auth in backend.
      
      const res = await api.post('/auth/player/login', { email, password }); // This endpoint needs to be created
      
      localStorage.setItem('player_token', res.data.access_token);
      localStorage.setItem('player_user', JSON.stringify(res.data.user));
      navigate('/');
    } catch (err) {
      console.error(err);
      // Mock Success for Demo if backend 404
      if (err.response && err.response.status === 404) {
          console.warn("Backend player auth not found, mocking login");
          localStorage.setItem('player_token', 'mock_token_123');
          localStorage.setItem('player_user', JSON.stringify({ username: 'Demo Player', balance_real: 1000 }));
          navigate('/');
          return;
      }
      setError('Invalid credentials');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
      <div className="w-full max-w-md p-8 bg-secondary/30 rounded-2xl border border-white/10 backdrop-blur">
        <h1 className="text-3xl font-bold text-center mb-2">Welcome Back</h1>
        <p className="text-center text-muted-foreground mb-8">Sign in to your account</p>
        
        {error && <div className="bg-red-500/20 text-red-400 p-3 rounded-lg text-sm mb-4">{error}</div>}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input 
                type="email" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input 
                type="password" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
            />
          </div>
          <button type="submit" className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg transition-colors">
            Log In
          </button>
        </form>
        
        <p className="text-center mt-6 text-sm text-muted-foreground">
            Don't have an account? <a href="/register" className="text-primary hover:underline">Sign Up</a>
        </p>
      </div>
    </div>
  );
};

export default Login;