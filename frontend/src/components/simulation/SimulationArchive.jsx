import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Eye, RefreshCw, Download } from 'lucide-react';

const SimulationArchive = ({ runs, getTypeBadge, getStatusBadge }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">📁 Simulation Runs & Results Archive</CardTitle>
        <CardDescription>Tüm geçmiş simülasyonlar</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Simulation ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Owner</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runs.map(run => (
              <TableRow key={run.id}>
                <TableCell className="font-mono text-xs">{run.id}</TableCell>
                <TableCell className="font-medium">{run.name}</TableCell>
                <TableCell>{getTypeBadge(run.simulation_type)}</TableCell>
                <TableCell>{getStatusBadge(run.status)}</TableCell>
                <TableCell className="text-xs">{run.created_by}</TableCell>
                <TableCell>
                  {run.tags?.map(tag => <Badge key={tag} variant="outline" className="mr-1 text-xs">{tag}</Badge>)}
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" disabled title="Not implemented yet"><Eye className="w-4 h-4" /></Button>
                    <Button size="sm" variant="ghost" disabled title="Not implemented yet"><RefreshCw className="w-4 h-4" /></Button>
                    <Button size="sm" variant="ghost" disabled title="Not implemented yet"><Download className="w-4 h-4" /></Button>
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

export default SimulationArchive;
