import React, { useEffect } from 'react';
import api from '../services/api';
import useTableState from '@/hooks/useTableState';
import { TableSkeletonRows } from '@/components/TableState';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { KeyRound, Plus } from 'lucide-react';

const APIKeysPage = () => {
  const keysTable = useTableState([]);
  const keys = keysTable.rows;

  const fetchData = async () => {
    await keysTable
      .run(async () => {
        const keysRes = await api.get('/v1/api-keys/');
        keysTable.setRows(Array.isArray(keysRes.data) ? keysRes.data : []);
      })
      .catch(() => {
        keysTable.setRows([]);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateClick = () => {
    toast.warning('API Anahtarı oluşturma yetkiniz bulunmamaktadır.', {
      description: 'Lütfen sistem yöneticisi ile iletişime geçin.',
    });
  };

  const maskPrefix = (prefix) => {
    if (!prefix) return '';
    return `${prefix}****`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <KeyRound className="w-7 h-7 text-primary" /> API Keys
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage scope-based API keys for Game Robot and external integrations.
          </p>
        </div>
        <Button onClick={handleCreateClick} data-testid="api-keys-create-button">
          <Plus className="w-4 h-4 mr-2" /> API Anahtarı Oluştur
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API Key List</CardTitle>
          <CardDescription>
            Manage active/inactive status and scopes. The full secret is only shown at creation time.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table data-testid="api-keys-table">
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Key Prefix</TableHead>
                <TableHead>Scopes</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead>Last Used</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys.map((key) => (
                <TableRow key={key.id}>
                  <TableCell>{key.name}</TableCell>
                  <TableCell className="font-mono text-xs">{maskPrefix(key.key_prefix)}</TableCell>
                  <TableCell className="text-xs">{key.tenant_id}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {key.scopes.map((s) => (
                        <Badge key={s} variant="outline" className="text-[10px]">
                          {s}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={key.active ? 'default' : 'secondary'}>
                      {key.active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">
                    {key.created_at ? new Date(key.created_at).toLocaleString('en-US') : '-'}
                  </TableCell>
                  <TableCell className="text-xs">
                    {key.last_used_at ? new Date(key.last_used_at).toLocaleString('en-US') : '-'}
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={key.active}
                      onCheckedChange={() => handleToggleActive(key.id, key.active)}
                    />
                  </TableCell>
                </TableRow>
              ))}
              {keys.length === 0 && !loading && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground text-sm py-8">
                    No API keys yet.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default APIKeysPage;
