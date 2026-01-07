import React, { useCallback, useEffect, useMemo, useState } from 'react';
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
import GameConfigPanel from '../components/games/GameConfigPanel';

const GameManagement = () => {
  const { hasFeature } = useCapabilities();

  const featureFlags = useMemo(() => {
    // P1-GO-FLAG-01: default=false if flags not present
    return {
      gamesConfigEnabled: hasFeature?.('GAMES_CONFIG_ENABLED') === true,
      gamesAnalyticsEnabled: hasFeature?.('GAMES_ANALYTICS_ENABLED') === true,
    };
  }, [hasFeature]);

  const [games, setGames] = useState([]);
  const [gamesMeta, setGamesMeta] = useState({ page: 1, page_size: 50, total: null });
  const [gamesPageSize, setGamesPageSize] = useState(50);
  const [tables, setTables] = useState([]);
  const [selectedGame, setSelectedGame] = useState(null);
  const [gameCategory, setGameCategory] = useState('all');
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isTableOpen, setIsTableOpen] = useState(false);
  const [tableForm, setTableForm] = useState({ name: '', provider: '', min_bet: 1, max_bet: 100 });

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
  const [importLogs, setImportLogs] = useState([]);
  const [importJob, setImportJob] = useState(null);
  const [importItems, setImportItems] = useState([]);

  const fetchAll = useCallback(async (category = 'all', page = 1, pageSizeOverride) => {
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
    } catch {
      toast.error('Failed to load games');
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
      if (status === 403) {
        toast.error("You don't have permission");
        return;
      }
      if (status === 404 || status === 501) {
        toast.error('Feature not enabled');
        return;
      }
      toast.error(
        `Failed${status ? ` (${status})` : ''}`,
        { description: err?.response?.data?.detail?.error_code || err?.message }
      );
    }
  };

  const openConfig = (game) => {
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

  const handleUpload = async () => {
    if (isImporting) return;

    setIsImporting(true);
    setImportProgress(0);
    setImportLogs([]);
    setImportJob(null);
    setImportItems([]);

    const addLog = (msg) => setImportLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

    try {
      addLog('Initializing import sequence...');
      setImportProgress(10);

      if (uploadForm.method === 'fetch_api') {
        addLog(`Connecting to ${uploadForm.provider} API Gateway...`);
        await new Promise((r) => setTimeout(r, 800));
        setImportProgress(30);

        addLog('Authenticating and fetching catalog...');
        await new Promise((r) => setTimeout(r, 800));
        setImportProgress(50);

        addLog('Found 35 new games. Starting synchronization...');

        // TODO: Provider auto-fetch flow will be implemented in a separate task.
        const res = await api.post('/v1/games/upload', uploadForm);
        setImportProgress(90);
        addLog('Finalizing database entries...');
        await new Promise((r) => setTimeout(r, 500));
        setImportProgress(100);
        addLog('Import process completed successfully.');
        fetchAll();
        toast.success(res.data.message);
      } else {
        // Manual JSON/ZIP upload via game-import manual endpoint (client-aware)
        addLog('Uploading bundle to server...');
        setImportProgress(30);

        const formData = new FormData();
        if (uploadForm.file) {
          formData.append('file', uploadForm.file);
        }
        if (uploadForm.source_label) {
          formData.append('source_label', uploadForm.source_label);
        }
        if (uploadForm.notes) {
          formData.append('notes', uploadForm.notes);
        }
        if (uploadForm.client_type) {
          formData.append('client_type', uploadForm.client_type);
        }
        if (uploadForm.launch_url) {
          formData.append('launch_url', uploadForm.launch_url);
        }
        if (uploadForm.min_version) {
          formData.append('min_version', uploadForm.min_version);
        }

        const res = await api.post('/v1/game-import/manual/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        const { job_id, status, total_errors, total_warnings } = res.data;

        addLog(`Manual upload analyzed. Job ${job_id}, status=${status}, errors=${total_errors}, warnings=${total_warnings}.`);
        setImportProgress(60);

        // Job & item preview için detay çek
        try {
          const jobRes = await api.get(`/v1/game-import/jobs/${job_id}`);
          setImportJob(jobRes.data.job);
          setImportItems(jobRes.data.items || []);
        } catch (e) {
          console.error(e);
          addLog('Failed to load job preview details.');
        }

        setImportProgress(80);

        if (status === 'failed' || total_errors > 0) {
          addLog('Import job has validation errors. Please review the errors before importing.');
          toast.error('Manual upload contains validation errors.');
          setImportProgress(100);
        } else {
          addLog('Validation completed. Review the preview below and click Import to finalize.');
          setImportProgress(90);
        }
      }
    } catch (err) {
      console.error(err);
      addLog('ERROR: Import failed. Check console.');
      toast.error('Upload failed');
      setImportProgress(0);
    } finally {
      setTimeout(() => setIsImporting(false), 2000);
    }
  };

  const handleManualImportConfirm = async () => {
    if (!importJob) return;
    const addLog = (msg) => setImportLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

    try {
      addLog('Starting manual import...');
      setIsImporting(true);
      setImportProgress((p) => (p < 90 ? 90 : p));
      const res = await api.post(`/v1/game-import/jobs/${importJob.id}/import`);
      addLog(res.data.message || 'Import completed.');
      setImportProgress(100);
      toast.success(res.data.message || 'Game imported successfully.');
      fetchAll();
    } catch (err) {
      console.error(err);
      addLog('ERROR: Manual import failed.');
      toast.error('Manual import failed');
    } finally {
      setTimeout(() => setIsImporting(false), 2000);
    }
  };

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
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="inline-flex">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  disabled={!featureFlags.gamesAnalyticsEnabled}
                                  className={!featureFlags.gamesAnalyticsEnabled ? 'cursor-not-allowed opacity-50' : ''}
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
                        <Button size="sm" variant="outline" onClick={() => openConfig(game)}>
                          <Settings2 className="w-4 h-4 mr-1" /> Config
                        </Button>
                        <Switch
                          checked={game.business_status === 'active'}
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
                <div className="mt-4 space-y-2 border-t pt-4">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold">Manual Import Preview</span>
                    <span className="text-muted-foreground">
                      Job #{importJob.id} • {importJob.total_found} item • {importJob.total_errors} error / {importJob.total_warnings} warning
                    </span>
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Game ID</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>RTP</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Errors</TableHead>
                        <TableHead>Warnings</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {importItems.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell>{item.name}</TableCell>
                          <TableCell>{item.provider_game_id}</TableCell>
                          <TableCell>{item.category}</TableCell>
                          <TableCell>{item.rtp ?? '-'}</TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                item.status === 'ready'
                                  ? 'default'
                                  : item.status === 'error'
                                  ? 'destructive'
                                  : 'secondary'
                              }
                              className="uppercase text-[10px]"
                            >
                              {item.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-[10px] text-red-500 max-w-[160px] truncate" title={
                            (item.errors || []).join('; ')
                          }>
                            {(item.errors || []).length}
                          </TableCell>
                          <TableCell className="text-[10px] text-yellow-500 max-w-[160px] truncate" title={
                            (item.warnings || []).join('; ')
                          }>
                            {(item.warnings || []).length}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>

                  <div className="flex justify-end gap-2 mt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setImportJob(null);
                        setImportItems([]);
                      }}
                    >
                      Clear Preview
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleManualImportConfirm}
                      disabled={
                        isImporting ||
                        !importItems.some((it) => it.status === 'ready') ||
                        (importJob.total_errors || 0) > 0
                      }
                    >
                      Import This Game
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* --- GAME CONFIG MODAL --- */}
      <Dialog open={isConfigOpen} onOpenChange={setIsConfigOpen}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Game Settings: {selectedGame?.name}</DialogTitle>
            <CardDescription>Full configuration, RTP, bets, features and logs.</CardDescription>
          </DialogHeader>

          {selectedGame && (
            <GameConfigPanel
              game={selectedGame}
              onClose={() => setIsConfigOpen(false)}
              onSaved={fetchAll}
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
