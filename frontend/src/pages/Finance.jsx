import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const Finance = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("deposit");

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const res = await api.get('/v1/finance/transactions', { 
        params: { type: activeTab === 'all' ? undefined : activeTab } 
      });
      setTransactions(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [activeTab]);

  const handleApprove = async (id) => {
    try {
        await api.post(`/v1/finance/transactions/${id}/approve`);
        toast.success("Transaction Approved");
        fetchTransactions();
    } catch (err) {
        toast.error("Failed to approve");
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Finance Management</h2>

      <Tabs defaultValue="deposit" className="w-full" onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="deposit">Deposits</TabsTrigger>
          <TabsTrigger value="withdrawal">Withdrawals</TabsTrigger>
        </TabsList>
        
        <TabsContent value={activeTab} className="mt-4">
          <Card>
            <CardHeader><CardTitle>{activeTab === 'deposit' ? 'Deposit Requests' : 'Withdrawal Requests'}</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Player</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                   {loading ? (
                    <TableRow><TableCell colSpan={7} className="text-center">Loading...</TableCell></TableRow>
                  ) : transactions.length === 0 ? (
                    <TableRow><TableCell colSpan={7} className="text-center">No transactions found.</TableCell></TableRow>
                  ) : transactions.map((tx) => (
                    <TableRow key={tx.id}>
                      <TableCell className="font-mono text-xs">{tx.id}</TableCell>
                      <TableCell>{tx.player_id}</TableCell>
                      <TableCell className="font-bold text-green-500">${tx.amount}</TableCell>
                      <TableCell>{tx.method}</TableCell>
                      <TableCell>
                        <Badge variant={tx.status === 'completed' || tx.status === 'approved' ? 'default' : tx.status === 'pending' ? 'secondary' : 'destructive'}>
                          {tx.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">{new Date(tx.created_at).toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        {tx.status === 'pending' && (
                            <Button size="sm" onClick={() => handleApprove(tx.id)}>Approve</Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Finance;
