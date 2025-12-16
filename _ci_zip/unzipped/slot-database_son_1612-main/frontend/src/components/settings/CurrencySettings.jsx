import React, { useState } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { RefreshCw, Plus, Edit, Trash2, DollarSign } from 'lucide-react';
import { toast } from 'sonner';

const CurrencySettings = ({ currencies, onRefresh }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    currency_code: '',
    symbol: '',
    exchange_rate: 1.0,
    base_currency: 'USD',
    min_deposit: 10,
    max_deposit: 10000
  });

  const resetForm = () => {
    setFormData({
      currency_code: '',
      symbol: '',
      exchange_rate: 1.0,
      base_currency: 'USD',
      min_deposit: 10,
      max_deposit: 10000
    });
    setEditingId(null);
  };

  const handleOpenCreate = () => {
    resetForm();
    setIsModalOpen(true);
  };

  const handleOpenEdit = (curr) => {
    setFormData({
      currency_code: curr.currency_code,
      symbol: curr.symbol,
      exchange_rate: curr.exchange_rate,
      base_currency: curr.base_currency,
      min_deposit: curr.min_deposit,
      max_deposit: curr.max_deposit
    });
    setEditingId(curr.id);
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editingId) {
        await api.put(`/v1/settings/currencies/${editingId}`, formData);
        toast.success('Para birimi güncellendi');
      } else {
        await api.post('/v1/settings/currencies', formData);
        toast.success('Para birimi eklendi');
      }
      setIsModalOpen(false);
      onRefresh();
    } catch (err) {
      toast.error('İşlem başarısız');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Silmek istediğinize emin misiniz?')) return;
    try {
      await api.delete(`/v1/settings/currencies/${id}`);
      toast.success('Silindi');
      onRefresh();
    } catch {
      toast.error('Silinemedi');
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-green-600" /> Currencies & Exchange Rates
          </CardTitle>
          <CardDescription>
            Referans Kur: <Badge variant="outline">USD ($)</Badge> • Kurları manuel yönetin
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onRefresh}>
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
            <DialogTrigger asChild>
              <Button onClick={handleOpenCreate}><Plus className="w-4 h-4 mr-2" /> Yeni Para Birimi</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingId ? 'Para Birimi Düzenle' : 'Yeni Para Birimi Ekle'}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Currency Code</Label>
                    <Input 
                      value={formData.currency_code} 
                      onChange={e => setFormData({...formData, currency_code: e.target.value.toUpperCase()})} 
                      placeholder="EUR, TRY, CHF..." 
                      disabled={editingId && formData.currency_code === 'USD'}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Symbol</Label>
                    <Input 
                      value={formData.symbol} 
                      onChange={e => setFormData({...formData, symbol: e.target.value})} 
                      placeholder="€, ₺, ₣..." 
                    />
                  </div>
                </div>
                
                <div className="space-y-2 p-4 bg-muted/30 rounded-lg">
                  <Label>Exchange Rate (1 USD = ?)</Label>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-muted-foreground">1 USD =</span>
                    <Input 
                      type="number" 
                      step="0.0001" 
                      value={formData.exchange_rate} 
                      onChange={e => setFormData({...formData, exchange_rate: parseFloat(e.target.value)})} 
                      className="text-lg font-mono"
                      disabled={formData.currency_code === 'USD'}
                    />
                    <span className="text-sm font-bold text-muted-foreground">{formData.currency_code || 'UNIT'}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Örnek: 1 USD = 0.92 EUR veya 1 USD = 0.88 CHF (İsviçre Frankı)
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Min Deposit</Label>
                    <Input type="number" value={formData.min_deposit} onChange={e => setFormData({...formData, min_deposit: parseFloat(e.target.value)})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Max Deposit</Label>
                    <Input type="number" value={formData.max_deposit} onChange={e => setFormData({...formData, max_deposit: parseFloat(e.target.value)})} />
                  </div>
                </div>

                <Button onClick={handleSave} className="w-full">
                  {editingId ? 'Güncelle' : 'Oluştur'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Symbol</TableHead>
              <TableHead>Rate (vs USD)</TableHead>
              <TableHead>Min/Max Deposit</TableHead>
              <TableHead>Updated</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {currencies.map(curr => (
              <TableRow key={curr.id}>
                <TableCell className="font-bold">{curr.currency_code}</TableCell>
                <TableCell>{curr.symbol}</TableCell>
                <TableCell className="font-mono">
                  {curr.currency_code === 'USD' ? (
                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">BASE</Badge>
                  ) : (
                    curr.exchange_rate.toFixed(4)
                  )}
                </TableCell>
                <TableCell className="text-xs">
                  {curr.min_deposit} - {curr.max_deposit}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {new Date(curr.updated_at).toLocaleDateString('tr-TR')}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" size="sm" onClick={() => handleOpenEdit(curr)}>
                      <Edit className="w-4 h-4 text-blue-600" />
                    </Button>
                    {curr.currency_code !== 'USD' && (
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(curr.id)}>
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default CurrencySettings;
