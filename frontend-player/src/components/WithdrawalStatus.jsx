import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Clock, AlertCircle, XCircle } from 'lucide-react';

const statusConfig = {
  pending: { color: 'bg-gray-100', textColor: 'text-gray-800', icon: Clock, label: 'Pending' },
  submitted: { color: 'bg-blue-100', textColor: 'text-blue-800', icon: Clock, label: 'Submitted' },
  authorized: { color: 'bg-green-100', textColor: 'text-green-800', icon: CheckCircle, label: 'Authorized' },
  confirmed: { color: 'bg-green-100', textColor: 'text-green-800', icon: CheckCircle, label: 'Confirmed' },
  failed: { color: 'bg-red-100', textColor: 'text-red-800', icon: XCircle, label: 'Failed' },
  declined: { color: 'bg-red-100', textColor: 'text-red-800', icon: AlertCircle, label: 'Declined' },
  expired: { color: 'bg-yellow-100', textColor: 'text-yellow-800', icon: AlertCircle, label: 'Expired' },
};

export function WithdrawalStatus({ payoutId, onStatusChange }) {
  const [payout, setPayout] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPayoutStatus = async () => {
      try {
        const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';
        const response = await fetch(`${API_BASE}/api/payouts/status/${payoutId}`);
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

    // Poll for status updates every 10 seconds
    const interval = setInterval(fetchPayoutStatus, 10000);

    return () => clearInterval(interval);
  }, [payoutId, onStatusChange]);

  if (loading) {
    return <div className="text-center text-gray-600">Loading withdrawal status...</div>;
  }

  if (error) {
    return (
      <Alert className="bg-red-50 border-red-200">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-800">
          Error: {error}
        </AlertDescription>
      </Alert>
    );
  }

  if (!payout) {
    return <div className="text-gray-600">Payout not found</div>;
  }

  const config = statusConfig[payout.status] || statusConfig.pending;
  const StatusIcon = config.icon;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Withdrawal Status</CardTitle>
        <CardDescription>Payout ID: {payout._id}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Badge */}
        <div className="flex items-center gap-2">
          <StatusIcon className={`h-5 w-5 ${config.textColor}`} />
          <Badge className={`${config.color} ${config.textColor} border-none`}>
            {config.label}
          </Badge>
        </div>

        {/* Payout Details */}
        <div className="grid grid-cols-2 gap-4 border-t pt-4">
          <div>
            <p className="text-sm text-gray-600">Amount</p>
            <p className="text-lg font-semibold">
              {(payout.amount / 100).toFixed(2)} {payout.currency}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Player ID</p>
            <p className="text-lg font-semibold">{payout.player_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">PSP Reference</p>
            <p className="text-sm font-mono">{payout.psp_reference || 'Pending'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Created</p>
            <p className="text-sm">
              {new Date(payout.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Webhook Events */}
        {payout.webhook_events && payout.webhook_events.length > 0 && (
          <div className="border-t pt-4">
            <p className="text-sm font-semibold mb-2">Event History</p>
            <div className="space-y-2">
              {payout.webhook_events.map((event, index) => (
                <div key={index} className="text-xs bg-gray-50 p-2 rounded">
                  <p className="font-mono text-gray-700">{event.event_code}</p>
                  <p className="text-gray-600">
                    {new Date(event.timestamp).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
