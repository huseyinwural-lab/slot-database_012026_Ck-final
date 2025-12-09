import React, { useState } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Globe, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const DomainSettings = ({ domains, onRefresh }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newDomain, setNewDomain] = useState({
    domain: '',
    brand_id: '',
    market: 'Global',
    currency: 'USD'
  });

  const handleCreate = async () => {
    try {
      await api.post('/v1/settings/domains', newDomain);
      setIsModalOpen(false);
      onRefresh();
      toast.success('Domain eklendi');
    } catch { toast.error('Başarısız'); }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">Domains & Markets</CardTitle>
          <CardDescription>Domain bazlı pazar yönetimi</CardDescription>
        </div>
        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Domain</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Yeni Domain</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2"><Label>Domain</Label><Input value={newDomain.domain} onChange={e=>setNewDomain({...newDomain, domain: e.target.value})} placeholder="example.com" /></div>
              <div className="space-y-2"><Label>Brand ID</Label><Input value={newDomain.brand_id} onChange={e=>setNewDomain({...newDomain, brand_id: e.target.value})} /></div>
              <div className="space-y-2"><Label>Market</Label><Input value={newDomain.market} onChange={e=>setNewDomain({...newDomain, market: e.target.value})} /></div>
              <Button onClick={handleCreate} className="w-full">Oluştur</Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Domain</TableHead>
              <TableHead>Brand</TableHead>
              <TableHead>Market</TableHead>
              <TableHead>Currency</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {domains.map(d => (
              <TableRow key={d.id}>
                <TableCell className="font-medium">{d.domain}</TableCell>
                <TableCell>{d.brand_id}</TableCell>
                <TableCell>{d.market}</TableCell>
                <TableCell>{d.currency}</TableCell>
                <TableCell><Badge variant="default">{d.status}</Badge></TableCell>
                <TableCell><Button variant="ghost" size="sm"><Trash2 className="w-4 h-4" /></Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default DomainSettings;
