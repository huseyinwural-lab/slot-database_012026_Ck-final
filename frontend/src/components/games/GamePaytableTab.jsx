import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { RefreshCcw, Pencil } from 'lucide-react';
import api from '../../services/api';
import ConfigDiffPanel from './ConfigDiffPanel';

const GamePaytableTab = ({ game, paytable, onReload }) => {
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [jsonText, setJsonText] = useState(
    paytable?.current?.data ? JSON.stringify(paytable.current.data, null, 2) : '{"symbols": [], "lines": 20}'
  );
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const current = paytable?.current;
  const history = paytable?.history || [];

  const symbols = current?.data?.symbols || [];
  const allMultiplierKeys = Array.from(
    new Set(symbols.flatMap((s) => (s.pays ? Object.keys(s.pays) : [])))
  ).sort((a, b) => Number(a) - Number(b));

  const handleOpenOverride = () => {
    setJsonText(current?.data ? JSON.stringify(current.data, null, 2) : '{"symbols": [], "lines": 20}');
    setOverrideOpen(true);
  };

  const handleSaveOverride = async () => {
    let parsed;
    try {
      parsed = JSON.parse(jsonText);
    } catch (e) {
      toast.error('Geçersiz JSON');
      return;
    }

    if (!parsed.symbols || !Array.isArray(parsed.symbols) || parsed.symbols.length === 0) {
      toast.error('symbols alanı zorunlu ve boş olamaz');
      return;
    }

    setSaving(true);
    try {
      await api.post(`/v1/games/${game.id}/config/paytable/override`, {
        data: parsed,
        summary: 'Paytable override from UI',
      });
      toast.success('Paytable override kaydedildi');
      setOverrideOpen(false);
      await onReload?.();
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      const msg = apiError?.message || apiError?.detail || 'Override kaydedilemedi';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleRefreshFromProvider = async () => {
    setRefreshing(true);
    try {
      await api.post(`/v1/games/${game.id}/config/paytable/refresh-from-provider`);
      toast.success("Paytable provider'dan yenilendi (stub)");
      await onReload?.();
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      const msg = apiError?.message || apiError?.detail || "Provider'dan yenileme başarısız";
      toast.error(msg);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant={current?.source === 'override' ? 'default' : 'outline'}>
              {current?.source === 'override' ? 'Override' : 'Provider'}
            </Badge>
            {current && (
              <span className="text-xs text-muted-foreground">
                v{current.config_version_id?.slice(0, 8)} • {current.created_by} •{' '}
                {new Date(current.created_at).toLocaleString()}
              </span>
            )}
          </div>
          {!current && <p className="text-xs text-muted-foreground">Henüz kayıtlı bir paytable yok.</p>}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshFromProvider}
            disabled={refreshing}
          >
            <RefreshCcw className="w-4 h-4 mr-1" />
            {refreshing ? 'Refreshing...' : 'Refresh from Provider'}
          </Button>
          <Button variant="secondary" size="sm" onClick={handleOpenOverride}>
            <Pencil className="w-4 h-4 mr-1" /> Override Paytable
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Symbol Payout Grid</CardTitle>
          <CardDescription>Aktif paytable&apos;daki semboller ve ödeme katsayıları.</CardDescription>
        </CardHeader>
        <CardContent>
          {symbols.length === 0 ? (
            <div className="text-xs text-muted-foreground">Gösterilecek symbol bulunamadı.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  {allMultiplierKeys.map((k) => (
                    <TableHead key={k}>{k}x</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {symbols.map((s) => (
                  <TableRow key={s.code}>
                    <TableCell className="font-mono text-xs">{s.code}</TableCell>
                    {allMultiplierKeys.map((k) => (
                      <TableCell key={k} className="text-xs">
                        {s.pays && s.pays[k] != null ? s.pays[k] : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Paytable History</CardTitle>
          <CardDescription>Son versiyon değişikliklerinin özeti.</CardDescription>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <div className="text-xs text-muted-foreground">Henüz paytable geçmişi yok.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Version</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Tarih</TableHead>
                  <TableHead>Summary</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((h) => (
                  <TableRow key={h.config_version_id + h.created_at}>
                    <TableCell className="font-mono text-xs">
                      {h.config_version_id.slice(0, 8)}
                    </TableCell>
                    <TableCell className="text-xs">
                      <Badge variant={h.source === 'override' ? 'default' : 'outline'}>{h.source}</Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(h.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-xs max-w-xs truncate">{h.summary || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={overrideOpen} onOpenChange={setOverrideOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Override Paytable JSON</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 mt-2">
            <Textarea
              className="font-mono text-xs h-72"
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
            />
            <p className="text-[10px] text-muted-foreground">
              Geçerli bir JSON olmalı ve en az bir sembol içermelidir (symbols array).
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOverrideOpen(false)}>
              İptal
            </Button>
            <Button onClick={handleSaveOverride} disabled={saving}>
              {saving ? 'Saving...' : 'Save Override'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GamePaytableTab;
