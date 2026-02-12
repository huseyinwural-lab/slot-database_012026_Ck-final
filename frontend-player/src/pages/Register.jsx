import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore, useComplianceStore } from '@/domain';
import { useToast } from '@/components/ToastProvider';

const Register = () => {
  const [formData, setForm] = useState({
    username: '',
    email: '',
    phone: '',
    dob: '',
    accepted: false,
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const toast = useToast();
  const { register } = useAuthStore();
  const { verifyAge } = useComplianceStore();

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const ageOk = verifyAge({ dob: formData.dob, accepted: formData.accepted });
    if (!ageOk) {
      setError('18 yaş doğrulaması gerekli');
      setLoading(false);
      return;
    }

    const response = await register({
      username: formData.username,
      email: formData.email,
      phone: formData.phone,
      dob: formData.dob,
      password: formData.password,
      tenant_id: 'default_casino',
    });
    
    if (response.ok) {
      toast.push('Kayıt başarılı', 'success');
      navigate('/verify/email');
    } else {
      // Handle Rate Limit explicitly in UI text if needed, or generic
      if (response.error?.code === "RATE_LIMITED") {
         setError("Too many attempts. Please wait.");
      } else {
         setError(response.error?.message || 'Registration failed. Please try again.');
      }
      toast.push('Kayıt başarısız', 'error');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground" data-testid="register-page">
      <div className="w-full max-w-md p-8 bg-secondary/30 rounded-2xl border border-white/10 backdrop-blur">
        <h1 className="text-3xl font-bold text-center mb-2" data-testid="register-title">Create Account</h1>
        <p className="text-center text-muted-foreground mb-8">Join the action today</p>

        {error && (
          <div className="bg-red-500/20 text-red-400 p-3 rounded-lg text-sm mb-4" data-testid="register-error">
            <div>{error}</div>
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
                data-testid="register-username-input"
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
                data-testid="register-email-input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Phone</label>
            <input
                type="tel"
                value={formData.phone}
                onChange={e => setForm({...formData, phone: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
                required
                data-testid="register-phone-input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Date of Birth</label>
            <input
                type="date"
                value={formData.dob}
                onChange={e => setForm({...formData, dob: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
                required
                data-testid="register-dob-input"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-white/60" data-testid="register-age-consent">
            <input
              type="checkbox"
              checked={formData.accepted}
              onChange={(e) => setForm({ ...formData, accepted: e.target.checked })}
              data-testid="register-age-checkbox"
            />
            18 yaşından büyüğüm ve şartları kabul ediyorum
          </label>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input 
                type="password" 
                value={formData.password}
                onChange={e => setForm({...formData, password: e.target.value})}
                className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:outline-none focus:border-primary"
                required
                data-testid="register-password-input"
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg transition-colors disabled:opacity-50"
            data-testid="register-submit-button"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
        
        <p className="text-center mt-6 text-sm text-muted-foreground">
            Already have an account? <Link to="/login" className="text-primary hover:underline" data-testid="register-login-link">Log In</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
