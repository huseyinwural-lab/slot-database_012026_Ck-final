import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TrendingUp, DollarSign, Users, Activity } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

const OwnerRevenue = () => {
  const [loading, setLoading] = useState(true);
  const [revenueData, setRevenueData] = useState(null);
  const [selectedTenant, setSelectedTenant] = useState('all');
  const [dateRange, setDateRange] = useState('7'); // days

  useEffect(() => {
    fetchRevenue();
  }, [selectedTenant, dateRange]);

  const fetchRevenue = async () => {
    setLoading(true);
    try {
      const fromDate = new Date();
      fromDate.setDate(fromDate.getDate() - parseInt(dateRange));
      
      const params = {
        from_date: fromDate.toISOString(),
        to_date: new Date().toISOString()
      };
      
      if (selectedTenant !== 'all') {
        params.tenant_id = selectedTenant;
      }
      
      const response = await api.get('/v1/reports/revenue/all-tenants', { params });
      setRevenueData(response.data);
    } catch (error) {
      console.error('Failed to fetch revenue:', error);
      toast.error('Failed to load revenue data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const totalGGR = revenueData?.total_ggr || 0;
  const totalBets = revenueData?.tenants?.reduce((sum, t) => sum + t.total_bets, 0) || 0;
  const totalWins = revenueData?.tenants?.reduce((sum, t) => sum + t.total_wins, 0) || 0;
  const avgGGRPerTenant = revenueData?.tenants?.length > 0 ? totalGGR / revenueData.tenants.length : 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">All Tenants Revenue</h1>
          <p className="text-muted-foreground">Platform-wide revenue analytics</p>
        </div>
        <div className="flex gap-4">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Last 24 Hours</SelectItem>
              <SelectItem value="7">Last 7 Days</SelectItem>
              <SelectItem value="30">Last 30 Days</SelectItem>
              <SelectItem value="90">Last 90 Days</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={selectedTenant} onValueChange={setSelectedTenant}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="All Tenants" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Tenants</SelectItem>
              {revenueData?.tenants?.map((t) => (
                <SelectItem key={t.tenant_id} value={t.tenant_id}>
                  {t.tenant_name || t.tenant_id}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total GGR</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              ${totalGGR.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              Gross Gaming Revenue
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Bets</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalBets.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              All tenant bets
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Wins</CardTitle>
            <Activity className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalWins.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Player winnings
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg GGR/Tenant</CardTitle>
            <Users className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${avgGGRPerTenant.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {revenueData?.tenants?.length || 0} active tenants
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tenant Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue by Tenant</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-semibold">Tenant</th>
                  <th className="text-right p-3 font-semibold">Total Bets</th>
                  <th className="text-right p-3 font-semibold">Total Wins</th>
                  <th className="text-right p-3 font-semibold">GGR</th>
                  <th className="text-right p-3 font-semibold">Transactions</th>
                  <th className="text-right p-3 font-semibold">RTP %</th>
                </tr>
              </thead>
              <tbody>
                {revenueData?.tenants?.map((tenant) => {
                  const rtp = tenant.total_bets > 0 
                    ? ((tenant.total_wins / tenant.total_bets) * 100).toFixed(2) 
                    : 0;
                  
                  return (
                    <tr key={tenant.tenant_id} className="border-b hover:bg-secondary/50">
                      <td className="p-3">
                        <div>
                          <div className="font-medium">{tenant.tenant_name || 'Unknown'}</div>
                          <div className="text-xs text-muted-foreground">{tenant.tenant_id}</div>
                        </div>
                      </td>
                      <td className="text-right p-3">${tenant.total_bets.toLocaleString()}</td>
                      <td className="text-right p-3">${tenant.total_wins.toLocaleString()}</td>
                      <td className="text-right p-3">
                        <span className="font-semibold text-green-600">
                          ${tenant.ggr.toLocaleString()}
                        </span>
                      </td>
                      <td className="text-right p-3">{tenant.transaction_count}</td>
                      <td className="text-right p-3">
                        <span className={rtp > 100 ? 'text-red-600' : 'text-green-600'}>
                          {rtp}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OwnerRevenue;
