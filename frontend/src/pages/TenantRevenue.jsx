import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TrendingUp, DollarSign, Activity, BarChart3 } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

const TenantRevenue = () => {
  const [loading, setLoading] = useState(true);
  const [revenueData, setRevenueData] = useState(null);
  const [dateRange, setDateRange] = useState('7'); // days

  useEffect(() => {
    const fetchRevenue = async () => {
      setLoading(true);
      try {
        const fromDate = new Date();
        fromDate.setDate(fromDate.getDate() - parseInt(dateRange));
        
        const params = {
          from_date: fromDate.toISOString(),
          to_date: new Date().toISOString()
        };
        
        const response = await api.get('/v1/revenue/my-tenant', { params });
        setRevenueData(response.data);
      } catch (error) {
        console.error('Failed to fetch revenue:', error);
        toast.error('Failed to load revenue data');
      } finally {
        setLoading(false);
      }
    };

    fetchRevenue();
  }, [dateRange]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const ggr = revenueData?.ggr || 0;
  const totalBets = revenueData?.total_bets || 0;
  const totalWins = revenueData?.total_wins || 0;
  const rtp = totalBets > 0 ? ((totalWins / totalBets) * 100).toFixed(2) : 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">My Revenue</h1>
          <p className="text-muted-foreground">Your tenant&apos;s financial performance</p>
        </div>
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
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GGR</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              ${ggr.toLocaleString()}
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
              All player bets
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
            <CardTitle className="text-sm font-medium">RTP</CardTitle>
            <BarChart3 className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${rtp > 100 ? 'text-red-600' : 'text-green-600'}`}>
              {rtp}%
            </div>
            <p className="text-xs text-muted-foreground">
              Return to Player
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Details Card */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 border rounded-lg">
              <div className="text-sm text-muted-foreground mb-1">Period</div>
              <div className="font-medium">
                {new Date(revenueData?.period_start).toLocaleDateString()} - {new Date(revenueData?.period_end).toLocaleDateString()}
              </div>
            </div>
            
            <div className="p-4 border rounded-lg">
              <div className="text-sm text-muted-foreground mb-1">Transactions</div>
              <div className="font-medium">{revenueData?.transaction_count || 0}</div>
            </div>
            
            <div className="p-4 border rounded-lg">
              <div className="text-sm text-muted-foreground mb-1">Avg Bet Size</div>
              <div className="font-medium">
                ${revenueData?.transaction_count > 0 
                  ? (totalBets / revenueData.transaction_count).toFixed(2) 
                  : 0}
              </div>
            </div>
            
            <div className="p-4 border rounded-lg">
              <div className="text-sm text-muted-foreground mb-1">Avg Win Size</div>
              <div className="font-medium">
                ${revenueData?.transaction_count > 0 
                  ? (totalWins / revenueData.transaction_count).toFixed(2) 
                  : 0}
              </div>
            </div>
          </div>

          {/* Performance Indicator */}
          <div className="p-4 bg-secondary rounded-lg">
            <h3 className="font-semibold mb-2">Performance Summary</h3>
            <p className="text-sm text-muted-foreground">
              {ggr > 0 
                ? `Your tenant generated $${ggr.toLocaleString()} in GGR over the last ${dateRange} days. RTP is ${rtp}%.`
                : 'No revenue data available for the selected period.'}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TenantRevenue;
