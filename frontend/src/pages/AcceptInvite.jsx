import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

const AcceptInvite = () => {
  const query = useQuery();
  const navigate = useNavigate();
  const initialToken = query.get('token') || '';

  const [token, setToken] = useState(initialToken);
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token || !password) {
      toast.error('Token and new password are required');
      return;
    }
    setSubmitting(true);
    try {
      await api.post('/v1/auth/accept-invite', {
        token,
        new_password: password,
      });
      toast.success('Invite accepted. You can now log in.');
      navigate('/login');
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (detail === 'INVITE_TOKEN_INVALID') {
        toast.error('Invite link is invalid or has already been used.');
      } else if (detail === 'INVITE_TOKEN_EXPIRED') {
        toast.error('Invite link has expired.');
      } else if (detail === 'INVITE_NOT_PENDING') {
        toast.error('This invite is not pending anymore.');
      } else {
        toast.error('Failed to accept invite');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader>
          <CardTitle>Accept Admin Invite</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Invite Token</Label>
              <Input
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Paste your invite token"
              />
            </div>
            <div>
              <Label>New Password</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Set your password"
              />
            </div>
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? 'Submitting...' : 'Accept Invite'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default AcceptInvite;
