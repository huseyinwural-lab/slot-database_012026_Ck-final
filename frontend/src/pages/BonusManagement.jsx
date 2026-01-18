import React, { useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import { postWithReason } from '../services/apiReason';
import ReasonDialog from '../components/ReasonDialog';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Gift, Plus } from 'lucide-react';

const BonusManagement = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [games, setGames] = useState([]);
  const [gameSearch, setGameSearch] = useState('');

  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [reason, setReason] = useState('');

  const [reasonModalOpen, setReasonModalOpen] = useState(false);
  const [pendingStatusChange, setPendingStatusChange] = useState(null);

  const [newCampaign, setNewCampaign] = useState({
    name: '',
    bonus_type: 'MANUAL_CREDIT',
    status: 'draft',
    amount: 20,
    max_uses: 10,
    game_ids: [],
    is_onboarding: false,
  });

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

  const fetchGames = async () => {
    try {
      const res = await api.get('/v1/games', { params: { page: 1, page_size: 200 } });
      const rows = Array.isArray(res.data) ? res.data : (res.data.items || []);
      setGames(rows || []);
    } catch {
      // no-op
    }
  };

  useEffect(() => {
    fetchCampaigns();
    fetchGames();
  }, []);

  const filteredGames = useMemo(() => {
    const q = (gameSearch || '').toLowerCase();
    return (games || []).filter((g) => (g.name || '').toLowerCase().includes(q));
  }, [games, gameSearch]);

  const toggleGame = (gameId) => {
    const exists = (newCampaign.game_ids || []).includes(gameId);
    setNewCampaign({
      ...newCampaign,
      game_ids: exists
        ? newCampaign.game_ids.filter((id) => id !== gameId)
        : [...(newCampaign.game_ids || []), gameId],
    });
  };

  const handleCreate = async () => {
    if (!reason.trim()) {
      toast.error('Audit reason is required');
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

      await postWithReason('/v1/bonuses/campaigns', reason, payload);
      toast.success('Campaign created');
      setIsOpen(false);
      setReason('');
      setNewCampaign({
        name: '',
        bonus_type: 'MANUAL_CREDIT',
        status: 'draft',
        amount: 20,
        max_uses: 10,
        game_ids: [],
        is_onboarding: false,
      });
      fetchCampaigns();
    } catch (e) {
      toast.error('Creation failed');
    } finally {
      setLoading(false);
    }
  };

  const toggleStatus = async (id, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active';
    setPendingStatusChange({ id, newStatus });
    setReasonModalOpen(true);
  };

  useEffect(() => {
    if (reasonModalOpen) {
      // Ensure focus isn't stuck in other UI (e.g., global search)
      setTimeout(() => {
        try {
          const el = document.querySelector('[data-testid="reason-input"]');
          if (el) el.focus();
        } catch {
          // no-op
        }
      }, 50);
    }
  }, [reasonModalOpen]);

  const confirmStatusChange = async (modalReason) => {
    if (!pendingStatusChange) return;

    try {
      await postWithReason(
        `/v1/bonuses/campaigns/${pendingStatusChange.id}/status`,
        modalReason,
        { status: pendingStatusChange.newStatus }
      );
      toast.success(`Campaign ${pendingStatusChange.newStatus}`);
      fetchCampaigns();
      setReasonModalOpen(false);
      setPendingStatusChange(null);
    } catch (e) {
      const code = e?.standardized?.code;
      if (code === 'REASON_REQUIRED' || code === 'REASON_MISSING') toast.error('Audit reason is required');
      else toast.error(e?.standardized?.message || 'Status update failed');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Gift className="w-6 h-6" /> Bonuses
          </h1>
          <p className="text-muted-foreground">P0.5 Reason Modal enabled — P0 Campaign management (game-scoped + onboarding flag)</p>
        </div>

        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="w-4 h-4 mr-2" /> Create Campaign</Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create Bonus Campaign</DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input value={newCampaign.name} onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })} />
              </div>

              <div className="grid grid-cols-2 gap-4">
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

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Game scope</CardTitle>
                  <CardDescription>Select which games this campaign applies to</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Input value={gameSearch} onChange={(e) => setGameSearch(e.target.value)} placeholder="Search games..." />
                  <div className="max-h-48 overflow-auto border rounded p-2 space-y-1">
                    {filteredGames.length === 0 ? (
                      <div className="text-sm text-muted-foreground">No games found</div>
                    ) : filteredGames.map((g) => (
                      <label key={g.id} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={(newCampaign.game_ids || []).includes(g.id)}
                          onChange={() => toggleGame(g.id)}
                        />
                        <span>{g.name}</span>
                        <span className="ml-auto font-mono text-xs text-muted-foreground">{g.id}</span>
                      </label>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-2 pt-2 border-t">
                <Label>Audit Reason</Label>
                <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Why create/update this?" />
              </div>

              <div className="flex justify-end">
                <Button disabled={loading} onClick={handleCreate}>Create</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <ReasonDialog
        open={reasonModalOpen}
        onOpenChange={(open) => {
          setReasonModalOpen(open);
          if (!open) setPendingStatusChange(null);
        }}
        title={pendingStatusChange?.newStatus === 'active' ? 'Activate Campaign' : 'Pause Campaign'}
        placeholder="Why are you changing campaign status?"
        confirmText={pendingStatusChange?.newStatus === 'active' ? 'Activate' : 'Pause'}
        onConfirm={confirmStatusChange}
      />

      <Card>
        <CardHeader>
          <CardTitle>Campaigns</CardTitle>
          <CardDescription>Existing bonus campaigns</CardDescription>
        </CardHeader>
        <CardContent>
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
                    <div className="flex items-center gap-2">
                      <Badge variant={c.status === 'active' ? 'default' : 'secondary'}>
                        {c.status}
                      </Badge>
                      {Array.isArray(c.game_ids) && c.game_ids.length === 0 && (
                        <Badge variant="secondary">⚠ No games scoped</Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      data-testid={`campaign-status-${c.id}`}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        toggleStatus(c.id, c.status);
                      }}
                    >
                      {c.status === 'active' ? 'Pause' : 'Activate'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}

              {campaigns.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">No campaigns</TableCell>
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
