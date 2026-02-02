import React, { useCallback, useEffect, useRef, useState } from 'react';
import { LayoutGrid, Table as TableIcon, Upload, Activity, Plus, Settings2, Server, Star } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useCapabilities } from '../context/CapabilitiesContext';

import { toast } from 'sonner';
import api from '../services/api';
import GameConfigReadOnlyPanel from '../components/games/GameConfigReadOnlyPanel';

const GameManagement = () => {
  const { featureFlags, loading: capabilitiesLoading } = useCapabilities();

  const [games, setGames] = useState([]);
  const [gamesLoading, setGamesLoading] = useState(false);
  const [gamesMeta, setGamesMeta] = useState({ page: 1, page_size: 50, total: null });
  const [gamesPageSize, setGamesPageSize] = useState(50);
  const [tables, setTables] = useState([]);
  const [selectedGame, setSelectedGame] = useState(null);
  const [gameCategory, setGameCategory] = useState('all');
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isTableOpen, setIsTableOpen] = useState(false);
  const [tableForm, setTableForm] = useState({ name: '', provider: '', min_bet: 1, max_bet: 100 });

  // Non-visual state marker to help E2E validate controlled dialogs.
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.body.dataset.configOpen = isConfigOpen ? '1' : '0';
    }
  }, [isConfigOpen]);

  const [uploadForm, setUploadForm] = useState({
    method: 'fetch_api',
    provider: 'Pragmatic Play',
    file: null,
    source_label: '',
    notes: '',
    client_type: null,
    launch_url: '',
    min_version: '',
  });
  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [importLogs, setImportLogs] = useState([]); // legacy, kept for now
  const [importJob, setImportJob] = useState(null); // {id,status,total_items,total_errors,error_summary}
  const [importItems, setImportItems] = useState([]);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const fetchAll = useCallback(async (category = 'all', page = 1, pageSizeOverride) => {
    setGamesLoading(true);
    setGames([]);

    try {
      const gameParams = {};
      if (category && category !== 'all') gameParams.category = category;
      const effectivePageSize = pageSizeOverride || gamesPageSize;
      gameParams.page = page;
      gameParams.page_size = effectivePageSize;

      const [gamesRes, tablesRes] = await Promise.all([
        api.get('/v1/games', { params: gameParams }),
        api.get('/v1/tables'),
      ]);
      const data = gamesRes.data || {};
      setGames(data.items || []);
      setGamesMeta(data.meta || { page, page_size: effectivePageSize, total: null });
      setTables(tablesRes.data || []);
    } catch (err) {
      const status = err?.response?.status;
      if (status === 500 || status === 502 || status === 503) {
        toast.error('Service unavailable', {
          description: 'Veritabanına şu an ulaşılamıyor, lütfen az sonra tekrar deneyin.',
        });
      } else {
        toast.error('Failed to load games');
      }
    } finally {
      setGamesLoading(false);
    }
  }, [gamesPageSize]);

  useEffect(() => {
    fetchAll(gameCategory, 1);
  }, [fetchAll, gameCategory]);

  const handleToggleGame = async (gameId) => {
    try {
      await api.post(`/v1/games/${gameId}/toggle`);
      fetchAll();
    } catch (err) {
      const status = err?.response?.status;
      const code = err?.standardized?.code;

      // P2-GO-BE-02: Prefer error_code, fallback to status.
      if (code === 'FORBIDDEN' || status === 403) {
        toast.error("You don't have permission");
        return;
      }

      if (code === 'FEATURE_NOT_IMPLEMENTED' || status === 501) {
        toast.info('Not implemented', {
          description: 'This operation is not implemented yet.',
        });
        return;
      }

      if (status === 404) {
        // Should be rare for toggle after backend normalization, but keep safe fallback.
        toast.info('Toggle unavailable', {
          description: 'Not implemented in this environment (or game not found).',
        });
        return;
      }

      if (code === 'UNAUTHORIZED' || status === 401) {
        toast.warning('Unauthorized', {
          description: 'Session invalid. Please sign in again.',
        });
        return;
      }

      toast.error(
        `Failed${status ? ` (${status})` : ''}`,
        { description: err?.standardized?.message || err?.message }
      );
    }
  };

  const openConfig = (game) => {
    // P2-GO-BE-01 alignment: Config modal should always be able to open.
    // Any unavailable/provider-missing fields are handled as read-only in the panel.
    setSelectedGame(game);
    setIsConfigOpen(true);
  };

  const handleCreateTable = async () => {
    try {
      await api.post('/v1/tables', tableForm);
      setIsTableOpen(false);
      fetchAll();
      toast.success('Table Created');
    } catch {
      toast.error('Failed to create table');
    }
  };

  const pollJobUntil = useCallback(async (jobId, { untilStatuses, maxMs = 60000 }) => {
    const started = Date.now();

    while (Date.now() - started < maxMs) {
      const res = await api.get(`/v1/game-import/jobs/${jobId}`);
      const status = res.data?.status;

      setImportJob({
        id: res.data?.job_id,
        status,
        total_items: res.data?.total_items,
        total_errors: res.data?.total_errors,
        error_summary: res.data?.error_summary,
      });
      setImportItems(res.data?.items || []);

      if (untilStatuses.includes(status)) {
        return res.data;
      }

      // Keep UI responsive
      await new Promise((r) => setTimeout(r, 800));
    }

    throw new Error('JOB_POLL_TIMEOUT');
  }, []);

  const handleUpload = async () => {
    if (isImporting) return;

    setIsImporting(true);
    setImportProgress(0);
    setImportLogs([]);
    setImportJob(null);
    setImportItems([]);
    setIsPreviewOpen(false);

    try {
      // --- Provider auto-fetch flow is out of scope; keep UX but avoid broken endpoint.
      if (uploadForm.method === 'fetch_api') {
        toast.info('Coming soon', {
          description: 'Auto-fetch from provider API is not implemented yet. Please use manual upload.',
        });
        return;
      }

      // --- Manual JSON/ZIP upload
      const file = uploadForm.file;
      if (!file) {
        toast.error('Missing file', { description: 'Please select a .json or .zip file.' });
        return;
      }

      const name = (file.name || '').toLowerCase();
      const isZip = name.endsWith('.zip');
      const isJson = name.endsWith('.json');
      if (!isZip && !isJson) {
        toast.error('Geçersiz Dosya Formatı', { description: 'Sadece .zip veya .json yükleyebilirsiniz.' });
        return;
      }

      setImportProgress(15);

      const formData = new FormData();
      formData.append('file', file);

      const uploadRes = await api.post('/v1/game-import/manual/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const jobId = uploadRes.data?.job_id;
      if (!jobId) {
        throw new Error('MISSING_JOB_ID');
      }

      setImportProgress(35);

      const jobData = await pollJobUntil(jobId, { untilStatuses: ['ready', 'failed'], maxMs: 60000 });

      setImportProgress(70);
      setIsPreviewOpen(true);

      if (jobData?.status === 'failed') {
        toast.error('Upload failed', { description: 'Bundle parsing/validation failed. Please review errors.' });
      } else {
        toast.success('Preview ready', { description: 'Review the preview and confirm Import.' });
      }

      setImportProgress(85);
    } catch (err) {
      const code = err?.standardized?.code || err?.response?.data?.error_code;
      const status = err?.response?.status;

      if (code === 'UNSUPPORTED_FILE') {
        toast.error('Geçersiz Dosya Formatı', { description: 'Backend bu dosya formatını desteklemiyor.' });
      } else if (code === 'UPLOAD_TOO_LARGE' || status === 413) {
        toast.error('Upload too large', { description: 'Dosya boyutu limitini aşıyor.' });
      } else if (status === 500 || status === 502 || status === 503) {
        toast.error('Service unavailable', {
          description: 'Veritabanına şu an ulaşılamıyor, lütfen az sonra tekrar deneyin.',
        });
      } else {
        toast.error('Upload failed');
      }

      setImportProgress(0);
    } finally {
      setIsImporting(false);
    }
  };

  const handleManualImportConfirm = async () => {
    if (!importJob?.id) return;

    try {
      setIsImporting(true);
      setImportProgress((p) => (p < 80 ? 80 : p));

      const res = await api.post(`/v1/game-import/jobs/${importJob.id}/import`);

      // Import endpoint is synchronous; still fetch job for final status.
      await pollJobUntil(importJob.id, { untilStatuses: ['completed', 'failed'], maxMs: 60000 });

      setImportProgress(100);

      toast.success('Import completed', {
        description: `Imported: ${res.data?.imported_count ?? 0}`,
      });

      setIsPreviewOpen(false);
      setImportJob(null);
      setImportItems([]);

      await fetchAll(gameCategory, 1);
    } catch (err) {
      const code = err?.standardized?.code || err?.response?.data?.error_code;
      const status = err?.response?.status;

      if (code === 'JOB_NOT_READY' || status === 409) {
        toast.error('Job not ready', { description: 'Preview is not ready yet. Please wait.' });
      } else if (status === 500 || status === 502 || status === 503) {
        toast.error('Service unavailable', {
          description: 'Veritabanına şu an ulaşılamıyor, lütfen az sonra tekrar deneyin.',
        });
      } else {
        toast.error('Manual import failed');
      }

      setImportProgress(0);
    } finally {
      setIsImporting(false);
    }
  };

  if (capabilitiesLoading) {
    return (
      <div className="p-6">
        <div className="text-sm text-muted-foreground">Loading capabilities…</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mt-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Category filter:</span>
          <Select
            value={gameCategory}
            onValueChange={(v) => setGameCategory(v)}
          >
            <SelectTrigger className="w-32 h-7 text-xs">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="Slot">Slot</SelectItem>
              <SelectItem value="Crash">Crash</SelectItem>
              <SelectItem value="Dice">Dice</SelectItem>
              <SelectItem value="TABLE_POKER">Table Poker</SelectItem>
              <SelectItem value="TABLE_BLACKJACK">Table Blackjack</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <h2 className="text-3xl font-bold tracking-tight">Game Operations</h2>

      <Tabs defaultValue="games" className="w-full">
        <TabsList>
          <TabsTrigger value="games">
            <LayoutGrid className="w-4 h-4 mr-2" /> Slots &amp; Games
          </TabsTrigger>
          <TabsTrigger value="tables">
            <TableIcon className="w-4 h-4 mr-2" /> Live Tables
          </TabsTrigger>
          <TabsTrigger value="upload">
            <Upload className="w-4 h-4 mr-2" /> Upload &amp; Import
          </TabsTrigger>
        </TabsList>

        {/* --- SLOTS & GAMES TAB --- */}
        <TabsContent value="games" className="mt-4">
          <Card>
            <CardContent className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Provider</TableHead>
                    <TableHead>RTP</TableHead>
                    <TableHead>Lifecycle</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {games.map((game) => (
                    <TableRow key={game.id}>
                      <TableCell>
                        <div className="font-medium flex items-center gap-2">
                          {game.is_special_game && (
                            <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
                          )}
                          {game.name}
                        </div>
                        {game.suggestion_reason && (
                          <div className="text-[10px] text-orange-500">{game.suggestion_reason}</div>
                        )}
                      </TableCell>
                      <TableCell>{game.provider}</TableCell>
                      <TableCell>{game.configuration?.rtp ?? '-'}%</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="uppercase text-[10px]">
                          {game.business_status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            game.runtime_status === 'online'
                              ? 'default'
                              : game.runtime_status === 'maintenance'
                              ? 'destructive'
                              : 'secondary'
                          }
                        >
                          {game.runtime_status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right flex justify-end gap-2">

                      {/* Analytics icon is intentionally disabled in this environment (P1-GO-UX-01).
                          We also prevent pointer events so no click/toast can ever fire.
                      */}

                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="inline-flex">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  disabled={!featureFlags.gamesAnalyticsEnabled}
                                  className={!featureFlags.gamesAnalyticsEnabled ? 'cursor-not-allowed opacity-50 pointer-events-none' : ''}
                                >
                                  <Activity className="w-4 h-4 text-blue-500" />
                                </Button>
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>
                                {featureFlags.gamesAnalyticsEnabled
                                  ? 'View analytics'
                                  : 'Analytics not available in this environment'}
                              </p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openConfig(game)}
                              >
                                <Settings2 className="w-4 h-4 mr-1" /> Config
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>View config (read-only snapshot)</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        <Switch
                          checked={!!game.is_active}
                          onCheckedChange={() => handleToggleGame(game.id)}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
            <div className="flex items-center justify-between px-4 py-3 border-t text-xs text-muted-foreground">
              <div>
                Page {gamesMeta.page}
                {gamesMeta.total != null && gamesMeta.page_size && (
                  <span>
                    {' '}of {Math.max(1, Math.ceil(gamesMeta.total / gamesMeta.page_size))}
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={gamesMeta.page <= 1}
                  onClick={() => {
                    const prevPage = (gamesMeta.page || 1) - 1;
                    if (prevPage < 1) return;
                    fetchAll(gameCategory, prevPage).then(() => {
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    });
                  }}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={games.length < (gamesMeta.page_size || gamesPageSize)}
                  onClick={() => {
                    const nextPage = (gamesMeta.page || 1) + 1;
                    fetchAll(gameCategory, nextPage).then(() => {
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    });
                  }}
                >
                  Next
                </Button>
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* --- CUSTOM TABLES TAB --- */}
        <TabsContent value="tables" className="mt-4">
          <div className="flex justify-end mb-4">
            <Dialog open={isTableOpen} onOpenChange={setIsTableOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" /> New Custom Table
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Custom Table</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Table Name</Label>
                    <Input
                      value={tableForm.name}
                      onChange={(e) => setTableForm({ ...tableForm, name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Provider</Label>
                    <Input
                      value={tableForm.provider}
                      onChange={(e) => setTableForm({ ...tableForm, provider: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Min Bet</Label>
                      <Input
                        type="number"
                        value={tableForm.min_bet}
                        onChange={(e) => setTableForm({ ...tableForm, min_bet: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Max Bet</Label>
                      <Input
                        type="number"
                        value={tableForm.max_bet}
                        onChange={(e) => setTableForm({ ...tableForm, max_bet: e.target.value })}
                      />
                    </div>
                  </div>
                  <Button onClick={handleCreateTable} className="w-full">
                    Create
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          <Card>
            <CardContent className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Limits</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tables.map((table) => (
                    <TableRow key={table.id}>
                      <TableCell>{table.name}</TableCell>
                      <TableCell>{table.game_type}</TableCell>
                      <TableCell>
                        ${table.min_bet} - ${table.max_bet}
                      </TableCell>
                      <TableCell>
                        <Badge variant={table.status === 'online' ? 'default' : 'secondary'}>
                          {table.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {/* TODO: implement handleToggleTable when Live Tables management is in scope */}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* --- UPLOAD TAB --- */}
        <TabsContent value="upload" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Game Import Wizard</CardTitle>
              <CardDescription>Fetch games from providers or upload bundles.</CardDescription>
            </CardHeader>
            <CardContent className="max-w-xl space-y-6">
              <div className="space-y-2">
                <Label>Method</Label>
                <Select
                  value={uploadForm.method}
                  onValueChange={(v) =>
                    setUploadForm({
                      ...uploadForm,
                      method: v,
                      // method değişince client & bundle alanlarını resetle
                      file: null,
                      client_type: v === 'html5_upload' ? 'html5' : v === 'unity_upload' ? 'unity' : null,
                      launch_url: '',
                      min_version: '',
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fetch_api">Auto-Fetch from Provider API</SelectItem>
                    <SelectItem value="html5_upload">Upload HTML5 Game Bundle</SelectItem>
                    <SelectItem value="unity_upload">Upload Unity WebGL Bundle</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {uploadForm.method === 'fetch_api' ? (
                <div className="space-y-2">
                  <Label>Provider</Label>
                  <Select
                    value={uploadForm.provider}
                    onValueChange={(v) => setUploadForm({ ...uploadForm, provider: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Pragmatic Play">Pragmatic Play</SelectItem>
                      <SelectItem value="Evolution">Evolution</SelectItem>
                      <SelectItem value="NetEnt">NetEnt</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <>
                  {/* Client Model / Runtime */}
                  <div className="space-y-2">
                    <Label>Client Model / Runtime</Label>
                    <div className="flex gap-4 text-xs">
                      <button
                        type="button"
                        className={`px-2 py-1 rounded border ${
                          uploadForm.client_type === 'html5'
                            ? 'border-blue-500 text-blue-500'
                            : 'border-slate-700 text-slate-300'
                        }`}
                        onClick={() => setUploadForm({ ...uploadForm, client_type: 'html5' })}
                      >
                        HTML5
                      </button>
                      <button
                        type="button"
                        className={`px-2 py-1 rounded border ${
                          uploadForm.client_type === 'unity'
                            ? 'border-blue-500 text-blue-500'
                            : 'border-slate-700 text-slate-300'
                        }`}
                        onClick={() => setUploadForm({ ...uploadForm, client_type: 'unity' })}
                      >
                        Unity WebGL
                      </button>
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      Bu bilgi, import sonrası game.client_variants ve primary_client_type alanlarına yazılır.
                    </p>
                  </div>

                  {/* Bundle file */}
                  <div className="space-y-2">
                    <Label>Game Bundle File</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="file"
                        accept=".zip,.json"
                        onChange={(e) => setUploadForm({ ...uploadForm, file: e.target.files?.[0] || null })}
                      />
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      Supported: .json metadata or .zip asset bundle.
                    </p>
                  </div>

                  {/* Optional launch_url */}
                  <div className="space-y-2">
                    <Label>Launch URL (optional)</Label>
                    <Input
                      value={uploadForm.launch_url}
                      onChange={(e) => setUploadForm({ ...uploadForm, launch_url: e.target.value })}
                      placeholder="https://cdn.example.com/games/slot123/index.html"
                    />
                  </div>

                  {/* Optional min_version */}
                  <div className="space-y-2">
                    <Label>Min Client Version (optional)</Label>
                    <Input
                      value={uploadForm.min_version}
                      onChange={(e) => setUploadForm({ ...uploadForm, min_version: e.target.value })}
                      placeholder="1.0.0"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Source / Studio (optional)</Label>
                    <Input
                      value={uploadForm.source_label}
                      onChange={(e) => setUploadForm({ ...uploadForm, source_label: e.target.value })}
                      placeholder="Custom Studio X"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Notes (optional)</Label>
                    <Input
                      value={uploadForm.notes}
                      onChange={(e) => setUploadForm({ ...uploadForm, notes: e.target.value })}
                      placeholder="Any internal notes about this bundle"
                    />
                  </div>
                </>
              )}

              <Button
                onClick={handleUpload}
                className="w-full"
                disabled={
                  isImporting ||
                  (uploadForm.method !== 'fetch_api' && (!uploadForm.file || !uploadForm.client_type))
                }
              >
                {uploadForm.method === 'fetch_api' ? (
                  <Server className="w-4 h-4 mr-2" />
                ) : (
                  <Upload className="w-4 h-4 mr-2" />
                )}
                {isImporting
                  ? 'Processing...'
                  : uploadForm.method === 'fetch_api'
                  ? 'Start Import'
                  : 'Upload & Analyze'}
              </Button>

              {isImporting && (
                <div className="space-y-2 pt-2 border-t">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Status</span>
                    <span>{importProgress}%</span>
                  </div>
                  <Progress value={importProgress} className="h-2" />
                  <div className="h-24 bg-slate-950 text-green-400 p-2 text-xs font-mono overflow-auto rounded border border-slate-800">
                    {importLogs.map((l, i) => (
                      <div key={i}>{l}</div>
                    ))}
                  </div>
                </div>
              )}

              {importJob && (
                <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
                  <DialogContent className="max-w-5xl">
                    <DialogHeader>
                      <DialogTitle>Import Preview</DialogTitle>
                      <CardDescription>
                        Job #{importJob.id} • status: {importJob.status} • items: {importJob.total_items ?? '-'} • errors: {importJob.total_errors ?? 0}
                      </CardDescription>
                    </DialogHeader>

                    <div className="space-y-2">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>External ID</TableHead>
                            <TableHead>Provider</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>RTP</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Errors</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {importItems.map((item) => (
                            <TableRow key={item.id}>
                              <TableCell>{item.name || '-'}</TableCell>
                              <TableCell>{item.external_id || '-'}</TableCell>
                              <TableCell>{item.provider_id || '-'}</TableCell>
                              <TableCell>{item.type || '-'}</TableCell>
                              <TableCell>{item.rtp ?? '-'}</TableCell>
                              <TableCell>
                                <Badge
                                  variant={item.status === 'valid' ? 'default' : item.status === 'invalid' ? 'destructive' : 'secondary'}
                                  className="uppercase text-[10px]"
                                >
                                  {item.status}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-[10px] text-red-500 max-w-[180px] truncate" title={(item.errors || []).join('; ')}>
                                {(item.errors || []).length}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>

                    <DialogFooter className="flex items-center justify-between">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setIsPreviewOpen(false);
                        }}
                      >
                        Close
                      </Button>

                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          onClick={() => {
                            setImportJob(null);
                            setImportItems([]);
                            setIsPreviewOpen(false);
                          }}
                        >
                          Clear
                        </Button>
                        <Button
                          onClick={handleManualImportConfirm}
                          disabled={
                            isImporting ||
                            importJob.status !== 'ready' ||
                            (importJob.total_errors || 0) > 0 ||
                            !importItems.some((it) => it.status === 'valid')
                          }
                        >
                          Import
                        </Button>
                      </div>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              )}

              {/* Legacy inline preview removed (moved to modal) */}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* --- GAME CONFIG MODAL --- */}
      <Dialog open={isConfigOpen} onOpenChange={(open) => {
        setIsConfigOpen(open);
        if (!open) setSelectedGame(null);
      }}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Game Settings: {selectedGame?.name}</DialogTitle>
            <CardDescription>Read-only configuration snapshot (provider config may be unavailable).</CardDescription>
          </DialogHeader>

          {selectedGame && (
            <GameConfigReadOnlyPanel
              game={selectedGame}
            />
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsConfigOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GameManagement;
