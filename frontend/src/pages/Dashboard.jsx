import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpRight, ArrowDownRight, Users, Activity } from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, trend, trendValue, color }) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <Icon className={`h-4 w-4 text-${color}-500`} />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      <p className="text-xs text-muted-foreground">
        {trend === 'up' ? <ArrowUpRight className="inline h-3 w-3 text-green-500 mr-1" /> : <ArrowDownRight className="inline h-3 w-3 text-red-500 mr-1" />}
        <span className={trend === 'up' ? 'text-green-500' : 'text-red-500'}>{trendValue}</span> from yesterday
      </p>
    </CardContent>
  </Card>
);

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

  if (loading) return <div className="text-center p-10">Loading Dashboard...</div>;
  if (!stats) return <div className="text-center p-10">Failed to load data.</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Overview</h2>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard 
          title="Total Revenue" 
          value={`$${stats.net_revenue_today.toLocaleString()}`} 
          icon={Activity} 
          trend="up" 
          trendValue="+20.1%" 
          color="blue"
        />
        <StatCard 
          title="Deposits" 
          value={`$${stats.total_deposit_today.toLocaleString()}`} 
          icon={ArrowUpRight} 
          trend="up" 
          trendValue="+12%" 
          color="green"
        />
        <StatCard 
          title="Withdrawals" 
          value={`$${stats.total_withdrawal_today.toLocaleString()}`} 
          icon={ArrowDownRight} 
          trend="down" 
          trendValue="+4%" 
          color="red"
        />
        <StatCard 
          title="Active Players" 
          value={stats.active_players_now} 
          icon={Users} 
          trend="up" 
          trendValue="+201" 
          color="yellow"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Registrations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.recent_registrations.map(player => (
                <div key={player.id} className="flex items-center justify-between border-b border-border pb-2 last:border-0">
                  <div className="flex items-center gap-4">
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-xs font-bold">
                      {player.username.substring(0,2).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium leading-none">{player.username}</p>
                      <p className="text-xs text-muted-foreground">{player.email}</p>
                    </div>
                  </div>
                  <div className="text-sm text-right">
                    <p>{player.country}</p>
                    <p className="text-xs text-muted-foreground">{new Date(player.registered_at).toLocaleDateString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
            <CardHeader>
                <CardTitle>Pending Actions</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-secondary/50 rounded-lg">
                        <span className="text-sm font-medium">Pending Withdrawals</span>
                        <span className="bg-yellow-500/20 text-yellow-500 px-2 py-1 rounded text-xs font-bold">{stats.pending_withdrawals_count}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-secondary/50 rounded-lg">
                        <span className="text-sm font-medium">Pending KYC</span>
                        <span className="bg-blue-500/20 text-blue-500 px-2 py-1 rounded text-xs font-bold">{stats.pending_kyc_count}</span>
                    </div>
                </div>
            </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
