import React, { useState, useEffect } from 'react';
import { CheckCircle, Clock, AlertCircle, XCircle } from 'lucide-react';

const statusConfig = {
  pending: { color: 'bg-gray-500/20', textColor: 'text-gray-400', icon: Clock, label: 'Pending' },
  submitted: { color: 'bg-blue-500/20', textColor: 'text-blue-400', icon: Clock, label: 'Submitted' },
  authorized: { color: 'bg-green-500/20', textColor: 'text-green-400', icon: CheckCircle, label: 'Authorized' },
  confirmed: { color: 'bg-green-500/20', textColor: 'text-green-400', icon: CheckCircle, label: 'Confirmed' },
  failed: { color: 'bg-red-500/20', textColor: 'text-red-400', icon: XCircle, label: 'Failed' },
  declined: { color: 'bg-red-500/20', textColor: 'text-red-400', icon: AlertCircle, label: 'Declined' },
  expired: { color: 'bg-yellow-500/20', textColor: 'text-yellow-400', icon: AlertCircle, label: 'Expired' },
};

export function WithdrawalStatus({ payoutId, onStatusChange }) {
  const [payout, setPayout] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPayoutStatus = async () => {
      try {
        const response = await fetch(`/api/v1/payouts/status/${payoutId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch payout status');
        }
        const data = await response.json();
        setPayout(data);

        if (onStatusChange) {
          onStatusChange(data.status);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPayoutStatus();
    const interval = setInterval(fetchPayoutStatus, 5000);
    return () => clearInterval(interval);
  }, [payoutId, onStatusChange]);

  if (loading) return <div className="text-center text-muted-foreground">Loading status...</div>;
  if (error) return <div className="text-red-400 text-sm">Error: {error}</div>;
  if (!payout) return <div className="text-muted-foreground">Payout not found</div>;

  const config = statusConfig[payout.status] || statusConfig.pending;
  const StatusIcon = config.icon;

  return (
    <div className="bg-secondary/20 p-6 rounded-xl border border-white/5">
      <h3 className="text-lg font-semibold mb-2 text-white">Withdrawal Status</h3>
      <p className="text-xs text-muted-foreground mb-4">ID: {payout._id}</p>
      
      <div className="flex items-center gap-2 mb-4">
        <StatusIcon className={`h-5 w-5 ${config.textColor}`} />
        <span className={`text-xs px-2 py-1 rounded-full uppercase tracking-wide ${config.color} ${config.textColor}`}>
          {config.label}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm mb-4">
        <div>
          <p className="text-muted-foreground">Amount</p>
          <p className="font-bold text-white">{(payout.amount / 100).toFixed(2)} {payout.currency}</p>
        </div>
        <div>
          <p className="text-muted-foreground">PSP Ref</p>
          <p className="font-mono text-white">{payout.psp_reference || '-'}</p>
        </div>
      </div>
    </div>
  );
}
