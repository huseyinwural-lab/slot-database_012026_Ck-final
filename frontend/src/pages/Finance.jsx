import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { toast } from 'sonner';
import { 
  DollarSign, ArrowUpRight, ArrowDownRight, RefreshCw, Filter, 
  Download, Eye, MoreHorizontal, Globe, Smartphone, CreditCard
} from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

// Components
import DepositDetailModal from '../components/finance/DepositDetailModal';

const Finance = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    type: 'deposit',
    status: 'all',
    min_amount: '',
    max_amount: '',
    player_search: '',
    provider: 'all',
    country: 'all'
  });
  
  // Selected TX for Detail Modal
  const [selectedTx, setSelectedTx] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.type !== 'all') params.append('type', filters.type);
      if (filters.status !== 'all') params.append('status', filters.status);
      if (filters.min_amount) params.append('min_amount', filters.min_amount);
      if (filters.max_amount) params.append('max_amount', filters.max_amount);
      if (filters.player_search) params.append('player_search', filters.player_search);
      if (filters.provider !== 'all') params.append('provider', filters.provider);
      if (filters.country !== 'all') params.append('country', filters.country);

      const res = await api.get(`/v1/finance/transactions?${params.toString()}`);
      setTransactions(res.data);
    } catch (err) {
      toast.error('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [filters]);

  const handleViewDetails = (tx) => {
    setSelectedTx(tx);
    setIsDetailOpen(true);
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'completed': return 'default'; // black/white
      case 'pending': return 'secondary'; // gray
      case 'rejected': return 'destructive'; // red
      case 'fraud_flagged': return 'destructive'; 
      default: return 'outline';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <DollarSign className="w-8 h-8 text-green-600" /> Finance Management
          </h2>
          <p className="text-muted-foreground">Manage deposits, withdrawals, and approvals.</p>
        </div>
        <Button onClick={fetchData} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Main Filter Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Input 
                placeholder="Search Transaction ID or Player..." 
                value={filters.player_search}
                onChange={e => setFilters({...filters, player_search: e.target.value})}
              />
            </div>
            
            <Select value={filters.type} onValueChange={v => setFilters({...filters, type: v})}>
              <SelectTrigger className="w-[140px]"><SelectValue placeholder="Type" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="deposit">Deposits</SelectItem>
                <SelectItem value="withdrawal">Withdrawals</SelectItem>
                <SelectItem value="adjustment">Adjustments</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filters.status} onValueChange={v => setFilters({...filters, status: v})}>
              <SelectTrigger className="w-[140px]"><SelectValue placeholder="Status" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="fraud_flagged">Fraud</SelectItem>
              </SelectContent>
            </Select>

            {/* Advanced Filters */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="border-dashed">
                  <Filter className="w-4 h-4 mr-2" /> Advanced
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80 p-4 space-y-4">
                <div className="space-y-2">
                  <h4 className="font-medium leading-none">Filter Options</h4>
                  <p className="text-sm text-muted-foreground">Detailed filtering controls.</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label>Min Amount</Label>
                    <Input type="number" placeholder="0" value={filters.min_amount} onChange={e => setFilters({...filters, min_amount: e.target.value})} />
                  </div>
                  <div className="space-y-1">
                    <Label>Max Amount</Label>
                    <Input type="number" placeholder="∞" value={filters.max_amount} onChange={e => setFilters({...filters, max_amount: e.target.value})} />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label>Provider</Label>
                  <Select value={filters.provider} onValueChange={v => setFilters({...filters, provider: v})}>
                    <SelectTrigger><SelectValue placeholder="Select Provider" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Providers</SelectItem>
                      <SelectItem value="Stripe">Stripe</SelectItem>
                      <SelectItem value="CoinPayments">CoinPayments</SelectItem>
                      <SelectItem value="Papara">Papara</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label>Country</Label>
                  <Input placeholder="ISO Code (e.g. TR)" value={filters.country === 'all' ? '' : filters.country} onChange={e => setFilters({...filters, country: e.target.value})} />
                </div>
                <Button className="w-full" onClick={fetchData}>Apply Filters</Button>
              </PopoverContent>
            </Popover>

            <Button variant="outline"><Download className="w-4 h-4 mr-2" /> Export</Button>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="transactions" className="w-full">
        <TabsList>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="reports">Daily Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="transactions">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Transaction History</CardTitle>
              <CardDescription>All financial movements.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tx ID</TableHead>
                    <TableHead>Player</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Method/Provider</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Fee/Net</TableHead>
                    <TableHead>Info</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow><TableCell colSpan={10} className="text-center h-24">Loading...</TableCell></TableRow>
                  ) : transactions.length === 0 ? (
                    <TableRow><TableCell colSpan={10} className="text-center h-24 text-muted-foreground">No transactions found</TableCell></TableRow>
                  ) : (
                    transactions.map((tx) => (
                      <TableRow key={tx.id}>
                        <TableCell className="font-mono text-xs">{tx.id}</TableCell>
                        <TableCell className="font-medium text-blue-600 cursor-pointer">{tx.player_username}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={tx.type === 'deposit' ? 'text-green-600 border-green-200' : 'text-red-600 border-red-200'}>
                            {tx.type.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-medium text-sm">{tx.method}</span>
                            <span className="text-xs text-muted-foreground">{tx.provider}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-bold">
                          ${tx.amount.toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right text-xs">
                          {tx.fee > 0 ? (
                            <>
                              <div className="text-red-500">-${tx.fee}</div>
                              <div className="font-bold text-green-600">${tx.net_amount.toLocaleString()}</div>
                            </>
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            {tx.country && <Badge variant="secondary" className="text-[10px] px-1 h-5"><Globe className="w-3 h-3 mr-1" />{tx.country}</Badge>}
                            {tx.device_info && <Badge variant="secondary" className="text-[10px] px-1 h-5"><Smartphone className="w-3 h-3" /></Badge>}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusColor(tx.status)}>{tx.status}</Badge>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {new Date(tx.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" variant="ghost" onClick={() => handleViewDetails(tx)}>
                            <Eye className="w-4 h-4 text-blue-600" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports">
          <div className="p-10 text-center text-muted-foreground">Reports Module Placeholder</div>
        </TabsContent>
      </Tabs>

      {/* Detailed Modal */}
      <DepositDetailModal 
        transaction={selectedTx} 
        open={isDetailOpen} 
        onOpenChange={setIsDetailOpen}
        onRefresh={fetchData}
      />
    </div>
  );
};

export default Finance;
