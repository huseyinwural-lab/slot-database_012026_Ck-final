import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';

const labelForStatus = (status) => {
  const s = (status || '').toLowerCase();
  const map = {
    pending: 'Pending',
    approved: 'Approved',
    processing: 'Processing',
    paid: 'Paid',
    failed: 'Failed',
    rejected: 'Rejected',
  };
  return map[s] || status || '-';
};

const badgeClassForStatus = (status) => {
  const s = (status || '').toLowerCase();
  if (s === 'pending') return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  if (s === 'approved') return 'bg-blue-100 text-blue-800 border-blue-200';
  if (s === 'processing') return 'bg-amber-100 text-amber-800 border-amber-200';
  if (s === 'paid') return 'bg-emerald-100 text-emerald-800 border-emerald-200';
  if (s === 'failed') return 'bg-red-100 text-red-800 border-red-200';
  if (s === 'rejected') return 'bg-slate-100 text-slate-800 border-slate-200';
  return 'bg-slate-100 text-slate-800 border-slate-200';
};

const formatDateTime = (v) => {
  if (!v) return '-';
  try {
    return new Date(v).toLocaleString();
  } catch {
    return String(v);
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

const Field = ({ label, value }) => (
  <div className="space-y-1">
    <div className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</div>
    <div className="text-sm break-words">{value}</div>
  </div>
);

export default function WithdrawalsDetailDrawer({ open, onOpenChange, withdrawal }) {
  const w = withdrawal || null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Withdrawal Detail</SheetTitle>
          <SheetDescription className="flex items-center gap-2">
            <span className="font-mono text-xs">{w?.id || '-'}</span>
            {w?.status ? (
              <Badge className={`border shadow-none ${badgeClassForStatus(w.status)}`}>
                {labelForStatus(w.status)}
              </Badge>
            ) : null}
          </SheetDescription>
        </SheetHeader>

        {!w ? (
          <div className="mt-6 text-sm text-muted-foreground">No item selected.</div>
        ) : (
          <div className="mt-6 grid grid-cols-1 gap-4">
            <Field label="Player" value={`${w.player_username || ''} (${w.player_email || ''})`} />
            <Field label="Player ID" value={<span className="font-mono text-xs">{w.player_id}</span>} />
            <div className="grid grid-cols-2 gap-4">
              <Field label="Amount" value={formatAmount(w.amount, w.currency)} />
              <Field label="Method" value={w.method || '-'} />
            </div>
            <Field label="Destination" value={w.destination || '-'} />
            <div className="grid grid-cols-2 gap-4">
              <Field label="KYC" value={w.kyc_status || '-'} />
              <Field label="Risk" value={w.risk_score || '-'} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Provider" value={w.provider || '-'} />
              <Field label="Provider Ref" value={w.provider_ref || '-'} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Created" value={formatDateTime(w.created_at)} />
              <Field label="Reviewed" value={formatDateTime(w.reviewed_at)} />
            </div>
            <Field label="Reviewed By" value={w.reviewed_by || '-'} />
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
