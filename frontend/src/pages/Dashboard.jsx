import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ArrowUpRight, ArrowDownRight, Users, Activity, AlertTriangle, Wallet, Server, DollarSign, Trophy } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

const StatCard = ({ title, value, icon: Icon, trend, trendValue, color, subtext }) => (
  <Card className="border-l-4" style={{borderLeftColor: color}}>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      <Icon className="h-4 w-4 text-muted-foreground" />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      <div className="flex items-center text-xs mt-1">
        {trend && (
            <span className={`flex items-center ${trend === 'up' ? 'text-green-500' : 'text-red-500'} mr-2`}>
                {trend === 'up' ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
                {trendValue}%
            </span>
        )}
        <span className="text-muted-foreground">{subtext || "vs yesterday"}</span>
      </div>
    </CardContent>
  </Card>
);

const HealthBadge = ({ status }) => {
    const colors = { UP: 'bg-green-500', DOWN: 'bg-red-500', WARNING: 'bg-yellow-500', Unstable: 'bg-orange-500' };
    return <span className={`px-2 py-0.5 rounded text-[10px] font-bold text-white ${colors[status] || 'bg-gray-500'}`}>{status}</span>;
};

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get('/v1/dashboard/stats');
        setStats(res.data);
      } catch (err) {
        console.error("Failed to fetch stats", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="p-10 flex items-center justify-center h-screen"><Activity className="w-10 h-10 animate-spin text-primary" /></div>;
  if (!stats) return <div className="text-center p-10">Failed to load data.</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Executive Dashboard</h2>
        <div className="flex gap-2">
            <Badge variant="outline" className="text-green-500 border-green-500">Live</Badge>
            <span className="text-sm text-muted-foreground">{new Date().toLocaleString()}</span>
        </div>
      </div>
      
      {/* 1. GGR / NGR / BETS / WINS */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard 
          title="GGR (Gross Gaming Revenue)" 
          value={`$${stats.ggr.value.toLocaleString()}`} 
          icon={DollarSign} 
          trend={stats.ggr.trend}
          trendValue={stats.ggr.change_percent.toFixed(1)}
          color="#3b82f6"
        />
        <StatCard 
          title="NGR (Net Gaming Revenue)" 
          value={`$${stats.ngr.value.toLocaleString()}`} 
          icon={Wallet} 
          trend={stats.ngr.trend}
          trendValue={stats.ngr.change_percent.toFixed(1)}
          color="#10b981"
        />
        <StatCard 
          title="Total Bets (Volume)" 
          value={`$${stats.total_bets.value.toLocaleString()}`} 
          icon={Activity} 
          trend={stats.total_bets.trend}
          trendValue={stats.total_bets.change_percent.toFixed(1)}
          color="#8b5cf6"
        />
        <StatCard 
          title="Total Wins (Paid Out)" 
          value={`$${stats.total_wins.value.toLocaleString()}`} 
          icon={Trophy} 
          trend={stats.total_wins.trend}
          trendValue={stats.total_wins.change_percent.toFixed(1)}
          color="#f59e0b"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-12">
        {/* 2. Provider Health & Payment Status */}
        <Card className="col-span-12 md:col-span-4">
            <CardHeader><CardTitle className="flex items-center gap-2"><Server className="w-4 h-4" /> System Health</CardTitle></CardHeader>
            <CardContent className="space-y-6">
                <div>
                    <h4 className="text-xs font-semibold uppercase text-muted-foreground mb-3">Game Providers</h4>
                    <div className="space-y-2">
                        {stats.provider_health.map((p, i) => (
                            <div key={i} className="flex justify-between items-center text-sm border-b border-dashed pb-1 last:border-0">
                                <span>{p.name}</span>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-muted-foreground">{p.latency}</span>
                                    <HealthBadge status={p.status} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
                <div>
                    <h4 className="text-xs font-semibold uppercase text-muted-foreground mb-3">Payment Gateways</h4>
                    <div className="space-y-2">
                        {stats.payment_health.map((p, i) => (
                            <div key={i} className="flex justify-between items-center text-sm border-b border-dashed pb-1 last:border-0">
                                <span>{p.name}</span>
                                <HealthBadge status={p.status} />
                            </div>
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>

        {/* 3. Live Activity & Risk */}
        <Card className="col-span-12 md:col-span-4">
            <CardHeader><CardTitle className="flex items-center gap-2"><Users className="w-4 h-4" /> Live Operations</CardTitle></CardHeader>
            <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-secondary/30 rounded-lg">
                        <div className="text-2xl font-bold text-primary">{stats.online_users}</div>
                        <div className="text-xs text-muted-foreground">Online Users</div>
                    </div>
                    <div className="text-center p-4 bg-secondary/30 rounded-lg">
                        <div className="text-2xl font-bold text-primary">{stats.active_sessions}</div>
                        <div className="text-xs text-muted-foreground">Active Games</div>
                    </div>
                </div>
                
                <div>
                    <h4 className="text-xs font-semibold uppercase text-muted-foreground mb-3 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Risk Alerts</h4>
                    <div className="space-y-2">
                        {Object.entries(stats.risk_alerts).map(([key, val]) => (
                            <div key={key} className="flex justify-between items-center text-sm">
                                <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                                <Badge variant={val > 0 ? "destructive" : "outline"}>{val}</Badge>
                            </div>
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>

        {/* 4. Top Games */}
        <Card className="col-span-12 md:col-span-4">
            <CardHeader><CardTitle>Top Performing Games</CardTitle></CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="h-8">Game</TableHead>
                            <TableHead className="h-8 text-right">Revenue</TableHead>
                            <TableHead className="h-8 text-right">RTP</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {stats.top_games.map((g, i) => (
                            <TableRow key={i}>
                                <TableCell className="py-2">
                                    <div className="font-medium text-sm">{g.name}</div>
                                    <div className="text-xs text-muted-foreground">{g.provider}</div>
                                </TableCell>
                                <TableCell className="text-right py-2">${g.revenue.toLocaleString()}</TableCell>
                                <TableCell className="text-right py-2">
                                    <span className={g.rtp_today < 95 ? "text-red-500 font-bold" : "text-green-500"}>
                                        {g.rtp_today}%
                                    </span>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
         <Card className="col-span-4 md:col-span-1">
            <CardHeader><CardTitle className="text-sm">Bonus Performance</CardTitle></CardHeader>
            <CardContent>
                <div className="flex justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Given Today</span>
                    <span className="font-bold">{stats.bonuses_given_today_count}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Total Value</span>
                    <span className="font-bold text-yellow-500">${stats.bonuses_given_today_amount.toLocaleString()}</span>
                </div>
            </CardContent>
         </Card>
         <Card className="col-span-4 md:col-span-1">
            <CardHeader><CardTitle className="text-sm">Pending Actions</CardTitle></CardHeader>
            <CardContent>
                <div className="flex justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Withdrawals</span>
                    <Badge variant={stats.pending_withdrawals_count > 0 ? "destructive" : "secondary"}>{stats.pending_withdrawals_count}</Badge>
                </div>
                <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">KYC Review</span>
                    <Badge variant="outline">{stats.pending_kyc_count}</Badge>
                </div>
            </CardContent>
         </Card>
      </div>
    </div>
  );
};

export default Dashboard;
