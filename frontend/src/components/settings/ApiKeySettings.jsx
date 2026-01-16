import React from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Plus } from 'lucide-react';
import { toast } from 'sonner';

const ApiKeySettings = ({ apiKeys, onRefresh }) => {
  // P1: Settings-level API keys/webhooks generation is not available in this environment.
  const handleGenerateAPIKey = async () => {
    // no-op
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">API Keys & Webhooks</CardTitle>
        </div>
        <Button disabled title="Not available in this environment"><Plus className="w-4 h-4 mr-2" /> Generate Key</Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Key Name</TableHead>
              <TableHead>Key Hash</TableHead>
              <TableHead>Owner</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {apiKeys.map(key => (
              <TableRow key={key.id}>
                <TableCell className="font-medium">{key.key_name}</TableCell>
                <TableCell className="font-mono text-xs">{key.key_hash}</TableCell>
                <TableCell>{key.owner}</TableCell>
                <TableCell><Badge variant={key.status === 'active' ? 'default' : 'secondary'}>{key.status}</Badge></TableCell>
                <TableCell className="text-xs">{new Date(key.created_at).toLocaleDateString('tr-TR')}</TableCell>
                <TableCell>
                  <Button size="sm" variant="destructive" disabled title="Not available in this environment">Revoke</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {apiKeys.length === 0 && <p className="text-center text-muted-foreground py-8">No API keys</p>}
      </CardContent>
    </Card>
  );
};

export default ApiKeySettings;
