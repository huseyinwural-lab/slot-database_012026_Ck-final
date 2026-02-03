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
    setLoading(true);
    try {
      const [keysRes, scopesRes] = await Promise.all([
        api.get('/v1/api-keys/'),
        api.get('/v1/api-keys/scopes'),
      ]);
      setKeys(keysRes.data || []);
      setScopes(scopesRes.data || []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load API key data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const toggleScope = (scope) => {
    setNewKeyScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]
    );
  };

  const handleCreate = async () => {
    if (!newKeyName.trim()) {
      toast.error('Name is required');
      return;
    }
    if (newKeyScopes.length === 0) {
      toast.error('You must select at least one scope');
      return;
    }
    try {
      const res = await api.post('/v1/api-keys/', {
        name: newKeyName.trim(),
        scopes: newKeyScopes,
      });
      setGeneratedSecret(res.data.api_key);
      setGeneratedMeta(res.data.key);
      toast.success('API key created');
      setNewKeyName('');
      setNewKeyScopes([]);
      fetchData();
    } catch (err) {
      console.error(err);
      const detail = err?.response?.data?.detail;
      if (detail?.error_code === 'INVALID_API_KEY_SCOPE') {
        toast.error('Invalid scope selection');
      } else if (err?.response?.status === 403 && detail?.error_code === 'TENANT_FEATURE_DISABLED') {
        toast.error('This module is disabled for your tenant.');
      } else {
        toast.error('Failed to create API key');
      }
    }
  };

  const handleToggleActive = async (id, current) => {
    try {
      const res = await api.patch(`/v1/api-keys/${id}`, { active: !current });
      setKeys((prev) => prev.map((k) => (k.id === id ? res.data : k)));
      toast.success('API key status updated');
    } catch (err) {
      console.error(err);
      toast.error('Failed to update status');
    }
  };

  const maskPrefix = (prefix) => {
    if (!prefix) return '';
    return `${prefix}****`;
  };

  const copySecret = async () => {
    if (!generatedSecret) return;
    try {
      await navigator.clipboard.writeText(generatedSecret);
      toast.success('API key copied');
    } catch {
      toast.error('Copy failed');
    }
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
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" /> New API Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
              <DialogDescription>
                This key will only be shown once. Please store it securely after creation.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Scopes</Label>
                <div className="grid grid-cols-2 gap-2">
                  {scopes.map((scope) => (
                    <button
                      key={scope}
                      type="button"
                      onClick={() => toggleScope(scope)}
                      className={`flex items-center justify-between border rounded px-3 py-2 text-xs ${
                        newKeyScopes.includes(scope)
                          ? 'bg-primary text-primary-foreground border-primary'
                          : 'hover:bg-secondary'
                      }`}
                    >
                      <span>{scope}</span>
                      {newKeyScopes.includes(scope) && <span>✓</span>}
                    </button>
                  ))}
                </div>
              </div>
              <Button className="w-full" onClick={handleCreate} disabled={loading}>
                Create
              </Button>

              {generatedSecret && generatedMeta && (
                <Card className="mt-4 bg-muted">
                  <CardHeader>
                    <CardTitle className="text-sm">API Key Created</CardTitle>
                    <CardDescription className="text-xs">
                      This key will only be shown on this screen. Please copy and store it safely.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-background px-2 py-1 rounded flex-1 truncate">
                        {generatedSecret}
                      </code>
                      <Button size="icon" variant="outline" onClick={copySecret}>
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Key prefix: <span className="font-mono">{generatedMeta.key_prefix}</span>
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API Key List</CardTitle>
          <CardDescription>
            Manage active/inactive status and scopes. The full secret is only shown at creation time.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Key Prefix</TableHead>
                <TableHead>Tenant</TableHead>
                <TableHead>Scopes</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead></TableHead>
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
