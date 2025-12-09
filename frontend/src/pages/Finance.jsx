import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { CheckCircle, XCircle, AlertTriangle, Filter, Eye, Download } from 'lucide-react';

const Finance = () => {
  const [activeTab, setActiveTab] = useState("deposit");
  const [transactions, setTransactions] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [filters, setFilters] = useState({
    status: 'all',
    min_amount: '',
    max_amount: '',
    player_search: ''
  });

  // Action Dialog
  const [actionTx, setActionTx] = useState(null);
  const [actionNote, setActionNote] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
        if (activeTab === 'reports') {
            const res = await api.get('/v1/finance/reports');
            setReport(res.data);
        } else {
            const params = { type: activeTab };
            if (filters.status !== 'all') params.status = filters.status;
            if (filters.min_amount) params.min_amount = filters.min_amount;
            if (filters.max_amount) params.max_amount = filters.max_amount;
            if (filters.player_search) params.player_search = filters.player_search;
            
            const res = await api.get('/v1/finance/transactions', { params });
            setTransactions(res.data);
        }
    } catch (err) {
        toast.error("Failed to load data");
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  const handleAction = async (action) => {
    if (!actionTx) return;
    try {
        await api.post(`/v1/finance/transactions/${actionTx.id}/action`, { action, reason: actionNote });
        toast.success(`Transaction ${action}`);
        setActionTx(null);
        setActionNote("");
        fetchData();
    } catch (err) { toast.error("Action failed"); }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Finance Management</h2>
        {activeTab === 'reports' && <Button variant="outline"><Download className="w-4 h-4 mr-2" /> Export Report</Button>}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="deposit">Deposit Requests</TabsTrigger>
          <TabsTrigger value="withdrawal">Withdrawal Requests</TabsTrigger>
          <TabsTrigger value="reports">Financial Reports</TabsTrigger>
        </TabsList>
        
        {/* FILTERS FOR LISTS */}
        {activeTab !== 'reports' && (
            <Card className="mt-4">
                <CardContent className="pt-6 flex flex-wrap gap-4 items-end">
                    <div className="flex-1 min-w-[200px]">
                        <Input placeholder="Search Player Username/ID..." value={filters.player_search} onChange={e => setFilters({...filters, player_search: e.target.value})} />
                    </div>
                    <div className="w-[150px]">
                        <Select value={filters.status} onValueChange={v => setFilters({...filters, status: v})}>
                            <SelectTrigger><SelectValue placeholder="Status" /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Status</SelectItem>
                                <SelectItem value="pending">Pending</SelectItem>
                                <SelectItem value="completed">Success</SelectItem>
                                <SelectItem value="failed">Failed</SelectItem>
                                <SelectItem value="waiting_second_approval">Wait Approval</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="w-[120px]"><Input type="number" placeholder="Min $" value={filters.min_amount} onChange={e => setFilters({...filters, min_amount: e.target.value})} /></div>
                    <div className="w-[120px]"><Input type="number" placeholder="Max $" value={filters.max_amount} onChange={e => setFilters({...filters, max_amount: e.target.value})} /></div>
                    <Button variant="secondary" onClick={fetchData}><Filter className="w-4 h-4 mr-2" /> Filter</Button>
                </CardContent>
            </Card>
        )}

        {/* LIST VIEW */}
        <TabsContent value={activeTab} className="mt-4">
          {(activeTab === 'deposit' || activeTab === 'withdrawal') && (
              <Card>
                <CardHeader>
                    <CardTitle>{activeTab === 'deposit' ? 'Incoming Deposits' : 'Cashout Requests'}</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Tx ID</TableHead>
                        <TableHead>Player</TableHead>
                        <TableHead>Amount</TableHead>
                        <TableHead>Method</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                       {loading ? <TableRow><TableCell colSpan={7} className="text-center">Loading...</TableCell></TableRow> : 
                        transactions.length === 0 ? <TableRow><TableCell colSpan={7} className="text-center">No transactions.</TableCell></TableRow> :
                        transactions.map((tx) => (
                        <TableRow key={tx.id}>
                          <TableCell className="font-mono text-xs">{tx.id}</TableCell>
                          <TableCell>
                            <div className="font-medium">{tx.player_username || tx.player_id}</div>
                          </TableCell>
                          <TableCell className={`font-bold ${tx.type==='deposit'?'text-green-500':'text-red-500'}`}>
                            ${tx.amount}
                          </TableCell>
                          <TableCell>{tx.method}</TableCell>
                          <TableCell>
                            <Badge variant={tx.status === 'completed' ? 'default' : tx.status === 'pending' ? 'secondary' : 'destructive'}>
                              {tx.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">{new Date(tx.created_at).toLocaleString()}</TableCell>
                          <TableCell className="text-right">
                            {tx.status === 'pending' && (
                                <Dialog>
                                    <DialogTrigger asChild>
                                        <Button size="sm" onClick={() => setActionTx(tx)}>Manage</Button>
                                    </DialogTrigger>
                                    <DialogContent>
                                        <DialogHeader>
                                            <DialogTitle>Process Transaction</DialogTitle>
                                            <CardDescription>TX: {tx.id} - ${tx.amount}</CardDescription>
                                        </DialogHeader>
                                        <div className="space-y-4 py-2">
                                            <Textarea placeholder="Admin note / Rejection reason..." value={actionNote} onChange={e => setActionNote(e.target.value)} />
                                            <div className="grid grid-cols-3 gap-2">
                                                <Button className="bg-green-600 hover:bg-green-700" onClick={() => handleAction('approve')}>
                                                    <CheckCircle className="w-4 h-4 mr-2" /> Approve
                                                </Button>
                                                <Button variant="destructive" onClick={() => handleAction('reject')}>
                                                    <XCircle className="w-4 h-4 mr-2" /> Reject
                                                </Button>
                                                <Button variant="outline" className="border-red-500 text-red-500 hover:bg-red-50" onClick={() => handleAction('fraud')}>
                                                    <AlertTriangle className="w-4 h-4 mr-2" /> Fraud
                                                </Button>
                                            </div>
                                        </div>
                                    </DialogContent>
                                </Dialog>
                            )}
                            <Button variant="ghost" size="sm"><Eye className="w-4 h-4" /></Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
          )}

          {/* REPORT VIEW */}
          {activeTab === 'reports' && report && (
              <div className="grid gap-6">
                  <div className="grid md:grid-cols-3 gap-4">
                      <Card>
                          <CardHeader><CardTitle className="text-sm">Total Deposit</CardTitle></CardHeader>
                          <CardContent><div className="text-2xl font-bold text-green-500">${report.total_deposit.toLocaleString()}</div></CardContent>
                      </Card>
                      <Card>
                          <CardHeader><CardTitle className="text-sm">Total Withdrawal</CardTitle></CardHeader>
                          <CardContent><div className="text-2xl font-bold text-red-500">${report.total_withdrawal.toLocaleString()}</div></CardContent>
                      </Card>
                      <Card>
                          <CardHeader><CardTitle className="text-sm">Net Cashflow</CardTitle></CardHeader>
                          <CardContent><div className="text-2xl font-bold text-blue-500">${report.net_cashflow.toLocaleString()}</div></CardContent>
                      </Card>
                  </div>
                  
                  <Card>
                      <CardHeader><CardTitle>Provider Breakdown</CardTitle></CardHeader>
                      <CardContent>
                          <Table>
                              <TableHeader><TableRow><TableHead>Provider</TableHead><TableHead className="text-right">Volume</TableHead></TableRow></TableHeader>
                              <TableBody>
                                  {Object.entries(report.provider_breakdown).map(([k, v]) => (
                                      <TableRow key={k}>
                                          <TableCell>{k}</TableCell>
                                          <TableCell className="text-right font-bold">${v.toLocaleString()}</TableCell>
                                      </TableRow>
                                  ))}
                              </TableBody>
                          </Table>
                      </CardContent>
                  </Card>
              </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Finance;
