import React, { useState } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { CreditCard, Activity, Plus } from 'lucide-react';
import { toast } from 'sonner';

const PaymentSettings = ({ providers, onRefresh }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newProvider, setNewProvider] = useState({
    provider_name: '',
    brand_id: '',
    provider_type: 'deposit',
    min_amount: 10,
    max_amount: 10000
  });

  const handleCreate = async () => {
    try {
      await api.post('/v1/settings/payment-providers', newProvider);
      setIsModalOpen(false);
      onRefresh();
      toast.success('Ödeme sağlayıcı eklendi');
    } catch { toast.error('Başarısız'); }
  };

  const checkHealth = async (id) => {
    try {
      await api.post(`/v1/settings/payment-providers/${id}/health-check`);
      toast.success('Sağlık kontrolü başarılı');
      onRefresh();
    } catch { toast.error('Kontrol başarısız'); }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div><CardTitle className="flex items-center gap-2">Payment Providers</CardTitle></div>
        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Provider</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Yeni Ödeme Sağlayıcı</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2"><Label>Provider Name</Label><Input value={newProvider.provider_name} onChange={e=>setNewProvider({...newProvider, provider_name: e.target.value})} /></div>
              <div className="space-y-2"><Label>Type</Label><Input value={newProvider.provider_type} onChange={e=>setNewProvider({...newProvider, provider_type: e.target.value})} placeholder="deposit/withdrawal" /></div>
              <Button onClick={handleCreate} className="w-full">Oluştur</Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Provider</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Limits</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Health</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {providers.map(p => (
              <TableRow key={p.id}>
                <TableCell className="font-medium">{p.provider_name}</TableCell>
                <TableCell className="capitalize">{p.provider_type}</TableCell>
                <TableCell>${p.min_amount} - ${p.max_amount}</TableCell>
                <TableCell><Badge variant="outline">{p.status}</Badge></TableCell>
                <TableCell>
                  <Badge variant={p.health_status === 'healthy' ? 'default' : 'destructive'}>
                    {p.health_status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Button variant="ghost" size="sm" onClick={() => checkHealth(p.id)}>
                    <Activity className="w-4 h-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default PaymentSettings;
