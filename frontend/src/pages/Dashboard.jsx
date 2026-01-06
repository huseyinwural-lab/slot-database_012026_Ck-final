import React, { useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpRight, ArrowDownRight, Users, Activity, Wallet, Server, DollarSign, Trophy, Filter, Info } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useNavigate } from 'react-router-dom';
import { useCapabilities } from '../context/CapabilitiesContext';


// Import New Components
import FinancialTrendChart from '../components/dashboard/FinancialTrendChart';
import RetentionCard from '../components/dashboard/RetentionCard';
import FTDCard from '../components/dashboard/FTDCard';
import CriticalAlertsPanel from '../components/dashboard/CriticalAlertsPanel';
import FinancialSummary from '../components/dashboard/FinancialSummary';
import LossLeadersTable from '../components/dashboard/LossLeadersTable';
import LiveBetsTicker from '../components/dashboard/LiveBetsTicker';
import BonusPerformanceCard from '../components/dashboard/BonusPerformanceCard';

const ComingSoonCard = ({ children, enabled, tooltip }) => {
  if (enabled) return children;
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="opacity-50 cursor-not-allowed">{children}</div>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltip || 'Coming soon'}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};


const StatCard = ({
  title,
  value,
  icon: Icon,
  trend,
  trendValue,
  color,
  subtext,
  onClick,
  disabled,
  tooltip,
}) => {
  const card = (
    <Card
      className={`border-l-4 shadow-sm transition-all ${
        disabled
          ? 'opacity-50 cursor-not-allowed'
          : 'cursor-pointer hover:shadow-md hover:border-primary/40'
      }`}
      style={{ borderLeftColor: color }}
      role={disabled ? undefined : 'button'}
      tabIndex={disabled ? -1 : 0}
      onClick={disabled ? undefined : onClick}
      onKeyDown={
        disabled
          ? undefined
          : (e) => {
              if (e.key === 'Enter' || e.key === ' ') onClick?.();
            }
      }
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className="flex items-center text-xs mt-1">
          {trend && (
            <span
              className={`flex items-center ${
                trend === 'up' ? 'text-green-500' : 'text-red-500'
              } mr-2`}
            >
              {trend === 'up' ? (
                <ArrowUpRight className="h-3 w-3 mr-1" />
              ) : (
                <ArrowDownRight className="h-3 w-3 mr-1" />
              )}
              {trendValue}%
            </span>
          )}
          <span className="text-muted-foreground">{subtext || 'vs yesterday'}</span>
        </div>
      </CardContent>
    </Card>
  );

  if (!tooltip) return card;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{card}</TooltipTrigger>
        <TooltipContent>
          <p>{tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

const HealthBadge = ({ status }) => {
    const colors = { UP: 'bg-green-500', DOWN: 'bg-red-500', WARNING: 'bg-yellow-500', Unstable: 'bg-orange-500' };
    return <span className={`px-2 py-0.5 rounded text-[10px] font-bold text-white ${colors[status] || 'bg-gray-500'}`}>{status}</span>;
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { isOwner, hasFeature } = useCapabilities();

  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');

  const rangeDays = useMemo(() => {
    if (timeRange === '7d') return 7;
    if (timeRange === '30d') return 30;
    if (timeRange === 'today') return 1;
    if (timeRange === 'yesterday') return 1;
    return 30;
  }, [timeRange]);

  const go = (path) => navigate(path);

  const ownerRevenueDisabled = !isOwner;

  const jackpotRouteExists = false; // P1 scope: do not add placeholder routes
  const liveBetsRouteExists = false; // P1 scope: do not add placeholder routes
  const bonusesRouteEnabled = hasFeature?.('can_manage_bonus') === true;


  const fetchStats = async () => {
    try {
      const res = await api.get('/v1/dashboard/comprehensive-stats');
      setStats(res.data);
    } catch (err) {
      console.error("Failed to fetch stats", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Simulate real-time update
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [timeRange]);

  if (loading) return <div className="p-10 flex items-center justify-center h-screen"><Activity className="w-10 h-10 animate-spin text-primary" /></div>;
  if (!stats) return <div className="text-center p-10">Failed to load data.</div>;

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Executive Dashboard</h2>
          <p className="text-muted-foreground text-sm">Real-time operational insights</p>
        </div>
        
        <div className="flex items-center gap-3">
            <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Time Range" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="today">Today</SelectItem>
                    <SelectItem value="yesterday">Yesterday</SelectItem>
                    <SelectItem value="7d">Last 7 Days</SelectItem>
                    <SelectItem value="30d">Last 30 Days</SelectItem>
                </SelectContent>
            </Select>
            <div className="flex gap-2 items-center bg-secondary/50 px-3 py-1 rounded-md border">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                <span className="text-xs font-medium">Live</span>
            </div>
        </div>
      </div>
      
      {/* 1. KPI Cards Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard 
          title="GGR (Gross Revenue)" 
          value={`$154,200`} 
          icon={DollarSign} 
          trend="up" trendValue="12.5" color="#3b82f6"
          disabled={ownerRevenueDisabled}
          tooltip={ownerRevenueDisabled ? 'Owner only' : 'View details'}
          onClick={() => go(`/revenue/all-tenants?metric=ggr&range_days=${rangeDays}`)}
        />
        <StatCard 
          title="NGR (Net Revenue)" 
          value={`$128,500`} 
          icon={Wallet} 
          trend="up" trendValue="10.2" color="#10b981"
          disabled={ownerRevenueDisabled}
          tooltip={ownerRevenueDisabled ? 'Owner only' : 'View details'}
          onClick={() => go(`/revenue/all-tenants?metric=ngr&range_days=${rangeDays}`)}
        />
        <StatCard 
          title="Active Players" 
          value={stats.online_users} 
          icon={Users} 
          trend="up" trendValue="5.4" color="#8b5cf6"
          subtext="online now"
          tooltip="View details"
          onClick={() => go('/players?status=active')}
        />
        <StatCard 
          title="Total Bets" 
          value="45,230" 
          icon={Activity} 
          trend="down" trendValue="2.1" color="#f59e0b"
          tooltip="View details"
          onClick={() => go(`/finance?tab=transactions&type=bet&range_days=${rangeDays}`)}
        />
      </div>

      {/* 2. Critical Alerts & Financial Summary Row */}
      <div className="grid gap-4 md:grid-cols-12">
        <div className="col-span-12 md:col-span-4">
            <CriticalAlertsPanel alerts={stats.critical_alerts} />
        </div>
        <div className="col-span-12 md:col-span-8">
            <FinancialSummary
              data={stats.financial_summary}
              onNavigate={({ key }) => {
                if (key === 'cash_in_system') go('/finance?tab=transactions');
                if (key === 'bonus_liabilities') {
                  if (bonusesRouteEnabled) go('/bonuses?view=liabilities');
                }
                if (key === 'pending_withdrawals') go('/finance/withdrawals?status=pending');
                if (key === 'jackpot_pools') {
                  // Route not available in P1 scope
                }
              }}
              bonusesEnabled={bonusesRouteEnabled}
              jackpotsEnabled={jackpotRouteExists}
            />
        </div>
      </div>

      {/* 3. Main Chart & Live Ticker */}
      <div className="grid gap-4 md:grid-cols-12">
        <div className="col-span-12 md:col-span-8">
            <FinancialTrendChart data={stats.financial_trend} />
        </div>
        <div className="col-span-12 md:col-span-4">
            <LiveBetsTicker bets={stats.live_bets} />
        </div>
      </div>

      {/* 4. Advanced Metrics Row (Retention, FTD, Bonus) */}
      <div className="grid gap-4 md:grid-cols-3">
        <ComingSoonCard enabled={false} tooltip="Coming soon">
          <RetentionCard data={stats.retention_metrics} />
        </ComingSoonCard>

        <StatCard
          title="💼 First Time Deposits (FTD)"
          value={stats?.ftd_metrics?.ftd_month?.toLocaleString?.() ?? '-'}
          icon={Activity}
          trend={null}
          trendValue={null}
          color="#22c55e"
          tooltip="View details"
          onClick={() => go(`/finance?tab=transactions&type=deposit&ftd=1&range_days=${rangeDays}`)}
        />

        <ComingSoonCard enabled={bonusesRouteEnabled} tooltip={bonusesRouteEnabled ? 'View details' : 'Coming soon'}>
          <BonusPerformanceCard data={stats.bonus_performance} />
        </ComingSoonCard>
      </div>

      {/* 5. Loss Leaders & System Health */}
      <div className="grid gap-4 md:grid-cols-12">
        <div className="col-span-12 md:col-span-8">
            <LossLeadersTable data={stats.negative_performing_games} />
        </div>
        <div className="col-span-12 md:col-span-4 space-y-4">
            {/* Provider Health */}
            <Card>
                <CardHeader className="py-3">
                    <CardTitle className="text-sm font-medium flex items-center justify-between">
                        <span>Provider Health</span>
                    </CardTitle>
                </CardHeader>
                <CardContent className="py-2">
                    <div className="space-y-3">
                        {stats.provider_health.map((p, i) => (
                            <div key={i} className="flex justify-between items-center text-sm border-b border-dashed pb-2 last:border-0 last:pb-0">
                                <div>
                                    <div className="font-medium">{p.name}</div>
                                    <div className="text-xs text-muted-foreground">{p.latency} • {p.last_error}</div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <HealthBadge status={p.status} />
                                    <Button variant="ghost" size="icon" className="h-6 w-6"><Info className="h-3 w-3" /></Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Payment Health */}
            <Card>
                <CardHeader className="py-3">
                    <CardTitle className="text-sm font-medium flex items-center justify-between">
                        <span>Payment Gateway Status</span>
                    </CardTitle>
                </CardHeader>
                <CardContent className="py-2">
                    <div className="space-y-3">
                        {stats.payment_health.map((p, i) => (
                            <div key={i} className="flex justify-between items-center text-sm border-b border-dashed pb-2 last:border-0 last:pb-0">
                                <div>
                                    <div className="font-medium">{p.name}</div>
                                    <div className="text-xs text-muted-foreground">{p.latency} • {p.last_error}</div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <HealthBadge status={p.status} />
                                    <Button variant="ghost" size="icon" className="h-6 w-6"><Info className="h-3 w-3" /></Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
