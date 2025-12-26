import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, ShieldAlert } from 'lucide-react';
import api from '../services/api';

const SettingsPanel = () => {
  const [loading, setLoading] = useState(false);
  const [exclusionPeriod, setExclusionPeriod] = useState('7');
  const [message, setMessage] = useState(null);

  const handleSelfExclude = async () => {
    if (!window.confirm("Are you sure? You will not be able to login or play during this period.")) return;
    
    setLoading(true);
    try {
        await api.post('/v1/rg/self-exclude', { period_days: parseInt(exclusionPeriod) });
        setMessage({ type: 'success', text: 'Self-exclusion active. You will be logged out.' });
        setTimeout(() => {
            localStorage.clear();
            window.location.href = '/login';
        }, 2000);
    } catch (err) {
        setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to exclude.' });
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>
      
      <Card className="border-red-900/50 bg-red-950/10">
        <CardHeader>
            <div className="flex items-center gap-2">
                <ShieldAlert className="text-red-500" />
                <CardTitle className="text-red-500">Responsible Gaming</CardTitle>
            </div>
            <CardDescription>
                If you feel your gaming is getting out of control, you can temporarily lock your account.
            </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
            {message && (
                <div className={`p-3 rounded text-sm ${message.type === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                    {message.text}
                </div>
            )}
            
            <div className="space-y-2">
                <Label>Time Out Period</Label>
                <Select value={exclusionPeriod} onValueChange={setExclusionPeriod}>
                    <SelectTrigger>
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="1">24 Hours</SelectItem>
                        <SelectItem value="7">7 Days</SelectItem>
                        <SelectItem value="30">30 Days</SelectItem>
                        <SelectItem value="90">90 Days</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            
            <Button variant="destructive" onClick={handleSelfExclude} disabled={loading} className="w-full">
                {loading ? 'Processing...' : 'Self Exclude Now'}
            </Button>
            <p className="text-xs text-muted-foreground text-center">
                This action cannot be undone by support.
            </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPanel;
