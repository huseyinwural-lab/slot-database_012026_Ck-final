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

  const [bonusType, setBonusType] = useState('cash');
  const [bonusAmount, setBonusAmount] = useState('');
  const [bonusQty, setBonusQty] = useState('');
  const [bonusExpiry, setBonusExpiry] = useState('');
  const [bonusReason, setBonusReason] = useState('');

  const [auditItems, setAuditItems] = useState([]);
  const [note, setNote] = useState('');

  const playerId = player?.id;

  const canCreditDebitBonus = useMemo(() => {
    try {
      const u = JSON.parse(localStorage.getItem('admin_user') || 'null');
      const role = u?.role;
      return role === 'Admin';
    } catch {
      return false;
    }
  }, []);

  const canSuspendForce = useMemo(() => {
    try {
      const u = JSON.parse(localStorage.getItem('admin_user') || 'null');
      const role = u?.role;
      return role === 'Ops' || role === 'Admin';
    } catch {
      return false;
    }
  }, []);

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
    if (open) refreshAudit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, playerId]);

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
      onPlayerUpdated?.(res.data.wallet);
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
    if (!bonusReason.trim()) return toast.error('Reason is required');

    const payload = { bonus_type: bonusType, reason: bonusReason };
    if (bonusType === 'cash') {
      if (!bonusAmount || Number(bonusAmount) <= 0) return toast.error('Amount must be > 0');
      payload.amount = Number(bonusAmount);
    } else {
      if (!bonusQty || Number(bonusQty) <= 0) return toast.error('Quantity must be > 0');
      payload.quantity = Number(bonusQty);
    }
    if (bonusExpiry) payload.expires_at = bonusExpiry;

    setLoading(true);
    try {
      await api.post(`/v1/players/${playerId}/bonuses`, payload, { headers: { 'X-Reason': bonusReason } });
      toast.success('Bonus granted');
      await refreshAudit();
      setBonusAmount('');
      setBonusQty('');
      setBonusExpiry('');
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
                <Button disabled={loading || !canCreditDebitBonus} onClick={doCredit}>Credit</Button>
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
                <Button disabled={loading || !canCreditDebitBonus} onClick={doDebit}>Debit</Button>
              </div>

              <div className="space-y-3">
                <div className="font-semibold">Grant Bonus</div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label>Bonus Type</Label>
                    <Select value={bonusType} onValueChange={setBonusType}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="free_spins">Free Spins</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    {bonusType === 'cash' ? (
                      <>
                        <Label>Amount</Label>
                        <Input value={bonusAmount} onChange={(e) => setBonusAmount(e.target.value)} placeholder="5" />
                      </>
                    ) : (
                      <>
                        <Label>Quantity</Label>
                        <Input value={bonusQty} onChange={(e) => setBonusQty(e.target.value)} placeholder="10" />
                      </>
                    )}
                  </div>
                </div>
                <div>
                  <Label>Expiry (optional, ISO)</Label>
                  <Input value={bonusExpiry} onChange={(e) => setBonusExpiry(e.target.value)} placeholder="2026-12-31T00:00:00" />
                </div>
                <div>
                  <Label>Reason</Label>
                  <Input value={bonusReason} onChange={(e) => setBonusReason(e.target.value)} placeholder="Required" />
                </div>
                <Button disabled={loading || !canCreditDebitBonus} onClick={doBonus}>Grant Bonus</Button>
              </div>

              <div className="space-y-3">
                <div className="font-semibold">Account Controls</div>
                <div>
                  <Label>Reason</Label>
                  <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Required" />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button disabled={loading || !canSuspendForce} onClick={doSuspend} variant="destructive">Suspend</Button>
                  <Button disabled={loading || !canSuspendForce} onClick={doUnsuspend} variant="secondary">Unsuspend</Button>
                  <Button disabled={loading || !canSuspendForce} onClick={doForceLogout} variant="outline">Force Logout</Button>
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
