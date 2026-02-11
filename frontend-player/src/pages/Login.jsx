import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '@/domain';
import { useToast } from '@/components/ToastProvider';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();
  const { login } = useAuthStore();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const response = await login({ email, password });
    if (response.ok) {
      toast.push('Giriş başarılı', 'success');
      navigate('/lobby');
    } else {
      setError(response.error?.message || 'Invalid credentials');
      toast.push('Giriş başarısız', 'error');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground" data-testid="login-page">
      <div className="w-full max-w-md p-8 bg-secondary/30 rounded-2xl border border-white/10 backdrop-blur">
        <h1 className="text-3xl font-bold text-center mb-2" data-testid="login-title">Welcome Back</h1>
        <p className="text-center text-muted-foreground mb-8">Sign in to your account</p>
        
        {error && <div className="bg-red-500/20 text-red-400 p-3 rounded-lg text-sm mb-4" data-testid="login-error">{error}</div>}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input 
                type="email" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
                required
                data-testid="login-email-input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input 
                type="password" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
                required
                data-testid="login-password-input"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-white/60" data-testid="login-remember-label">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              data-testid="login-remember-input"
            />
            Beni hatırla
          </label>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg transition-colors disabled:opacity-50"
            data-testid="login-submit-button"
          >
            {loading ? 'Logging In...' : 'Log In'}
          </button>
        </form>
        
        <p className="text-center mt-6 text-sm text-muted-foreground">
            Don't have an account? <Link to="/register" className="text-primary hover:underline" data-testid="login-register-link">Sign Up</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;