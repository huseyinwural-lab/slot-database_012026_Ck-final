import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Wallet, Gift, Trophy, ArrowRightLeft } from 'lucide-react';

const FinancialSummary = ({ data, onNavigate, bonusesEnabled = true, jackpotsEnabled = true }) => {
  const itemClass = (enabled) =>
    `space-y-1 transition-all ${enabled ? 'cursor-pointer hover:opacity-90' : 'opacity-50 cursor-not-allowed'}`;

  const clickable = (enabled, key, label) => ({
    className: itemClass(enabled),
    role: enabled ? 'button' : undefined,
    tabIndex: enabled ? 0 : -1,
    onClick: enabled ? () => onNavigate?.({ key }) : undefined,
    onKeyDown: enabled
      ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') onNavigate?.({ key });
        }
      : undefined,
    title: enabled ? 'View details' : (label || 'Coming soon'),
  });

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle className="text-sm font-medium">🧮 Financial Summary (Live)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-muted-foreground text-xs">
              <Wallet className="h-3 w-3" /> Cash in System
            </div>
            <div className="text-xl font-bold">${data.cash_in_system.toLocaleString()}</div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-muted-foreground text-xs">
              <Gift className="h-3 w-3" /> Bonus Liabilities
            </div>
            <div className="text-xl font-bold text-orange-600">${data.bonus_liabilities.toLocaleString()}</div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-muted-foreground text-xs">
              <Trophy className="h-3 w-3" /> Jackpot Pools
            </div>
            <div className="text-xl font-bold text-purple-600">${data.jackpot_pools.toLocaleString()}</div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-muted-foreground text-xs">
              <ArrowRightLeft className="h-3 w-3" /> Pending Withdrawals
            </div>
            <div className="text-xl font-bold text-blue-600">${data.pending_withdrawals.toLocaleString()}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default FinancialSummary;
