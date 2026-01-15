import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Eye, Download } from 'lucide-react';

const SimulationOverview = ({ runs, getTypeBadge, getStatusBadge }) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Lab Genel Durum</CardTitle>
          <CardDescription>Son simülasyonlar ve özet</CardDescription>
        </div>
        <Button disabled title="Not implemented yet"><Plus className="w-4 h-4 mr-2" /> Yeni Simülasyon</Button>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{runs.length}</div>
              <p className="text-xs text-muted-foreground">Toplam Simülasyon</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{runs.filter(r => r.status === 'completed').length}</div>
              <p className="text-xs text-muted-foreground">Tamamlanan</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{runs.filter(r => r.status === 'running').length}</div>
              <p className="text-xs text-muted-foreground">Çalışan</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{runs.filter(r => r.status === 'draft').length}</div>
              <p className="text-xs text-muted-foreground">Taslak</p>
            </CardContent>
          </Card>
        </div>

        <h3 className="font-bold mb-4">Son Simülasyonlar</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created By</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runs.slice(0, 10).map(run => (
              <TableRow key={run.id}>
                <TableCell className="font-medium">{run.name}</TableCell>
                <TableCell>{getTypeBadge(run.simulation_type)}</TableCell>
                <TableCell>{getStatusBadge(run.status)}</TableCell>
                <TableCell className="text-xs">{run.created_by}</TableCell>
                <TableCell className="text-xs">{new Date(run.created_at).toLocaleString('tr-TR')}</TableCell>
                <TableCell className="text-xs">{run.duration_seconds ? `${run.duration_seconds}s` : '-'}</TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" disabled title="Not implemented yet"><Eye className="w-4 h-4" /></Button>
                    <Button size="sm" variant="ghost" disabled title="Not implemented yet"><Download className="w-4 h-4" /></Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {runs.length === 0 && <p className="text-center text-muted-foreground py-8">Henüz simülasyon yok</p>}
      </CardContent>
    </Card>
  );
};

export default SimulationOverview;
