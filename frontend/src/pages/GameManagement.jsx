import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { Plus, Settings2, Upload, Server, Table as TableIcon, LayoutGrid, Database, List } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';

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
  const [tableForm, setTableForm] = useState({ name: '', provider: '', min_bet: 5, max_bet: 500, game_type: 'Blackjack', table_type: 'standard' });
  const [uploadForm, setUploadForm] = useState({ provider: 'Pragmatic Play', method: 'fetch_api' });

  const fetchAll = async () => {
    try {
        const [gRes, tRes] = await Promise.all([api.get('/v1/games'), api.get('/v1/tables')]);
        setGames(gRes.data);
        setTables(tRes.data);
    } catch (err) { console.error(err); } finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleToggleGame = async (id) => {
    try { await api.post(`/v1/games/${id}/toggle`); fetchAll(); toast.success("Updated"); } catch { toast.error("Failed"); }
  };

  const handleToggleTable = async (id, currentStatus) => {
    const newStatus = currentStatus === 'online' ? 'maintenance' : 'online';
    try { await api.post(`/v1/tables/${id}/status`, { status: newStatus }); fetchAll(); toast.success("Updated"); } catch { toast.error("Failed"); }
  };

  const openConfig = (game) => {
    setSelectedGame(game);
    setConfigForm(game.configuration || { rtp: 96.0, volatility: 'medium' });
    setIsConfigOpen(true);
  };

  const handleSaveConfig = async () => {
    try {
        await api.put(`/v1/games/${selectedGame.id}`, configForm);
        setIsConfigOpen(false);
        fetchAll();
        toast.success("Configuration Saved");
    } catch { toast.error("Failed to save"); }
  };

  const handleCreateTable = async () => {
    try {
        await api.post('/v1/tables', tableForm);
        setIsTableOpen(false);
        fetchAll();
        toast.success("Table Created");
    } catch { toast.error("Failed to create table"); }
  };

  const handleUpload = async () => {
    try {
        const res = await api.post('/v1/games/upload', uploadForm);
        setIsUploadOpen(false);
        fetchAll();
        toast.success(res.data.message);
    } catch { toast.error("Upload failed"); }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Game Operations</h2>
        
        <Tabs defaultValue="games" className="w-full">
            <TabsList>
                <TabsTrigger value="games"><LayoutGrid className="w-4 h-4 mr-2" /> Slots & Games</TabsTrigger>
                <TabsTrigger value="tables"><TableIcon className="w-4 h-4 mr-2" /> Live Tables</TabsTrigger>
                <TabsTrigger value="upload"><Upload className="w-4 h-4 mr-2" /> Upload & Import</TabsTrigger>
            </TabsList>

            {/* --- SLOTS & GAMES TAB --- */}
            <TabsContent value="games" className="mt-4">
                <Card>
                    <CardContent className="pt-6">
                        <Table>
                            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Provider</TableHead><TableHead>RTP</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {games.map(game => (
                                    <TableRow key={game.id}>
                                        <TableCell className="font-medium">{game.name}</TableCell>
                                        <TableCell>{game.provider}</TableCell>
                                        <TableCell>{game.configuration?.rtp}%</TableCell>
                                        <TableCell><Badge variant={game.status==='active'?'default':'secondary'}>{game.status}</Badge></TableCell>
                                        <TableCell className="text-right flex justify-end gap-2">
                                            <Button size="sm" variant="outline" onClick={() => openConfig(game)}><Settings2 className="w-4 h-4 mr-1" /> Config</Button>
                                            <Switch checked={game.status==='active'} onCheckedChange={() => handleToggleGame(game.id)} />
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
                        <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> New Custom Table</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Create Custom Table</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Table Name</Label><Input value={tableForm.name} onChange={e=>setTableForm({...tableForm, name: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Provider</Label><Input value={tableForm.provider} onChange={e=>setTableForm({...tableForm, provider: e.target.value})} /></div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2"><Label>Min Bet</Label><Input type="number" value={tableForm.min_bet} onChange={e=>setTableForm({...tableForm, min_bet: e.target.value})} /></div>
                                    <div className="space-y-2"><Label>Max Bet</Label><Input type="number" value={tableForm.max_bet} onChange={e=>setTableForm({...tableForm, max_bet: e.target.value})} /></div>
                                </div>
                                <Button onClick={handleCreateTable} className="w-full">Create</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card>
                    <CardContent className="pt-6">
                        <Table>
                            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Limits</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {tables.map(table => (
                                    <TableRow key={table.id}>
                                        <TableCell>{table.name}</TableCell>
                                        <TableCell>{table.game_type}</TableCell>
                                        <TableCell>${table.min_bet} - ${table.max_bet}</TableCell>
                                        <TableCell><Badge variant={table.status==='online'?'default':'secondary'}>{table.status}</Badge></TableCell>
                                        <TableCell className="text-right">
                                            <Button size="sm" variant={table.status==='online'?'destructive':'default'} onClick={() => handleToggleTable(table.id, table.status)}>
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
                    <CardHeader><CardTitle>Game Import Wizard</CardTitle><CardDescription>Fetch games from providers or upload bundles.</CardDescription></CardHeader>
                    <CardContent className="max-w-md space-y-6">
                        <div className="space-y-2">
                            <Label>Method</Label>
                            <Select value={uploadForm.method} onValueChange={v => setUploadForm({...uploadForm, method: v})}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="fetch_api">Auto-Fetch from Provider API</SelectItem>
                                    <SelectItem value="json_upload">Manual Bundle Upload (.zip)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Provider</Label>
                            <Select value={uploadForm.provider} onValueChange={v => setUploadForm({...uploadForm, provider: v})}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Pragmatic Play">Pragmatic Play</SelectItem>
                                    <SelectItem value="Evolution">Evolution</SelectItem>
                                    <SelectItem value="NetEnt">NetEnt</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <Button onClick={handleUpload} className="w-full">
                            <Server className="w-4 h-4 mr-2" /> Start Import
                        </Button>
                    </CardContent>
                </Card>
            </TabsContent>
        </Tabs>

        {/* --- DEEP CONFIG DRAWER (MODAL) --- */}
        <Dialog open={isConfigOpen} onOpenChange={setIsConfigOpen}>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Game Settings: {selectedGame?.name}</DialogTitle>
                    <CardDescription>Advanced Configuration & Math</CardDescription>
                </DialogHeader>
                
                <Tabs defaultValue="general" className="w-full mt-4">
                    <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="general">General</TabsTrigger>
                        <TabsTrigger value="math">Math & RTP</TabsTrigger>
                        <TabsTrigger value="jackpot">Jackpots</TabsTrigger>
                        <TabsTrigger value="visuals">Assets</TabsTrigger>
                    </TabsList>

                    <TabsContent value="general" className="space-y-4 py-4">
                        <div className="space-y-2"><Label>Game ID (Readonly)</Label><Input value={selectedGame?.id} disabled /></div>
                        <div className="space-y-2"><Label>Category</Label><Input value={selectedGame?.category} disabled /></div>
                        <div className="space-y-2"><Label>Game Version</Label><Badge variant="outline">{configForm.version || "1.0.0"}</Badge></div>
                    </TabsContent>

                    <TabsContent value="math" className="space-y-4 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2"><Label>RTP (%)</Label><Input type="number" value={configForm.rtp} onChange={e => setConfigForm({...configForm, rtp: e.target.value})} /></div>
                            <div className="space-y-2">
                                <Label>Volatility</Label>
                                <Select value={configForm.volatility} onValueChange={v => setConfigForm({...configForm, volatility: v})}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent><SelectItem value="low">Low</SelectItem><SelectItem value="medium">Medium</SelectItem><SelectItem value="high">High</SelectItem></SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2"><Label>Min Bet</Label><Input type="number" value={configForm.min_bet} onChange={e => setConfigForm({...configForm, min_bet: e.target.value})} /></div>
                            <div className="space-y-2"><Label>Max Win (x)</Label><Input type="number" value={configForm.max_win_multiplier} onChange={e => setConfigForm({...configForm, max_win_multiplier: e.target.value})} /></div>
                        </div>
                        <div className="space-y-2">
                            <Label>Paytable (JSON)</Label>
                            <Textarea value={JSON.stringify(configForm.paytable || {}, null, 2)} readOnly className="font-mono text-xs" />
                            <Button variant="secondary" size="sm" className="w-full">Refresh from Provider</Button>
                        </div>
                    </TabsContent>

                    <TabsContent value="jackpot" className="space-y-4 py-4">
                        <div className="p-4 border border-dashed rounded text-center text-muted-foreground">
                            <p>Jackpot configuration available for supported games only.</p>
                        </div>
                    </TabsContent>

                    <TabsContent value="visuals" className="space-y-4 py-4">
                        <div className="space-y-2"><Label>Thumbnail URL</Label><Input value={selectedGame?.image_url || ''} /></div>
                        <div className="h-20 bg-secondary rounded flex items-center justify-center text-muted-foreground">Preview Area</div>
                    </TabsContent>
                </Tabs>

                <DialogFooter>
                    <Button onClick={handleSaveConfig}>Save Changes</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    </div>
  );
};

export default GameManagement;
