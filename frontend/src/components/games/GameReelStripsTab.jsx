import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { Upload, Save, FlaskConical } from 'lucide-react';
import api from '../../services/api';

const parseReelsFromText = (text) => {
  const lines = text
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);
  return lines.map((line) =>
    line
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
  );
};

const formatReelsToText = (reels) => {
  if (!Array.isArray(reels)) return '';
  return reels.map((r) => (Array.isArray(r) ? r.join(',') : '')).join('\n');
};

const GameReelStripsTab = ({ game }) => {
  const [loading, setLoading] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [simulateLoading, setSimulateLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);

  const [current, setCurrent] = useState(null);
  const [history, setHistory] = useState([]);
  const [reelText, setReelText] = useState('');

  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importFormat, setImportFormat] = useState('json');
  const [importContent, setImportContent] = useState('');

  const loadData = async () => {
    if (!game) return;
    setLoading(true);
    try {
      const res = await api.get(`/v1/games/${game.id}/config/reel-strips`);
      const data = res.data || {};
      setCurrent(data.current || null);
      setHistory(data.history || []);

      const reels = data.current?.data?.reels || [];
      setReelText(formatReelsToText(reels));
    } catch (err) {
      console.error(err);
      toast.error('Reel strips yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [game?.id]);

  const handleSave = async () => {
    if (!game) return;
    setSaveLoading(true);
    try {
      const reels = parseReelsFromText(reelText);
      const payload = {
        data: {
          layout: {
            reels: reels.length,
            rows: null,
          },
          reels,
        },
        source: 'manual',
        summary: 'Updated from UI',
      };
      const res = await api.post(`/v1/games/${game.id}/config/reel-strips`, payload);
      toast.success('Reel strips kaydedildi');
      setCurrent(res.data);
      await loadData();
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      const msg = apiError?.message || apiError?.detail || 'Reel strips kaydedilemedi';
      toast.error(msg);
    } finally {
      setSaveLoading(false);
    }
  };

  const handleFileImport = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const ext = file.name.toLowerCase().endsWith('.csv') ? 'csv' : 'json';
    setImportFormat(ext);

    const reader = new FileReader();
    reader.onload = () => {
      setImportContent(reader.result?.toString() || '');
      setImportDialogOpen(true);
    };
    reader.onerror = () => {
      toast.error('Dosya okunamadı');
    };
    reader.readAsText(file);
  };

  const handleConfirmImport = async () => {
    if (!game || !importContent) return;
    setImportLoading(true);
    try {
      const res = await api.post(`/v1/games/${game.id}/config/reel-strips/import`, {
        format: importFormat,
        content: importContent,
      });
      toast.success('Reel strips imported');
      setImportDialogOpen(false);
      setCurrent(res.data);
      await loadData();
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      const msg = apiError?.message || apiError?.detail || 'Import başarısız';
      toast.error(msg);
    } finally {
      setImportLoading(false);
    }
  };

  const handleSimulate = async () => {
    if (!game) return;
    setSimulateLoading(true);
    try {
      const res = await api.post(`/v1/games/${game.id}/config/reel-strips/simulate`, {
        rounds: 10000,
        bet: 1.0,
      });
      toast.success(`Simulation triggered (stub). ID: ${res.data?.simulation_id}`);
    } catch (err) {
      console.error(err);
      toast.error('Simulation tetiklenemedi');
    } finally {
      setSimulateLoading(false);
    }
  };

  const reelsCount = current?.data?.layout?.reels || (current?.data?.reels?.length ?? 0);
  const rows = current?.data?.layout?.rows ?? null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant={current?.source === 'import' ? 'secondary' : 'default'}>
              {current?.source || 'manual'}
            </Badge>
            {current && (
              <span className="text-xs text-muted-foreground">
                v{current.config_version_id?.slice(0, 8)} • {current.created_by} •{' '}
                {new Date(current.created_at).toLocaleString()}
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            {reelsCount ? `${reelsCount} reels` : 'No reels configured'}
            {rows ? ` • ${rows} rows` : ''}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="inline-flex items-center gap-2 cursor-pointer text-xs text-muted-foreground">
            <Upload className="w-4 h-4" />
            <span>Import (JSON/CSV)</span>
            <Input type="file" accept=".json,.csv" className="hidden" onChange={handleFileImport} />
          </label>
          <Button size="sm" variant="outline" onClick={handleSimulate} disabled={simulateLoading}>
            <FlaskConical className="w-4 h-4 mr-1" />
            {simulateLoading ? 'Simulating...' : 'Simulate 10.000 Spins'}
          </Button>
          <Button size="sm" onClick={handleSave} disabled={saveLoading}>
            <Save className="w-4 h-4 mr-1" />
            {saveLoading ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Reel Editor</CardTitle>
          <CardDescription>
            Her satır bir reel, semboller virgülle ayrılmıştır. Örnek: A,K,Q,J,9,WILD,SCATTER
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            className="font-mono text-xs h-64"
            value={reelText}
            onChange={(e) => setReelText(e.target.value)}
            placeholder={"A,K,Q,J,9\nA,K,Q,10,9"}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Reel Strips History</CardTitle>
          <CardDescription>Son değişikliklerin özeti.</CardDescription>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <div className="text-xs text-muted-foreground">Henüz reel strips geçmişi yok.</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Version</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Schema</TableHead>
                  <TableHead>Tarih</TableHead>
                  <TableHead>Summary</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((h) => (
                  <TableRow key={h.config_version_id + h.created_at}>
                    <TableCell className="font-mono text-xs">{h.config_version_id.slice(0, 8)}</TableCell>
                    <TableCell className="text-xs">
                      <Badge variant={h.source === 'import' ? 'secondary' : 'outline'}>{h.source}</Badge>
                    </TableCell>
                    <TableCell className="text-xs">{h.schema_version}</TableCell>
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

      <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Import Reel Strips ({importFormat.toUpperCase()})</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 mt-2">
            <Textarea
              className="font-mono text-xs h-72"
              value={importContent}
              onChange={(e) => setImportContent(e.target.value)}
            />
            <p className="text-[10px] text-muted-foreground">
              JSON için doğrudan data objesi, CSV için her satır bir reel olacak şekilde virgülle ayrılmış semboller.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setImportDialogOpen(false)}>
              İptal
            </Button>
            <Button onClick={handleConfirmImport} disabled={importLoading}>
              {importLoading ? 'Importing...' : 'Import'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GameReelStripsTab;
