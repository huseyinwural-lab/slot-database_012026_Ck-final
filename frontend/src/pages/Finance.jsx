import React, { useEffect, useMemo, useState } from 'react';
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
import { Checkbox } from '@/components/ui/checkbox';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuCheckboxItem } from '@/components/ui/dropdown-menu';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import { 
  DollarSign, ArrowUpRight, ArrowDownRight, RefreshCw, Filter, 
  Download, Eye, Globe, Smartphone, CreditCard, AlertTriangle, 
  CheckCircle, XCircle, ShieldAlert, Calendar, FileText, MoreHorizontal,
  Edit, Upload, MessageSquare, ExternalLink, Settings2
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Components
import TransactionDetailModal from '../components/finance/TransactionDetailModal';

import ReconciliationPanel from '../components/finance/ReconciliationPanel';
import ChargebackList from '../components/finance/ChargebackList';

const parseCsvList = (v) =>
  String(v || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

const Finance = () => {
  const [transactions, setTransactions] = useState([]);
  const [txMeta, setTxMeta] = useState({ page: 1, page_size: 50, total: null });
  const [pageSize, setPageSize] = useState(50);
const formatAmount = (amount, currency) => {
  if (amount == null) return '-';
  try {
    const value = Number(amount);
    const formatted = value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    return `${formatted} ${currency || ''}`.trim();
  const [activeTab, setActiveTab] = useState('transactions');

  } catch {
    return `${amount} ${currency || ''}`.trim();
  }
};

  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState(null);
  
  const [filters, setFilters] = useState({
    type: 'all',
    status: 'all',
    min_amount: '',
    max_amount: '',
    player_search: '',
    provider: 'all',
    country: 'all',
    start_date: '',
    end_date: '',
    currency: 'all',
    ip_address: '',
    range_days: ''

  // P1 Deep-link: /finance?tab=transactions&type=bet,deposit&range_days=30
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get('tab');
      const typeParam = params.get('type');
      const rangeDays = params.get('range_days');

      if (tab && ['transactions', 'reports', 'reconciliation', 'chargebacks'].includes(tab)) {
        setActiveTab(tab);
      }

      setFilters((prev) => {
        const next = { ...prev };
        if (typeParam) next.type = typeParam; // supports CSV list like bet,withdrawal
        if (rangeDays) next.range_days = rangeDays;
        return next;
      });
    } catch {
      // ignore
    }
  }, []);

  });

  // Column Visibility State
  const [visibleColumns, setVisibleColumns] = useState({
    id: true,
    player: true,
    type: true,
    amount: true,
    status: true,
    date: true,
    actions: true,
    // Optional
    provider_id: false,
    wallet: false,
    net_amount: false,
    fee: false,
    ip: false,
    device: false,
    risk: true
  });
  
  // Selected TX for Detail Modal
  const [selectedTx, setSelectedTx] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedRows, setSelectedRows] = useState([]);

  const fetchData = async (page = 1, pageSizeOverride) => {
    const safePage = Number(page) || 1;

    setLoading(true);
    try {
      const params = new URLSearchParams();

      // type can be CSV list in deep-links: bet,deposit,withdrawal
      const normalizedFilters = { ...filters };
      if (normalizedFilters.type && normalizedFilters.type.includes(',')) {
        normalizedFilters.type = parseCsvList(normalizedFilters.type);
      }

      Object.keys(normalizedFilters).forEach((key) => {
        const value = normalizedFilters[key];
        if (!value) return;
        if (value === 'all') return;

        if (Array.isArray(value)) {
          value.forEach((v) => params.append(key, v));
        } else {
          params.append(key, value);
        }
      });

      const effectivePageSize = pageSizeOverride || pageSize;
      params.append('page', String(safePage));
      params.append('page_size', String(effectivePageSize));

      const res = await api.get(`/v1/finance/transactions?${params.toString()}`);

      const items = Array.isArray(res.data)
        ? res.data
        : res.data.items ?? res.data.rows ?? [];

      setTransactions(Array.isArray(items) ? items : []);
      setTxMeta(res.data.meta || { page: safePage, page_size: effectivePageSize, total: null });
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      const errorCode =
        err?.response?.data?.error_code ||
        err?.response?.data?.detail?.error_code ||
        err?.code;

      const detailText =
        typeof detail === 'string' ? detail : (detail?.error_code || detail?.message);

      toast.error(
        `Failed to load transactions${status ? ` (${status})` : ''}${errorCode ? ` · ${errorCode}` : ''}`,
        {
          description: detailText || err?.message || 'Unknown error',
        }
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchReports = async () => {
    try {
      const res = await api.get('/v1/finance/reports');
      setReportData(res.data);
    } catch (err) {
      toast.error('Failed to load reports');
    }
  };

  useEffect(() => { fetchData(1); }, [filters]);

  const handleViewDetails = (tx) => {
    setSelectedTx(tx);
    setIsDetailOpen(true);
  };

  const toggleRow = (id) => {
    if (selectedRows.includes(id)) {
      setSelectedRows(selectedRows.filter(r => r !== id));
    } else {
      setSelectedRows([...selectedRows, id]);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      completed: "bg-green-100 text-green-800 border-green-200",
      paid: "bg-green-100 text-green-800 border-green-200",
      pending: "bg-yellow-100 text-yellow-800 border-yellow-200",
      requested: "bg-blue-100 text-blue-800 border-blue-200",
      under_review: "bg-orange-100 text-orange-800 border-orange-200",
      rejected: "bg-red-100 text-red-800 border-red-200",
      failed: "bg-red-100 text-red-800 border-red-200",
      fraud_flagged: "bg-purple-100 text-purple-800 border-purple-200",
      processing: "bg-indigo-100 text-indigo-800 border-indigo-200",
    };
    return (
      <Badge className={`${styles[status] || "bg-gray-100 text-gray-800"} border shadow-none capitalize whitespace-nowrap`}>
        {status?.replace('_', ' ')}
      </Badge>
    );
  };

  const getRiskBadge = (score) => {
    const styles = {
      low: "text-green-600 bg-green-50",
      medium: "text-yellow-600 bg-yellow-50",
      high: "text-red-600 bg-red-50",
      critical: "text-purple-600 bg-purple-50",
    };
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${styles[score] || "text-gray-500"}`}>
        {score}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <DollarSign className="w-8 h-8 text-green-600" /> Finance Hub
          </h2>
          <p className="text-muted-foreground">Comprehensive financial monitoring and operations center.</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => fetchData(txMeta?.page ?? 1)} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={() => {
              const params = new URLSearchParams();
              Object.keys(filters).forEach((key) => {
                if (filters[key] && filters[key] !== 'all') params.append(key, filters[key]);
              });
              api
                .get('/v1/finance/transactions/export', {
                  params: Object.fromEntries(params.entries()),
                  responseType: 'blob',
                })
                .then((res) => {
                  const url = window.URL.createObjectURL(new Blob([res.data]));
                  const link = document.createElement('a');
                  link.href = url;
                  link.setAttribute('download', `finance_transactions_${new Date().toISOString()}.csv`);
                  document.body.appendChild(link);
                  link.click();
                  link.remove();
                })
                .catch(() => {
                  toast.error('Export failed');
                });
            }}
          >
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
        </div>
      </div>

      <Tabs
        value={activeTab}
        className="w-full"
        onValueChange={(v) => {
          setActiveTab(v);
          if (v === 'reports') fetchReports();
        }}
      >
        <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="reconciliation">Reconciliation</TabsTrigger>
          <TabsTrigger value="chargebacks">Chargebacks</TabsTrigger>
        </TabsList>
        <TabsContent value="transactions" className="space-y-4">
          {/* Main Filter Bar */}
          <Card>
            <CardContent className="p-4 space-y-4">
              <div className="flex flex-wrap gap-4 items-center">
                <div className="relative flex-1 min-w-[200px]">
                  <Input 
                    placeholder="Search Transaction ID, Player, or Provider Ref..." 
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
                    <SelectItem value="bonus_issued">Bonus Issued</SelectItem>
                    <SelectItem value="jackpot_win">Jackpot Win</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={filters.status} onValueChange={v => setFilters({...filters, status: v})}>
                  <SelectTrigger className="w-[160px]"><SelectValue placeholder="Status" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="requested">Requested</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="under_review">Under Review</SelectItem>
                    <SelectItem value="approved">Approved</SelectItem>
                    <SelectItem value="processing">Processing</SelectItem>
                    <SelectItem value="completed">Completed / Paid</SelectItem>
                    <SelectItem value="rejected">Rejected</SelectItem>
                    <SelectItem value="fraud_flagged">Fraud Flagged</SelectItem>
                  </SelectContent>
                </Select>
                
                <div className="flex items-center gap-2">
                  <Input 
                    type="date" 
                    className="w-[140px]" 
                    value={filters.start_date} 
                    onChange={e => setFilters({...filters, start_date: e.target.value})}
                  />
                  <span className="text-muted-foreground">-</span>
                  <Input 
                    type="date" 
                    className="w-[140px]" 
                    value={filters.end_date} 
                    onChange={e => setFilters({...filters, end_date: e.target.value})}
                  />
                </div>

                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="border-dashed">
                      <Filter className="w-4 h-4 mr-2" /> More Filters
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-80 p-4 space-y-4">
                    <div className="space-y-2">
                      <h4 className="font-medium leading-none">Advanced Filters</h4>
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
                          <SelectItem value="InternalBank">Bank Transfer</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1">
                      <Label>Currency</Label>
                      <Select value={filters.currency} onValueChange={v => setFilters({...filters, currency: v})}>
                        <SelectTrigger><SelectValue placeholder="Select Currency" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All</SelectItem>
                          <SelectItem value="USD">USD</SelectItem>
                          <SelectItem value="EUR">EUR</SelectItem>
                          <SelectItem value="TRY">TRY</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                     <div className="space-y-1">
                      <Label>IP Address</Label>
                      <Input placeholder="192.168.x.x" value={filters.ip_address} onChange={e => setFilters({...filters, ip_address: e.target.value})} />
                    </div>
                    <div className="space-y-1">
                      <Label>Country</Label>
                      <Input placeholder="ISO Code (e.g. TR)" value={filters.country === 'all' ? '' : filters.country} onChange={e => setFilters({...filters, country: e.target.value})} />
                    </div>
                    <Button className="w-full" onClick={fetchData}>Apply Filters</Button>
                  </PopoverContent>
                </Popover>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <div>
                <CardTitle>Transaction History</CardTitle>
                <CardDescription>Live feed of financial movements.</CardDescription>
              </div>
              <div className="flex gap-2">
                {selectedRows.length > 0 && (
                  <>
                    <Button variant="outline" size="sm" className="text-green-600 bg-green-50 border-green-200">Approve ({selectedRows.length})</Button>
                    <Button variant="outline" size="sm" className="text-red-600 bg-red-50 border-red-200">Reject ({selectedRows.length})</Button>
                  </>
                )}
                
                {/* Column Toggle */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm"><Settings2 className="w-4 h-4 mr-2"/> Columns</Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                        <DropdownMenuLabel>Toggle Columns</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuCheckboxItem checked={visibleColumns.provider_id} onCheckedChange={(c) => setVisibleColumns({...visibleColumns, provider_id: c})}>Provider Tx ID</DropdownMenuCheckboxItem>
                        <DropdownMenuCheckboxItem checked={visibleColumns.wallet} onCheckedChange={(c) => setVisibleColumns({...visibleColumns, wallet: c})}>Wallet Before/After</DropdownMenuCheckboxItem>
                        <DropdownMenuCheckboxItem checked={visibleColumns.net_amount} onCheckedChange={(c) => setVisibleColumns({...visibleColumns, net_amount: c})}>Net Amount</DropdownMenuCheckboxItem>
                        <DropdownMenuCheckboxItem checked={visibleColumns.fee} onCheckedChange={(c) => setVisibleColumns({...visibleColumns, fee: c})}>Fee</DropdownMenuCheckboxItem>
                        <DropdownMenuCheckboxItem checked={visibleColumns.ip} onCheckedChange={(c) => setVisibleColumns({...visibleColumns, ip: c})}>IP Address</DropdownMenuCheckboxItem>
                        <DropdownMenuCheckboxItem checked={visibleColumns.device} onCheckedChange={(c) => setVisibleColumns({...visibleColumns, device: c})}>Device</DropdownMenuCheckboxItem>
                    </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            <CardContent className="p-0 overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[30px]"><Checkbox /></TableHead>
                    <TableHead>Tx ID</TableHead>
                    <TableHead>Player</TableHead>
                    <TableHead>Type/Method</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    
                    {visibleColumns.net_amount && <TableHead className="text-right">Net</TableHead>}
                    {visibleColumns.fee && <TableHead className="text-right">Fee</TableHead>}
                    {visibleColumns.wallet && <TableHead className="text-right">Wallet</TableHead>}
                    
                    <TableHead>Status</TableHead>
                    
                    {/* Optional Columns */}
                    {visibleColumns.provider_id && <TableHead>Ref ID</TableHead>}
                    {visibleColumns.ip && <TableHead>IP</TableHead>}
                    {visibleColumns.device && <TableHead>Device</TableHead>}
                    
                    {/* Withdrawal Specific - Always show if withdrawal filter active, else conditional? Let's keep risk always */}
                    <TableHead>Risk</TableHead>
                    
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow><TableCell colSpan={15} className="text-center h-32">Loading...</TableCell></TableRow>
                  ) : transactions.length === 0 ? (
                    <TableRow><TableCell colSpan={15} className="text-center h-32 text-muted-foreground">No transactions found matching filters</TableCell></TableRow>
                  ) : (
                    transactions.map((tx) => (
                      <TableRow key={tx.id}>
                        <TableCell><Checkbox checked={selectedRows.includes(tx.id)} onCheckedChange={() => toggleRow(tx.id)}/></TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">{tx.id.substring(0, 8)}...</TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-medium text-blue-600 cursor-pointer hover:underline">{tx.player_username}</span>
                            {tx.country && <span className="text-[10px] text-muted-foreground flex items-center gap-1"><Globe className="w-3 h-3"/> {tx.country}</span>}
                          </div>
                        </TableCell>
                        <TableCell>
                           <div className="flex items-center gap-2">
                             <Badge variant="outline" className={tx.type === 'deposit' ? 'text-green-600 border-green-200' : tx.type === 'withdrawal' ? 'text-red-600 border-red-200' : 'text-blue-600 border-blue-200'}>
                                {tx.type === 'deposit' ? <ArrowDownRight className="w-3 h-3 mr-1" /> : tx.type === 'withdrawal' ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <RefreshCw className="w-3 h-3 mr-1" />}
                                {tx.type.toUpperCase()}
                             </Badge>
                             <span className="text-xs text-muted-foreground">{tx.method}</span>
                           </div>
                           <div className="text-[10px] text-muted-foreground mt-1">{tx.provider}</div>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="font-bold">{formatAmount(tx.amount, tx.currency)}</div>
                        </TableCell>
                        
                        {visibleColumns.net_amount && <TableCell className="text-right font-mono text-xs">${tx.net_amount?.toLocaleString()}</TableCell>}
                        {visibleColumns.fee && <TableCell className="text-right text-red-500 text-xs">-${tx.fee}</TableCell>}
                        {visibleColumns.wallet && (
                             <TableCell className="text-right text-xs">
                                 <div className="text-muted-foreground">{tx.balance_before?.toLocaleString()}</div>
                                 <div className="font-bold">→ {tx.balance_after?.toLocaleString()}</div>
                             </TableCell>
                        )}

                        <TableCell>
                          {getStatusBadge(tx.status)}
                        </TableCell>
                        
                         {visibleColumns.provider_id && <TableCell className="font-mono text-xs">{tx.provider_tx_id || '-'}</TableCell>}
                         {visibleColumns.ip && <TableCell className="font-mono text-xs">{tx.ip_address || '-'}</TableCell>}
                         {visibleColumns.device && <TableCell className="text-xs truncate max-w-[100px]" title={tx.device_info}>{tx.device_info || '-'}</TableCell>}
                        
                        <TableCell>{getRiskBadge(tx.risk_score_at_time || 'low')}</TableCell>

                        <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                          {new Date(tx.created_at).toLocaleDateString()}
                          <div className="text-[10px]">{new Date(tx.created_at).toLocaleTimeString()}</div>
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm"><MoreHorizontal className="w-4 h-4"/></Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={() => handleViewDetails(tx)}>
                                      <Eye className="w-4 h-4 mr-2"/> View Details
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                      <Edit className="w-4 h-4 mr-2"/> Edit Transaction
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                      <ExternalLink className="w-4 h-4 mr-2"/> Retry Callback
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  {tx.status === 'pending' || tx.status === 'under_review' ? (
                                      <>
                                        <DropdownMenuItem className="text-green-600">
                                            <CheckCircle className="w-4 h-4 mr-2"/> Approve
                                        </DropdownMenuItem>
                                        <DropdownMenuItem className="text-red-600">
                                            <XCircle className="w-4 h-4 mr-2"/> Reject
                                        </DropdownMenuItem>
                                      </>
                                  ) : null}
                                  <DropdownMenuItem className="text-orange-600">
                                      <ShieldAlert className="w-4 h-4 mr-2"/> Open in Fraud
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem>
                                      <Upload className="w-4 h-4 mr-2"/> Upload Proof
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                      <MessageSquare className="w-4 h-4 mr-2"/> Add Note
                                  </DropdownMenuItem>
                              </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
            <div className="flex items-center justify-between px-4 py-3 border-t text-xs text-muted-foreground">
              <div>
                Page {txMeta.page}
                {txMeta.total != null && txMeta.page_size && (
                  <span>
                    {' '}of {Math.max(1, Math.ceil(txMeta.total / txMeta.page_size))}
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={loading || txMeta.page <= 1}
                  onClick={() => {
                    const prevPage = (txMeta.page || 1) - 1;
                    if (prevPage < 1) return;
                    fetchData(prevPage).then(() => {
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    });
                  }}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={loading || transactions.length < (txMeta.page_size || pageSize)}
                  onClick={() => {
                    const nextPage = (txMeta.page || 1) + 1;
                    fetchData(nextPage).then(() => {
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    });
                  }}
                >
                  Next
                </Button>
              </div>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="reports" className="space-y-6">
            <div className="flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const params = new URLSearchParams();
                  Object.keys(filters).forEach((key) => {
                    if (filters[key] && filters[key] !== 'all') params.append(key, filters[key]);
                  });
                  api
                    .get('/v1/finance/reports/export', {
                      params: Object.fromEntries(params.entries()),
                      responseType: 'blob',
                    })
                    .then((res) => {
                      const url = window.URL.createObjectURL(new Blob([res.data]));
                      const link = document.createElement('a');
                      link.href = url;
                      link.setAttribute('download', `finance_reports_${new Date().toISOString()}.csv`);
                      document.body.appendChild(link);
                      link.click();
                      link.remove();
                    })
                    .catch(() => {
                      toast.error('Export failed');
                    });
                }}
              >
                <Download className="w-4 h-4 mr-2" /> Export CSV
              </Button>
            </div>

            {!reportData ? (
                <div className="text-center p-10">Loading Reports...</div>
            ) : (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <Card>
                            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">GGR (Gross Gaming Revenue)</CardTitle></CardHeader>
                            <CardContent><div className="text-2xl font-bold text-green-700">${reportData.ggr?.toLocaleString()}</div></CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">NGR (Net Gaming Revenue)</CardTitle></CardHeader>
                            <CardContent><div className="text-2xl font-bold text-blue-700">${reportData.ngr?.toLocaleString()}</div></CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Total Deposits</CardTitle></CardHeader>
                            <CardContent><div className="text-2xl font-bold">${reportData.total_deposit?.toLocaleString()}</div></CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Total Withdrawals</CardTitle></CardHeader>
                            <CardContent><div className="text-2xl font-bold text-red-600">${reportData.total_withdrawal?.toLocaleString()}</div></CardContent>
                        </Card>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Provider Breakdown */}
                        <Card>
                            <CardHeader><CardTitle>Provider Volume Breakdown</CardTitle></CardHeader>
                            <CardContent className="h-[300px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie 
                                            data={Object.entries(reportData.provider_breakdown || {}).map(([k,v]) => ({name: k, value: v}))}
                                            cx="50%" cy="50%" outerRadius={80} fill="#8884d8" dataKey="value" label
                                        >
                                            {Object.keys(reportData.provider_breakdown || {}).map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={['#0088FE', '#00C49F', '#FFBB28', '#FF8042'][index % 4]} />
                                            ))}
                                        </Pie>
                                        <RechartsTooltip />
                                        <Legend />
                                    </PieChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>

                        {/* Daily Stats */}
                        <Card>
                            <CardHeader><CardTitle>Daily Cashflow</CardTitle></CardHeader>
                            <CardContent className="h-[300px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={reportData.daily_stats}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="date" />
                                        <YAxis />
                                        <RechartsTooltip />
                                        <Legend />
                                        <Bar dataKey="deposit" fill="#10b981" name="Deposits" />
                                        <Bar dataKey="withdrawal" fill="#ef4444" name="Withdrawals" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Detailed Metrics Table */}
                    <Card>
                        <CardHeader><CardTitle>Detailed Cost Analysis</CardTitle></CardHeader>
                        <CardContent>
                            <Table>
                                <TableBody>
                                    <TableRow>
                                        <TableCell className="font-medium">Bonus Costs</TableCell>
                                        <TableCell className="text-right text-red-500">-${reportData.bonus_cost?.toLocaleString()}</TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell className="font-medium">Provider Costs (Estimated)</TableCell>
                                        <TableCell className="text-right text-red-500">-${reportData.provider_cost?.toLocaleString()}</TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell className="font-medium">Payment Gateway Fees</TableCell>
                                        <TableCell className="text-right text-red-500">-${reportData.payment_fees?.toLocaleString()}</TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell className="font-medium">Chargebacks ({reportData.chargeback_count || 0})</TableCell>
                                        <TableCell className="text-right text-red-500">-${reportData.chargeback_amount?.toLocaleString()}</TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell className="font-medium">FX Impact</TableCell>
                                        <TableCell className="text-right text-yellow-600">${reportData.fx_impact?.toLocaleString()}</TableCell>
                                    </TableRow>
                                    <TableRow className="bg-muted/50">
                                        <TableCell className="font-bold">Total Operational Costs</TableCell>
                                        <TableCell className="text-right font-bold text-red-700">
                                            -${((reportData.bonus_cost || 0) + (reportData.provider_cost || 0) + (reportData.payment_fees || 0) + (reportData.chargeback_amount || 0)).toLocaleString()}
                                        </TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </>
            )}
        </TabsContent>
        <TabsContent value="reconciliation">
            <ReconciliationPanel />
        </TabsContent>

        <TabsContent value="chargebacks">
            <ChargebackList />
        </TabsContent>
      </Tabs>

      {/* Detailed Modal */}
      <TransactionDetailModal 
        transaction={selectedTx} 
        open={isDetailOpen} 
        onOpenChange={setIsDetailOpen}
        onRefresh={fetchData}
      />
    </div>
  );
};

export default Finance;
