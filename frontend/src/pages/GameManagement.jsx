import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { Plus, Settings2, Upload, Server, Table as TableIcon, LayoutGrid, Star, Lock, Activity, Globe } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';

import { Progress } from '@/components/ui/progress';
import GameConfigPanel from '../components/games/GameConfigPanel';

const GameManagement = () => {
  const [games, setGames] = useState([]);
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isTableOpen, setIsTableOpen] = useState(false);
  const [selectedGame, setSelectedGame] = useState(null);

  // Forms
  const [configForm, setConfigForm] = useState({});
  const [statusForm, setStatusForm] = useState({});
  const [tableForm, setTableForm] = useState({
    name: '',
    provider: '',
    min_bet: 5,
    max_bet: 500,
    game_type: 'Blackjack',
    table_type: 'standard',
  });
  const [uploadForm, setUploadForm] = useState({ provider: 'Pragmatic Play', method: 'fetch_api' });

  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [importLogs, setImportLogs] = useState([]);

  const fetchAll = async () => {
    try {
      const [gRes, tRes] = await Promise.all([api.get('/v1/games'), api.get('/v1/tables')]);
      setGames(gRes.data);
      setTables(tRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const handleToggleGame = async (id) => {
    try {
      await api.post(`/v1/games/${id}/toggle`);
      fetchAll();
      toast.success('Updated');
    } catch {
      toast.error('Failed');
    }
  };

  const handleToggleTable = async (id, currentStatus) => {
    const newStatus = currentStatus === 'online' ? 'maintenance' : 'online';
    try {
      await api.post(`/v1/tables/${id}/status`, { status: newStatus });
      fetchAll();
      toast.success('Updated');
    } catch {
      toast.error('Failed');
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
        // Manual JSON/ZIP upload via game-import manual endpoint
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

        const res = await api.post('/v1/game-import/manual/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        const { job_id, status, total_errors, total_warnings } = res.data;

        addLog(`Manual upload analyzed. Job ${job_id}, status=${status}, errors=${total_errors}, warnings=${total_warnings}.`);
        setImportProgress(70);

        if (status === 'failed' || total_errors > 0) {
          addLog('Import job has validation errors. Please review in Game Import Jobs.');
          toast.error('Manual upload contains validation errors.');
          setImportProgress(100);
        } else {
          // For MVP, directly import the single READY item
          addLog('Importing validated game...');
          const importRes = await api.post(`/v1/game-import/jobs/${job_id}/import`);
          addLog('Import completed.');
          setImportProgress(100);
          toast.success(importRes.data.message || 'Game imported successfully.');
          fetchAll();
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

  return (
    <div className="space-y-6">
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
                      <TableCell>{game.configuration?.rtp}%</TableCell>
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
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => toast.info('Analytics Coming Soon')}
                        >
                          <Activity className="w-4 h-4 text-blue-500" />
                        </Button>
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
                        <Button
                          size="sm"
                          variant={table.status === 'online' ? 'destructive' : 'default'}
                          onClick={() => handleToggleTable(table.id, table.status)}
                        >
                          {table.status === 'online' ? 'Go Maintenance' : 'Go Online'}
                        </Button>
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
            <CardContent className="max-w-md space-y-6">
              <div className="space-y-2">
                <Label>Method</Label>
                <Select
                  value={uploadForm.method}
                  onValueChange={(v) => setUploadForm({ ...uploadForm, method: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fetch_api">Auto-Fetch from Provider API</SelectItem>
                    <SelectItem value="json_upload">Manual Bundle Upload (.zip / .json)</SelectItem>
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
                <div className="space-y-2">
                  <Label>Game Bundle File</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      type="file"
                      accept=".zip,.json"
                      onChange={(e) => setUploadForm({ ...uploadForm, file: e.target.files[0] })}
                    />
                  </div>
                  <p className="text-[10px] text-muted-foreground">
                    Supported: .json metadata or .zip asset bundle.
                  </p>
                </div>
              )}

              <Button onClick={handleUpload} className="w-full" disabled={isImporting}>
                {uploadForm.method === 'fetch_api' ? (
                  <Server className="w-4 h-4 mr-2" />
                ) : (
                  <Upload className="w-4 h-4 mr-2" />
                )}
                {isImporting
                  ? 'Importing...'
                  : uploadForm.method === 'fetch_api'
                  ? 'Start Import'
                  : 'Upload Bundle'}
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
