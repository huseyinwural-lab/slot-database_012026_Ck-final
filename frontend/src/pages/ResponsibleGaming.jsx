import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Shield, Clock, AlertTriangle } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

const ResponsibleGaming = () => {
  const [loading, setLoading] = useState(false);
  const [searchEmail, setSearchEmail] = useState('');
  const [profile, setProfile] = useState(null);
  const [reason, setReason] = useState('');
  const [action, setAction] = useState('none'); // none | exclude | cooloff

  const handleSearch = async () => {
    setLoading(true);
    try {
      // Assuming search by email via admin endpoint (not implemented in MVP route, mocking)
      // We will assume we found player with ID 'dummy'
      // To be real, we need /admin/players?email=...
      // Let's just mock profile for MVP UI demo
      setProfile({
        player_id: "demo_player",
        email: searchEmail,
        deposit_limit_daily: 100,
        self_excluded_until: null,
        self_excluded_permanent: false
      });
    } catch (e) {
      toast.error('Player not found');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!reason) {
      toast.error('Reason required');
      return;
    }
    setLoading(true);
    try {
      // Simulate Admin Override
      await api.post(`/v1/rg/admin/override/${profile.player_id}`, {
        action: action,
        reason: reason
      });
      toast.success('RG Action Applied');
    } catch (e) {
      toast.error('Action failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
        <Shield className="w-7 h-7 text-green-600" /> Responsible Gaming
      </h2>

      <Card>
        <CardHeader>
          <CardTitle>Player Intervention</CardTitle>
          <CardDescription>Look up a player to apply RG actions manually.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input 
              value={searchEmail} 
              onChange={(e) => setSearchEmail(e.target.value)} 
              placeholder="Player Email" 
            />
            <Button onClick={handleSearch} disabled={loading}>Search</Button>
          </div>

          {profile && (
            <div className="space-y-4 pt-4 border-t">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-secondary/50 rounded-md">
                  <span className="text-xs text-muted-foreground">Current Status</span>
                  <div className="text-lg font-bold">
                    {profile.self_excluded_permanent ? 'PERMANENTLY EXCLUDED' : 
                     profile.self_excluded_until ? 'TEMPORARY EXCLUSION' : 'ACTIVE'}
                  </div>
                </div>
                <div className="p-4 bg-secondary/50 rounded-md">
                  <span className="text-xs text-muted-foreground">Deposit Limit (Daily)</span>
                  <div className="text-lg font-bold">{profile.deposit_limit_daily || 'No Limit'}</div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Action</Label>
                <Select value={action} onValueChange={setAction}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No Action</SelectItem>
                    <SelectItem value="cooloff">Cool-off (24h)</SelectItem>
                    <SelectItem value="exclude_temp">Exclude (30 Days)</SelectItem>
                    <SelectItem value="exclude_perm">Exclude (Permanent)</SelectItem>
                    <SelectItem value="lift">Lift Exclusion (Dangerous)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Reason (Audit)</Label>
                <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Requested by chat" />
              </div>

              {action === 'lift' && (
                <div className="p-3 bg-red-500/10 text-red-500 rounded text-sm flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Warning: Lifting exclusion requires compliance approval.
                </div>
              )}

              <Button className="w-full" onClick={handleApply} disabled={loading || action === 'none'}>
                Apply Action
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ResponsibleGaming;
