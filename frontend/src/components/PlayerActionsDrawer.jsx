import React, { useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

const PlayerActionsDrawer = ({ open, onOpenChange, player, onPlayerUpdated }) => {
  const [loading, setLoading] = useState(false);

  const [creditAmount, setCreditAmount] = useState('');
  const [debitAmount, setDebitAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [reason, setReason] = useState('');

  const [bonusType, setBonusType] = useState('');
  const [bonusAmount, setBonusAmount] = useState('');
  const [bonusReason, setBonusReason] = useState('');

  const [bonusCampaigns, setBonusCampaigns] = useState([]);

  const selectedCampaign = useMemo(() => {
    return (bonusCampaigns || []).find((c) => c.id === bonusType) || null;
  }, [bonusCampaigns, bonusType]);

  const [auditItems, setAuditItems] = useState([]);
  const [note, setNote] = useState('');

  const playerId = player?.id;

  const permissions = useMemo(() => {
    const { getAdminFromStorage, getEffectiveRole, hasPermission, PERMISSIONS } = require('../lib/rbac');

    const admin = getAdminFromStorage();
    const effectiveRole = getEffectiveRole(admin);

    return {
      admin,
      role: effectiveRole,
      canView: hasPermission(admin, PERMISSIONS.SUPPORT_VIEW),
      canOps: hasPermission(admin, PERMISSIONS.OPS_ACTIONS),
      canAdmin: hasPermission(admin, PERMISSIONS.CREDIT_ADJUSTMENT),
    };
  }, []);

  const canCreditDebitBonus = permissions.canAdmin;
  const canSuspendForce = permissions.canOps;

  const refreshAudit = async () => {
    if (!playerId) return;
    try {
      const res = await api.get('/v1/audit/events', {
        params: { resource_type: 'player', resource_id: playerId, limit: 20, since_hours: 24 * 30 },
      });
      setAuditItems(res.data.items || []);
    } catch {
      // no-op
    }
  };

  useEffect(() => {
    if (open) {
      refreshAudit();
      refreshBonusCampaigns();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, playerId]);


  const refreshBonusCampaigns = async () => {
    try {
      const res = await api.get('/v1/bonuses/campaigns');
      const rows = res.data || [];
      setBonusCampaigns(Array.isArray(rows) ? rows.filter((c) => c.status === 'active') : []);
      if (!bonusType && Array.isArray(rows) && rows.length) {
        const firstActive = rows.find((c) => c.status === 'active');
        if (firstActive) setBonusType(firstActive.id);
      }
    } catch {
      // no-op
    }
  };


  const doCredit = async () => {
    if (!playerId) return;
    if (!creditAmount || Number(creditAmount) <= 0) return toast.error('Amount must be > 0');
    if (!reason.trim()) return toast.error('Reason is required');

    setLoading(true);
    try {
      const res = await api.post(
        `/v1/players/${playerId}/credit`,
        { amount: Number(creditAmount), currency, reason },
        { headers: { 'X-Reason': reason } }
      );
      toast.success('Credited');
      onPlayerUpdated?.({
        balance_real: res.data.balance_real,
        balance_bonus: res.data.balance_bonus,
        balance_real_available: res.data.balance_real_available,
      });
      await refreshAudit();
      setCreditAmount('');
      setReason('');
    } catch (e) {
      toast.error(e?.response?.data?.detail?.error_code === 'FORBIDDEN' ? 'Unauthorized' : 'Credit failed');
    } finally {
      setLoading(false);
    }
  };

  const doDebit = async () => {
    if (!playerId) return;
    if (!debitAmount || Number(debitAmount) <= 0) return toast.error('Amount must be > 0');
    if (!reason.trim()) return toast.error('Reason is required');

    setLoading(true);
    try {
      await api.post(
        `/v1/players/${playerId}/debit`,
        { amount: Number(debitAmount), currency, reason },
        { headers: { 'X-Reason': reason } }
      );
      toast.success('Debited');
      await refreshAudit();
      setDebitAmount('');
      setReason('');
    } catch (e) {
      const code = e?.response?.data?.detail?.error_code;
      if (e?.response?.status === 409 && code === 'INSUFFICIENT_FUNDS') toast.error('Insufficient funds');
      else toast.error(code === 'FORBIDDEN' ? 'Unauthorized' : 'Debit failed');
    } finally {
      setLoading(false);
    }
  };

  const doBonus = async () => {
    if (!playerId) return;
    
    // P0 bonus engine: campaign-based grants
    if (!bonusReason.trim()) return toast.error('Reason is required');
    if (!bonusType) return toast.error('Campaign is required');
    if (!selectedCampaign) return toast.error('Invalid campaign');
    const campaignType = selectedCampaign.bonus_type || selectedCampaign.type;
    if (campaignType !== 'MANUAL_CREDIT') {
      return toast.error('Only MANUAL_CREDIT can be granted from here (P0)');
    }
    if (!bonusAmount || Number(bonusAmount) <= 0) return toast.error('Amount must be > 0');

    const payload = {
      campaign_id: bonusType,
      player_id: playerId,
      amount: Number(bonusAmount),
    };

    setLoading(true);
    try {
      await api.post(`/v1/bonuses/grant`, payload, { headers: { 'X-Reason': bonusReason } });
      toast.success('Bonus granted');
      await refreshAudit();
      setBonusAmount('');
      setBonusReason('');
    } catch (e) {
      toast.error(e?.response?.data?.detail?.error_code === 'FORBIDDEN' ? 'Unauthorized' : 'Bonus failed');
    } finally {
      setLoading(false);
    }
  };

  const doSuspend = async () => {
    if (!playerId) return;
    if (!reason.trim()) return toast.error('Reason is required');
    setLoading(true);
    try {
      const res = await api.post(`/v1/players/${playerId}/suspend`, { reason }, { headers: { 'X-Reason': reason } });
      toast.success('Suspended');
      onPlayerUpdated?.({ status: res.data.status });
      await refreshAudit();
      setReason('');
    } catch (e) {
      toast.error(e?.response?.data?.detail?.error_code === 'FORBIDDEN' ? 'Unauthorized' : 'Suspend failed');
    } finally {
      setLoading(false);
    }
  };

  const doUnsuspend = async () => {
    if (!playerId) return;
    if (!reason.trim()) return toast.error('Reason is required');
    setLoading(true);
    try {
      const res = await api.post(`/v1/players/${playerId}/unsuspend`, { reason }, { headers: { 'X-Reason': reason } });
      toast.success('Unsuspended');
      onPlayerUpdated?.({ status: res.data.status });
      await refreshAudit();
      setReason('');
    } catch (e) {
      const code = e?.response?.data?.detail?.error_code;
      if (e?.response?.status === 409 && code === 'STATE_MISMATCH') toast.error('State mismatch');
      else toast.error(code === 'FORBIDDEN' ? 'Unauthorized' : 'Unsuspend failed');
    } finally {
      setLoading(false);
    }
  };

  const doForceLogout = async () => {
    if (!playerId) return;
    if (!reason.trim()) return toast.error('Reason is required');
    setLoading(true);
    try {
      await api.post(`/v1/players/${playerId}/force-logout`, { reason }, { headers: { 'X-Reason': reason } });
      toast.success('Force logout sent');
      await refreshAudit();
      setReason('');
    } catch (e) {
      toast.error(e?.response?.data?.detail?.error_code === 'FORBIDDEN' ? 'Unauthorized' : 'Force logout failed');
    } finally {
      setLoading(false);
    }
  };

  const addNote = async () => {
    if (!playerId) return;
    if (!note.trim()) return toast.error('Note is required');
    setLoading(true);
    try {
      await api.post(`/v1/players/${playerId}/notes`, { note, reason: note }, { headers: { 'X-Reason': note } });
      toast.success('Note added');
      setNote('');
      await refreshAudit();
    } catch {
      toast.error('Failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Player Actions</DialogTitle>
          {player && (
            <div className="text-sm text-muted-foreground">
              <div className="font-medium text-foreground">{player.username} <span className="text-muted-foreground">({player.email})</span></div>
              <div className="font-mono text-xs">{player.id}</div>
            </div>
          )}
        </DialogHeader>

        <Tabs defaultValue="quick">
          <TabsList>
            <TabsTrigger value="quick">Quick Actions</TabsTrigger>
            <TabsTrigger value="audit">Notes / Audit</TabsTrigger>
          </TabsList>

          <TabsContent value="quick" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="font-semibold">Credit</div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label>Amount</Label>
                    <Input value={creditAmount} onChange={(e) => setCreditAmount(e.target.value)} placeholder="10" />
                  </div>
                  <div>
                    <Label>Currency</Label>
                    <Input value={currency} onChange={(e) => setCurrency(e.target.value)} placeholder="USD" />
                  </div>
                </div>
                <div>
                  <Label>Reason</Label>
                  <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Required" />
                </div>
                {/* RBAC Credit Button */}
                {canCreditDebitBonus ? (
                  <Button data-testid="player-action-credit" disabled={loading} onClick={doCredit}>Credit</Button>
                ) : null}
              </div>

              <div className="space-y-3">
                <div className="font-semibold">Debit</div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label>Amount</Label>
                    <Input value={debitAmount} onChange={(e) => setDebitAmount(e.target.value)} placeholder="10" />
                  </div>
                  <div>
                    <Label>Currency</Label>
                    <Input value={currency} onChange={(e) => setCurrency(e.target.value)} placeholder="USD" />
                  </div>
                </div>
                <div>
                  <Label>Reason</Label>
                  <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Required" />
                </div>
                {canCreditDebitBonus ? (
                  <Button data-testid="player-action-debit" disabled={loading} onClick={doDebit}>Debit</Button>
                ) : null}
              </div>

              <div className="space-y-3">
                <div className="font-semibold">Grant Bonus</div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label>Campaign</Label>
                    <Select value={bonusType} onValueChange={setBonusType}>
                      <SelectTrigger><SelectValue placeholder="Select campaign" /></SelectTrigger>
                      <SelectContent>
                        {bonusCampaigns.map((c) => (
                          <SelectItem key={c.id} value={c.id}>
                            {c.name} ({c.bonus_type || c.type})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Amount</Label>
                    <Input value={bonusAmount} onChange={(e) => setBonusAmount(e.target.value)} placeholder="20" />
                  </div>
                </div>
                <div>
                  <Label>Reason</Label>
                  <Input value={bonusReason} onChange={(e) => setBonusReason(e.target.value)} placeholder="Required" />
                </div>
                {canCreditDebitBonus ? (
                  <Button data-testid="player-action-bonus" disabled={loading} onClick={doBonus}>Grant Bonus</Button>
                ) : null}
              </div>

              <div className="space-y-3">
                <div className="font-semibold">Account Controls</div>
                <div>
                  <Label>Reason</Label>
                  <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Required" />
                </div>
                <div className="flex flex-wrap gap-2">
                  {canSuspendForce ? (
                    <>
                      <Button data-testid="player-action-suspend" disabled={loading} onClick={doSuspend} variant="destructive">Suspend</Button>
                      <Button data-testid="player-action-unsuspend" disabled={loading} onClick={doUnsuspend} variant="secondary">Unsuspend</Button>
                      <Button data-testid="player-action-force-logout" disabled={loading} onClick={doForceLogout} variant="outline">Force Logout</Button>
                    </>
                  ) : null}
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="audit" className="space-y-4">
            <div className="space-y-2">
              <Label>Internal Note</Label>
              <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Add an internal note..." />
              <Button disabled={loading} onClick={addNote}>Add Note</Button>
            </div>

            <div className="space-y-2">
              <div className="font-semibold">Last actions</div>
              <div className="max-h-64 overflow-auto border rounded-md">
                {auditItems.length === 0 ? (
                  <div className="p-3 text-sm text-muted-foreground">No events.</div>
                ) : (
                  <div className="divide-y">
                    {auditItems.map((e) => (
                      <div key={e.id} className="p-3 text-sm">
                        <div className="font-mono text-xs text-muted-foreground">{e.timestamp} · {e.action} · {e.status}</div>
                        <div>{e.reason || ''}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default PlayerActionsDrawer;
