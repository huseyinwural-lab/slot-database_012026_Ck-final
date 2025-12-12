import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { KeyRound, Plus, Copy } from 'lucide-react';

const APIKeysPage = () => {
  const [keys, setKeys] = useState([]);
  const [scopes, setScopes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyScopes, setNewKeyScopes] = useState([]);
  const [generatedSecret, setGeneratedSecret] = useState('');
  const [generatedMeta, setGeneratedMeta] = useState(null);

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
      toast.error('İsim zorunludur');
      return;
    }
    if (newKeyScopes.length === 0) {
      toast.error('En az bir scope seçmelisiniz');
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
      } else {
        toast.error('Failed to create API key');
      }
    }
  };

  const handleToggleActive = async (id, current) => {
    try {
      const res = await api.patch(`/v1/api-keys/${id}`, { active: !current });
      setKeys((prev) => prev.map((k) => (k.id === id ? res.data : k)));
      toast.success('API key durumu güncellendi');
    } catch (err) {
      console.error(err);
      toast.error('Durum güncellenemedi');
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
      toast.success('API key kopyalandı');
    } catch {
      toast.error('Kopyalama başarısız');
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
            Game Robot ve dış entegrasyonlar için scope tabanlı API anahtarları yönetin.
          </p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" /> Yeni API Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Yeni API Key Oluştur</DialogTitle>
              <DialogDescription>
                Bu anahtar sadece bir kez gösterilecek. Lütfen oluşturduktan sonra güvenli bir yerde saklayın.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label>İsim</Label>
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
                Oluştur
              </Button>

              {generatedSecret && generatedMeta && (
                <Card className="mt-4 bg-muted">
                  <CardHeader>
                    <CardTitle className="text-sm">API Key Oluşturuldu</CardTitle>
                    <CardDescription className="text-xs">
                      Bu anahtar sadece bu ekranda gösterilecek. Lütfen kopyalayın.
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
          <CardTitle>API Key Listesi</CardTitle>
          <CardDescription>
            Aktif/pasif durumları ve scope’ları yönetin. Full secret yalnızca oluşturma anında gösterilir.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>İsim</TableHead>
                <TableHead>Key Prefix</TableHead>
                <TableHead>Tenant</TableHead>
                <TableHead>Scopes</TableHead>
                <TableHead>Durum</TableHead>
                <TableHead>Oluşturulma</TableHead>
                <TableHead>Son Kullanım</TableHead>
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
                      {key.active ? 'Aktif' : 'Pasif'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">
                    {key.created_at ? new Date(key.created_at).toLocaleString('tr-TR') : '-'}
                  </TableCell>
                  <TableCell className="text-xs">
                    {key.last_used_at ? new Date(key.last_used_at).toLocaleString('tr-TR') : '-'}
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
                    Henüz API key yok.
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
