import React, { useState } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Scale, Plus } from 'lucide-react';
import { toast } from 'sonner';

const RegulatorySettings = ({ settings, onRefresh }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newReg, setNewReg] = useState({
    jurisdiction: '',
    min_age: 18,
    aml_threshold: 2000
  });

  const handleCreate = async () => {
    try {
      await api.post('/v1/settings/regulatory', newReg);
      setIsModalOpen(false);
      onRefresh();
      toast.success('Kural seti eklendi');
    } catch { toast.error('Başarısız'); }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div><CardTitle className="flex items-center gap-2">Compliance & Regulatory</CardTitle></div>
        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Jurisdiction</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Yeni Yasal Bölge</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2"><Label>Jurisdiction</Label><Input value={newReg.jurisdiction} onChange={e=>setNewReg({...newReg, jurisdiction: e.target.value})} placeholder="Malta / Curacao" /></div>
              <div className="space-y-2"><Label>Min Age</Label><Input type="number" value={newReg.min_age} onChange={e=>setNewReg({...newReg, min_age: parseInt(e.target.value)})} /></div>
              <Button onClick={handleCreate} className="w-full">Oluştur</Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Jurisdiction</TableHead>
              <TableHead>Min Age</TableHead>
              <TableHead>AML Threshold</TableHead>
              <TableHead>RTP Req</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {settings.map(s => (
              <TableRow key={s.id}>
                <TableCell className="font-medium">{s.jurisdiction}</TableCell>
                <TableCell>{s.min_age}+</TableCell>
                <TableCell>${s.aml_threshold}</TableCell>
                <TableCell>{s.min_rtp_requirement}%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default RegulatorySettings;
