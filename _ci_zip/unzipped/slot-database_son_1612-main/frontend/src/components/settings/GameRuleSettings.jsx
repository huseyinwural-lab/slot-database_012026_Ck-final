import React, { useState } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Gamepad2, Plus } from 'lucide-react';
import { toast } from 'sonner';

const GameRuleSettings = ({ rules, onRefresh }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newRule, setNewRule] = useState({
    game_id: '',
    brand_id: 'default',
    country_code: '',
    is_allowed: true
  });

  const handleCreate = async () => {
    try {
      await api.post('/v1/settings/game-availability', newRule);
      setIsModalOpen(false);
      onRefresh();
      toast.success('Kural eklendi');
    } catch { toast.error('Başarısız'); }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div><CardTitle className="flex items-center gap-2">Game Availability Rules</CardTitle></div>
        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Rule</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Yeni Oyun Kuralı</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2"><Label>Game ID</Label><Input value={newRule.game_id} onChange={e=>setNewRule({...newRule, game_id: e.target.value})} /></div>
              <div className="space-y-2"><Label>Country Code</Label><Input value={newRule.country_code} onChange={e=>setNewRule({...newRule, country_code: e.target.value})} placeholder="TR" /></div>
              <Button onClick={handleCreate} className="w-full">Oluştur</Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Game ID</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Allowed</TableHead>
              <TableHead>RTP Override</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rules.map(r => (
              <TableRow key={r.id}>
                <TableCell className="font-mono">{r.game_id}</TableCell>
                <TableCell>{r.country_code}</TableCell>
                <TableCell><Badge variant={r.is_allowed ? 'default' : 'destructive'}>{r.is_allowed ? 'Yes' : 'No'}</Badge></TableCell>
                <TableCell>{r.rtp_override_allowed ? 'Yes' : 'No'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default GameRuleSettings;
