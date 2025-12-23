import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Pagination, PaginationContent, PaginationItem, PaginationNext, PaginationPrevious } from '@/components/ui/pagination';
import { Badge } from '@/components/ui/badge';

const PAGE_SIZE = 25;

const PlayerWallet = () => {
  const [balance, setBalance] = useState({ available: 0, held: 0, total: 0 });
  const [items, setItems] = useState([]);
  const [meta, setMeta] = useState({ total: 0, limit: PAGE_SIZE, offset: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const fetchData = async (pageOverride) => {
    const nextPage = pageOverride || page;
    const limit = PAGE_SIZE;
    const offset = (nextPage - 1) * limit;

    setLoading(true);
    try {
      // Balance endpoint (existing player wallet balance API)
      const balRes = await api.get('/v1/player/wallet/balance');
      const bal = balRes.data || {};
      const available = bal.balance_real_available ?? 0;
      const held = bal.balance_real_held ?? 0;
      setBalance({ available, held, total: available + held });

      // Transactions list endpoint (minimal: this assumes an existing backend route)
      const txRes = await api.get('/v1/player/wallet/transactions', {
        params: { limit, offset },
      });
      setItems(txRes.data.items || []);
      setMeta(txRes.data.meta || { total: 0, limit, offset });
      setPage(nextPage);
    } catch (err) {
      // Errors are already handled globally via interceptor
      // Keep UI calm on failure (just leave previous state)
      console.error('Failed to load wallet data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalPages = meta.limit ? Math.max(1, Math.ceil((meta.total || 0) / meta.limit)) : 1;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">My Wallet</h2>
        <p className="text-muted-foreground text-sm">Real-money balance and recent transactions.</p>
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Available</CardTitle>
            <CardDescription>Can be used for betting or withdrawal.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{balance.available.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Held</CardTitle>
            <CardDescription>Locked for pending withdrawals.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{balance.held.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <CardDescription>Available + Held.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{balance.total.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
          <CardDescription>Deposits and withdrawals on your wallet.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>State</TableHead>
                  <TableHead>Provider Ref</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-6 text-muted-foreground">
                      Loading...
                    </TableCell>
                  </TableRow>
                ) : items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-6 text-muted-foreground">
                      No transactions found.
                    </TableCell>
                  </TableRow>
                ) : (
                  items.map((tx) => (
                    <TableRow key={tx.id || tx.tx_id}>
                      <TableCell>
                        <Badge variant="outline" className="uppercase text-[10px]">
                          {tx.type}
                        </Badge>
                      </TableCell>
                      <TableCell>{`${tx.amount} ${tx.currency || ''}`.trim()}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="uppercase text-[10px]">
                          {tx.state}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs">{tx.provider_ref || '-'}</TableCell>
                      <TableCell className="text-xs">
                        {tx.created_at ? new Date(tx.created_at).toLocaleString() : '-'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
              <div>
                Showing {meta.offset + 1}–
                {Math.min(meta.offset + (meta.limit || PAGE_SIZE), meta.total || 0)} of {meta.total || 0}
              </div>
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      onClick={() => page > 1 && fetchData(page - 1)}
                      className={page <= 1 ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationNext
                      onClick={() => page < totalPages && fetchData(page + 1)}
                      className={page >= totalPages ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PlayerWallet;
