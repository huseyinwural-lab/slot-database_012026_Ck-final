import React, { useState } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Edit, Download, Plus } from 'lucide-react';
import { toast } from 'sonner';

const BrandSettings = ({ brands, onRefresh }) => {
  const safeBrands = Array.isArray(brands) ? brands : [];
  const [isBrandModalOpen, setIsBrandModalOpen] = useState(false);
  const [newBrand, setNewBrand] = useState({
    brand_name: '',
    default_currency: 'USD',
    default_language: 'en'
  });

  const handleCreateBrand = async () => {
    try {
      await api.post('/v1/settings/brands', newBrand);
      setIsBrandModalOpen(false);
      onRefresh();
      toast.success('Marka oluşturuldu');
    } catch { toast.error('Başarısız'); }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">Tenants / Brands</CardTitle>
          <CardDescription>Multi-brand yönetimi</CardDescription>
        </div>
        <Dialog open={isBrandModalOpen} onOpenChange={setIsBrandModalOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="w-4 h-4 mr-2" /> Add Brand</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Yeni Marka</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Brand Name</Label>
                <Input value={newBrand.brand_name} onChange={e=>setNewBrand({...newBrand, brand_name: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Default Currency</Label>
                <Select value={newBrand.default_currency} onValueChange={v=>setNewBrand({...newBrand, default_currency: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="TRY">TRY</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={handleCreateBrand} className="w-full">Oluştur</Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Brand Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Currency</TableHead>
              <TableHead>Language</TableHead>
              <TableHead>Countries</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {safeBrands.map(brand => (
              <TableRow key={brand.id}>
                <TableCell className="font-medium">{brand.brand_name}</TableCell>
                <TableCell><Badge variant={brand.status === 'active' ? 'default' : 'secondary'}>{brand.status}</Badge></TableCell>
                <TableCell>{brand.default_currency}</TableCell>
                <TableCell>{brand.default_language}</TableCell>
                <TableCell>{brand.country_availability?.length || 0}</TableCell>
                <TableCell className="text-xs">{new Date(brand.created_at).toLocaleDateString('tr-TR')}</TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost"><Edit className="w-4 h-4" /></Button>
                    <Button size="sm" variant="ghost"><Download className="w-4 h-4" /></Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {safeBrands.length === 0 && <p className="text-center text-muted-foreground py-8">Henüz marka yok</p>}
      </CardContent>
    </Card>
  );
};

export default BrandSettings;
