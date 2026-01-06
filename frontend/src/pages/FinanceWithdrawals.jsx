import React, { useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import WithdrawalsDetailDrawer from '../components/WithdrawalsDetailDrawer';
import { callMoneyAction } from '../services/moneyActions';
import { moneyPathErrorMessage } from '../services/moneyPathErrors';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Pagination, PaginationContent, PaginationItem, PaginationPrevious, PaginationNext } from '@/components/ui/pagination';
import { toast } from 'sonner';
import { ArrowDownRight, CheckCircle2, XCircle, Copy } from 'lucide-react';


const ADMIN_SCOPE = 'admin';

const makeRowKey = (txId, action) => `${ADMIN_SCOPE}:${txId}:${action}`;

const STATE_LABELS = {
  requested: 'Requested',
  approved: 'Approved',
  payout_pending: 'Payout Pending',
  payout_failed: 'Payout Failed',
  paid: 'Paid',
  rejected: 'Rejected',
};

const STATE_CLASSES = {
  requested: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  approved: 'bg-blue-100 text-blue-800 border-blue-200',
  payout_pending: 'bg-amber-100 text-amber-800 border-amber-200',
  payout_failed: 'bg-red-100 text-red-800 border-red-200',
  paid: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  rejected: 'bg-slate-100 text-slate-800 border-slate-200',
};

const renderStateBadge = (state) => {
  const label = STATE_LABELS[state] || state;
  const extra = STATE_CLASSES[state] || '';
  return (
    <Badge variant="outline" className={`uppercase text-[10px] ${extra}`}>
      {label}
    </Badge>
  );
};

const PAGE_SIZE = 50;

const formatDateTime = (value) => {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
};

const formatAmount = (amount, currency) => {
  if (amount == null) return '-';
  try {
    const n = Number(amount);
    const formatted = n.toLocaleString(undefined, { maximumFractionDigits: 2 });
    return `${formatted} ${currency || ''}`.trim();
  } catch {
    return `${amount} ${currency || ''}`.trim();
  }
};

const FinanceWithdrawals = () => {
  const [filters, setFilters] = useState({
    status: 'all',
    q: '',
    provider_ref: '',
  });

  const [items, setItems] = useState([]);
  const [meta, setMeta] = useState({ total: 0, limit: PAGE_SIZE, offset: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const [selectedWithdrawal, setSelectedWithdrawal] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const [actionModal, setActionModal] = useState({ open: false, type: null, tx: null });
  const [actionReason, setActionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [rowStatus, setRowStatus] = useState({}); // key -> { status, message }

  const handleCopyTxId = async (txId) => {
    try {
      await navigator.clipboard.writeText(txId);
      toast.success('Transaction ID copied');
    } catch {
      // ignore
    }
  };

  const fetchWithdrawals = async (pageOverride) => {
    const nextPage = pageOverride || page;
    const limit = PAGE_SIZE;
    const offset = (nextPage - 1) * limit;

    setLoading(true);
    try {
      const params = {
        limit,
        offset,
      };

      if (filters.status && filters.status !== 'all') params.status = filters.status;
      if (filters.q) params.q = filters.q;
      if (filters.provider_ref) params.provider_ref = filters.provider_ref;
      // Backend defaults to created_at DESC; make it explicit for contract clarity.
      params.sort = 'created_at_desc';

      // P0 decision: Withdrawal approvals live under /withdrawals (source of truth)
      const res = await api.get('/v1/withdrawals', { params });
      setItems(res.data.items || []);
      setMeta(res.data.meta || { total: 0, limit, offset });
      setPage(nextPage);
    } catch (err) {
      const message = err?.standardized?.message || 'Failed to load withdrawals';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial load
    fetchWithdrawals(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const applyFilters = () => {
    // Filter change -> offset reset (page 1)
    fetchWithdrawals(1);
  };

  const handleOpenDetail = (w) => {
    setSelectedWithdrawal(w);
    setIsDetailOpen(true);
  };

  const handleCloseDetail = () => {
    setIsDetailOpen(false);
    setSelectedWithdrawal(null);
  };

  const handleActionError = async (err) => {
    const status = err?.response?.status;
    const code = err?.standardized?.code;
    const message = moneyPathErrorMessage(err);

    if (status === 409 && code === 'IDEMPOTENCY_KEY_REUSE_CONFLICT') {
      toast.warning('İşlem anahtarı çakışması', {
        description: message,
      });
      await fetchWithdrawals(1);
      return;
    }

    if (status === 409 && code === 'INVALID_STATE_TRANSITION') {
      toast.warning('Kayıt durumu değişti', {
        description: message,
      });
      await fetchWithdrawals(1);
      return;
    }

    // Other errors (401/403/5xx) interceptor zaten Request ID içeren toast basıyor;
    // burada sadece ek, daha kullanıcı-dostu bir mesaj gösteriyoruz.
    toast.error(message);
  };

  const updateRowStatus = (txId, action, status, message) => {
    const key = makeRowKey(txId, action);
    setRowStatus((prev) => ({
      ...prev,
      [key]: { status, message },
    }));
  };

  // P0 scope: Withdrawals page is the source of truth and supports
  // approve/reject + manual mark paid/failed.
  // No PSP / payout-start workflow in P0 here.

  const openActionModal = (tx, type) => {
    setActionModal({ open: true, type, tx });
    setActionReason('');
  };

  const openActionModal = (tx, type) => {
    setActionModal({ open: true, type, tx });
    setActionReason('');
  };

  const handleActionConfirm = async () => {
    const { type, tx } = actionModal;
    if (!tx || !actionReason.trim()) return;
    
    const txId = tx.tx_id;
    setActionLoading(true);
    updateRowStatus(txId, type, 'in_flight');

    try {
      await callMoneyAction({
        scope: ADMIN_SCOPE,
        id: txId,
        action: type,
        requestFn: (idemKey) => {
          const headers = { 'Idempotency-Key': idemKey };
          
          if (type === 'approve') {
             return api.post(`/v1/finance/withdrawals/${txId}/review`, { action: 'approve', reason: actionReason.trim() }, { headers });
          }
          if (type === 'reject') {
             return api.post(`/v1/finance/withdrawals/${txId}/review`, { action: 'reject', reason: actionReason.trim() }, { headers });
          }
          if (type === 'mark_paid') {
             return api.post(`/v1/finance/withdrawals/${txId}/mark-paid`, { reason: actionReason.trim() }, { headers });
          }
          throw new Error('Unknown action type');
        },
        onStatus: (status) => {
          updateRowStatus(txId, type, status.status || status, status.message);
        },
      });

      const successMsgs = {
        approve: 'Withdrawal approved',
        reject: 'Withdrawal rejected',
        mark_paid: 'Withdrawal marked as paid',
      };
      toast.success(successMsgs[type] || 'Action completed');
      
      setActionModal({ open: false, type: null, tx: null });
      setActionReason('');
      await fetchWithdrawals(page);
    } catch (err) {
      await handleActionError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const totalPages = meta.limit ? Math.max(1, Math.ceil((meta.total || 0) / meta.limit)) : 1;

  const canApproveOrReject = (w) => (w?.status || '').toLowerCase() === 'pending';
  const canMarkPaid = (w) => {
    const s = (w?.status || '').toLowerCase();
    return s === 'approved' || s === 'processing';
  };
  const canMarkFailed = (w) => (w?.status || '').toLowerCase() === 'processing';

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <ArrowDownRight className="w-7 h-7 text-emerald-500" /> Withdrawals
          </h2>
          <p className="text-muted-foreground text-sm">
            Review, approve or reject player withdrawal requests and track payout status.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter withdrawal requests by state, player and date range.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="w-44">
              <Label htmlFor="status">Status</Label>
              <Select value={filters.status} onValueChange={(v) => setFilters((f) => ({ ...f, status: v }))}>
                <SelectTrigger id="status">
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="w-72">
              <Label htmlFor="q">Search</Label>
              <Input
                id="q"
                placeholder="player / request id / provider ref"
                value={filters.q}
                onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
              />
            </div>

            <div className="w-56">
              <Label htmlFor="provider_ref">Provider Ref</Label>
              <Input
                id="provider_ref"
                placeholder="(optional)"
                value={filters.provider_ref}
                onChange={(e) => setFilters((f) => ({ ...f, provider_ref: e.target.value }))}
              />
            </div>

            <div className="flex gap-2 ml-auto">
              <Button onClick={applyFilters} disabled={loading}>
                Apply
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Withdrawal Requests</CardTitle>
            <CardDescription>
              {meta.total || 0} total result{(meta.total || 0) === 1 ? '' : 's'}. Page {page} of {totalPages}.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tx ID</TableHead>
                  <TableHead>Player ID</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>State</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Reviewed By</TableHead>
                  <TableHead>Reviewed At</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-6 text-muted-foreground">
                      Loading withdrawals...
                    </TableCell>
                  </TableRow>
                ) : items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-6 text-muted-foreground">
                      No withdrawals found for current filters.
                    </TableCell>
                  </TableRow>
                ) : (
                  items.map((tx) => (
                    <TableRow key={tx.tx_id} className="cursor-pointer" onClick={() => handleOpenDetail(tx)}>
                      <TableCell className="font-mono text-xs" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-2">
                          <span>{tx.tx_id}</span>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCopyTxId(tx.tx_id);
                            }}
                          >
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-xs">{tx.player_id}</TableCell>
                      <TableCell>{formatAmount(tx.amount, tx.currency)}</TableCell>
                      <TableCell>
                        {renderStateBadge(tx.state)}
                      </TableCell>
                      <TableCell className="text-xs">{formatDateTime(tx.created_at)}</TableCell>
                      <TableCell className="text-xs">{tx.reviewed_by || '-'}</TableCell>
                      <TableCell className="text-xs">{formatDateTime(tx.reviewed_at)}</TableCell>
                      <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-2">
                          {canApproveOrReject(tx) && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={actionLoading}
                                onClick={() => openActionModal(tx, 'approve')}
                              >
                                <CheckCircle2 className="w-4 h-4 mr-1" /> Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                disabled={actionLoading}
                                onClick={() => openActionModal(tx, 'reject')}
                              >
                                <XCircle className="w-4 h-4 mr-1" /> Reject
                              </Button>
                            </>
                          )}
                          {canMarkPaid(tx) && (
                            <Button
                              size="sm"
                              variant="default"
                              disabled={actionLoading}
                              onClick={() => openActionModal(tx, 'mark_paid')}
                            >
                              <CheckCircle2 className="w-4 h-4 mr-1" /> Mark Paid
                            </Button>
                          )}
                          {canStartOrRetryPayout(tx) && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={actionLoading}
                              onClick={() => handleStartOrRetryPayout(tx)}
                            >
                              <CheckCircle2 className="w-4 h-4 mr-1" />
                              {tx.state === 'payout_failed' ? 'Retry Payout' : 'Start Payout'}
                            </Button>
                          )}
                          {canRecheck(tx) && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={actionLoading}
                              onClick={() => handleRecheck(tx)}
                            >
                              Recheck
                            </Button>
                          )}
                        </div>
                        {/* Row-level inline status for money-path actions */}
                        <div className="mt-1 text-right text-[11px] text-muted-foreground min-h-[1rem]">
                          {(() => {
                            const approveKey = makeRowKey(tx.tx_id, 'approve');
                            const rejectKey = makeRowKey(tx.tx_id, 'reject');
                            const markPaidKey = makeRowKey(tx.tx_id, 'mark_paid');
                            const payoutStartKey = makeRowKey(tx.tx_id, 'payout_start');
                            const payoutRetryKey = makeRowKey(tx.tx_id, 'payout_retry');
                            const recheckKey = makeRowKey(tx.tx_id, 'recheck');
                            const statusEntry =
                              rowStatus[approveKey] ||
                              rowStatus[rejectKey] ||
                              rowStatus[markPaidKey] ||
                              rowStatus[payoutStartKey] ||
                              rowStatus[payoutRetryKey] ||
                              rowStatus[recheckKey];

                            if (!statusEntry) return null;
                            if (statusEntry.status === 'in_flight') return 'İşlem yürütülüyor...';
                            if (statusEntry.status === 'failed')
                              return statusEntry.message || 'İşlem sırasında hata oluştu.';
                            if (statusEntry.status === 'done') return 'İşlem tamamlandı.';
                            return null;
                          })()}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
              <div>
                Showing {meta.offset + 1}–
                {Math.min(meta.offset + (meta.limit || PAGE_SIZE), meta.total || 0)} of {meta.total || 0}
              </div>
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      onClick={() => page > 1 && fetchWithdrawals(page - 1)}
                      className={page <= 1 ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationNext
                      onClick={() => page < totalPages && fetchWithdrawals(page + 1)}
                      className={page >= totalPages ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Modal */}
      <Dialog open={isDetailOpen && !!selectedTx} onOpenChange={(open) => !open && handleCloseDetail()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Withdrawal Detail</DialogTitle>
            <DialogDescription>
              Transaction ID: <span className="font-mono text-xs">{selectedTx?.tx_id}</span>
            </DialogDescription>
          </DialogHeader>
          {selectedTx && (
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="font-semibold">Player ID:</span> {selectedTx.player_id}
                </div>
                <div>
                  <span className="font-semibold">Amount:</span> {formatAmount(selectedTx.amount, selectedTx.currency)}
                </div>
                <div>
                  <span className="font-semibold">State:</span> {selectedTx.state}
                </div>
                <div>
                  <span className="font-semibold">Created At:</span> {formatDateTime(selectedTx.created_at)}
                </div>
                <div>
                  <span className="font-semibold">Reviewed By:</span> {selectedTx.reviewed_by || '-'}
                </div>
                <div>
                  <span className="font-semibold">Reviewed At:</span> {formatDateTime(selectedTx.reviewed_at)}
                </div>
              </div>
              <div>
                <span className="font-semibold">Balance snapshot after tx:</span>{' '}
                {selectedTx.balance_after != null ? selectedTx.balance_after : '-'}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Action Modal */}
      <Dialog open={actionModal.open} onOpenChange={(open) => !open && setActionModal(prev => ({ ...prev, open: false }))}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="capitalize">
              {actionModal.type === 'mark_paid' ? 'Mark as Paid' : actionModal.type} Withdrawal
            </DialogTitle>
            <DialogDescription>
              Please provide a reason for this action. This will be logged to the audit trail.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="action-reason">Reason (Required)</Label>
            <Textarea
              id="action-reason"
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
              placeholder="Enter reason..."
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setActionModal(prev => ({ ...prev, open: false }))}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              variant={actionModal.type === 'reject' ? 'destructive' : 'default'}
              onClick={handleActionConfirm}
              disabled={actionLoading || !actionReason.trim()}
            >
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FinanceWithdrawals;
