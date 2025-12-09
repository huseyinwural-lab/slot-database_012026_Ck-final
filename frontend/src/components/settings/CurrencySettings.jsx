import React from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const CurrencySettings = ({ currencies, onRefresh }) => {
  const handleSyncRates = async () => {
    try {
      await api.post('/v1/settings/currencies/sync-rates');
      toast.success('Döviz kurları güncellendi');
      onRefresh();
    } catch { toast.error('Başarısız'); }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">Currencies & Exchange Rates</CardTitle>
        </div>
        <Button onClick={handleSyncRates}><RefreshCw className="w-4 h-4 mr-2" /> Sync Rates</Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Currency</TableHead>
              <TableHead>Symbol</TableHead>
              <TableHead>Exchange Rate</TableHead>
              <TableHead>Min Deposit</TableHead>
              <TableHead>Max Deposit</TableHead>
              <TableHead>Updated</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {currencies.map(curr => (
              <TableRow key={curr.id}>
                <TableCell className="font-medium">{curr.currency_code}</TableCell>
                <TableCell>{curr.symbol}</TableCell>
                <TableCell>{curr.exchange_rate.toFixed(4)}</TableCell>
                <TableCell>${curr.min_deposit}</TableCell>
                <TableCell>${curr.max_deposit}</TableCell>
                <TableCell className="text-xs">{new Date(curr.updated_at).toLocaleDateString('tr-TR')}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default CurrencySettings;
