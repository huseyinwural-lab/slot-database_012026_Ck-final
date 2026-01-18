import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Gift, Plus, Activity } from 'lucide-react';

const BonusManagement = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newCampaign, setNewCampaign] = useState({
    name: '',
    bonus_type: 'MANUAL_CREDIT',
    status: 'draft',
    amount: 20,
    max_uses: 10,
    game_ids: [],
    is_onboarding: false,
  });
  const [reason, setReason] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const res = await api.get('/v1/bonuses/campaigns');
      setCampaigns(res.data || []);
    } catch (e) {
      toast.error('Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!reason) {
      toast.error('Reason is required');
      return;
    }
    if (!newCampaign.name.trim()) {
      toast.error('Campaign name is required');
      return;
    }

    setLoading(true);
    try {
      const config = {};
      if (newCampaign.bonus_type === 'MANUAL_CREDIT') {
        config.amount = Number(newCampaign.amount || 0);
      }
      if (newCampaign.is_onboarding) {
        config.is_onboarding = true;
      }

      const payload = {
        name: newCampaign.name,
        bonus_type: newCampaign.bonus_type,
        status: newCampaign.status,
        game_ids: newCampaign.game_ids,
        max_uses: newCampaign.bonus_type === 'MANUAL_CREDIT' ? null : Number(newCampaign.max_uses || 0),
        config,
      };

      await api.post('/v1/bonuses/campaigns', payload, { headers: { 'X-Reason': reason } });
      toast.success('Campaign created');
      setIsOpen(false);
      setReason('');
      fetchCampaigns();
    } catch (e) {
      toast.error('Creation failed');
    } finally {
      setLoading(false);
    }
  };

  const toggleStatus = async (id, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active';
    const reason = prompt(`Reason to ${newStatus} campaign?`);
    if (!reason) return;

    try {
      await api.post(`/v1/bonuses/campaigns/${id}/status`, { status: newStatus, reason });
      toast.success(`Campaign ${newStatus}`);
      fetchCampaigns();
    } catch (e) {
      toast.error('Status update failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Gift className="w-7 h-7 text-purple-500" /> Bonus Campaigns
        </h2>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="w-4 h-4 mr-2" /> New Campaign</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Bonus Campaign</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Campaign Name</Label>
                <Input value={newCampaign.name} onChange={(e) => setNewCampaign({...newCampaign, name: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Bonus Type</Label>
                <Select value={newCampaign.bonus_type} onValueChange={(v) => setNewCampaign({ ...newCampaign, bonus_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MANUAL_CREDIT">MANUAL_CREDIT</SelectItem>
                    <SelectItem value="FREE_BET">FREE_BET</SelectItem>
                    <SelectItem value="FREE_SPIN">FREE_SPIN</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={newCampaign.status} onValueChange={(v) => setNewCampaign({ ...newCampaign, status: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="draft">draft</SelectItem>
                    <SelectItem value="active">active</SelectItem>
                    <SelectItem value="paused">paused</SelectItem>
                    <SelectItem value="archived">archived</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {newCampaign.bonus_type === 'MANUAL_CREDIT' && (
                <div className="space-y-2">
                  <Label>Amount (bonus credit)</Label>
                  <Input type="number" value={newCampaign.amount} onChange={(e) => setNewCampaign({ ...newCampaign, amount: e.target.value })} />
                </div>
              )}

              {newCampaign.bonus_type !== 'MANUAL_CREDIT' && (
                <div className="space-y-2">
                  <Label>Max Uses</Label>
                  <Input type="number" value={newCampaign.max_uses} onChange={(e) => setNewCampaign({ ...newCampaign, max_uses: e.target.value })} />
                </div>
              )}

              <div className="flex items-center gap-2 pt-2">
                <input
                  id="is_onboarding"
                  type="checkbox"
                  checked={Boolean(newCampaign.is_onboarding)}
                  onChange={(e) => setNewCampaign({ ...newCampaign, is_onboarding: e.target.checked })}
                />
                <Label htmlFor="is_onboarding">Mark as onboarding campaign (config.is_onboarding=true)</Label>
              </div>

              <div className="space-y-2 pt-2 border-t">
                <Label>Audit Reason</Label>
                <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Why create this?" />
              </div>
              <Button className="w-full" onClick={handleCreate} disabled={loading}>Create Campaign</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Config</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {campaigns.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">{c.name}</TableCell>
                  <TableCell>{c.bonus_type || c.type}</TableCell>
                  <TableCell className="text-xs font-mono">
                    {JSON.stringify({ ...c.config, game_ids: c.game_ids })}
                  </TableCell>
                  <TableCell>
                    <Badge variant={c.status === 'active' ? 'default' : 'secondary'}>
                      {c.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => toggleStatus(c.id, c.status)}
                    >
                      {c.status === 'active' ? 'Pause' : 'Activate'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {campaigns.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No active campaigns.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default BonusManagement;
