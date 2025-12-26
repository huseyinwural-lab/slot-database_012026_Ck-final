import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const PlayerBonusesTab = ({ playerId }) => {
  const [grants, setGrants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState('');
  const [amount, setAmount] = useState(10);
  const [reason, setReason] = useState('');

  useEffect(() => {
    fetchData();
  }, [playerId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [gRes, cRes] = await Promise.all([
        api.get(`/v1/bonuses/player/${playerId}`),
        api.get('/v1/bonuses/campaigns')
      ]);
      setGrants(gRes.data);
      setCampaigns(cRes.data.filter(c => c.status === 'active'));
    } catch (e) {
      toast.error('Failed to load bonus data');
    } finally {
      setLoading(false);
    }
  };

  const handleGrant = async () => {
    if (!selectedCampaign || !amount || !reason) {
      toast.error('All fields required');
      return;
    }
    
    try {
      await api.post('/v1/bonuses/grant', {
        player_id: playerId,
        campaign_id: selectedCampaign,
        amount: Number(amount),
        reason: reason
      });
      toast.success('Bonus granted');
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Grant failed');
    }
  };

  return (
    <div className="space-y-6 pt-4">
      <div className="grid grid-cols-3 gap-6">
        {/* Manual Grant Form */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Manual Grant</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Campaign</label>
              <Select value={selectedCampaign} onValueChange={setSelectedCampaign}>
                <SelectTrigger><SelectValue placeholder="Select Active Campaign" /></SelectTrigger>
                <SelectContent>
                  {campaigns.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Amount</label>
              <Input type="number" value={amount} onChange={e => setAmount(e.target.value)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Reason</label>
              <Input value={reason} onChange={e => setReason(e.target.value)} placeholder="Support compensation" />
            </div>
            <Button onClick={handleGrant} disabled={loading} className="w-full">Grant Bonus</Button>
          </CardContent>
        </Card>

        {/* Grant List */}
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Bonus History</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Granted At</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Wagering</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Expires</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {grants.map(g => (
                  <TableRow key={g.id}>
                    <TableCell className="text-xs">{new Date(g.granted_at).toLocaleString()}</TableCell>
                    <TableCell>{g.amount_granted}</TableCell>
                    <TableCell>
                      {g.wagering_contributed} / {g.wagering_target}
                      <div className="w-20 h-1 bg-secondary mt-1 rounded overflow-hidden">
                        <div 
                          className="h-full bg-primary" 
                          style={{ width: `${Math.min(100, (g.wagering_contributed / g.wagering_target) * 100)}%` }}
                        />
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={g.status === 'active' ? 'default' : 'secondary'}>
                        {g.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs">{new Date(g.expires_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
                {grants.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground">No bonuses found.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PlayerBonusesTab;
