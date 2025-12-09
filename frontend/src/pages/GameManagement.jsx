import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { Plus, Settings2 } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

const GameManagement = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [selectedGame, setSelectedGame] = useState(null);
  
  const [newGame, setNewGame] = useState({ name: '', provider: '', category: 'Slot', rtp: 96.0 });
  
  // Game Config State
  const [configForm, setConfigForm] = useState({
    rtp: 96.0,
    volatility: 'medium',
    min_bet: 0.1,
    max_bet: 100,
    max_win_multiplier: 5000,
    paytable_id: 'standard'
  });

  const fetchGames = async () => {
    try {
        const res = await api.get('/v1/games');
        setGames(res.data);
    } catch (err) { console.error(err); } finally { setLoading(false); }
  };

  useEffect(() => { fetchGames(); }, []);

  const handleToggle = async (id) => {
    try {
        await api.post(`/v1/games/${id}/toggle`);
        fetchGames();
        toast.success("Game status updated");
    } catch (err) { toast.error("Failed to update status"); }
  };

  const handleAddGame = async () => {
    try {
        await api.post('/v1/games', newGame);
        setIsAddOpen(false);
        fetchGames();
        toast.success("Game added successfully");
    } catch (err) { toast.error("Failed to add game"); }
  };

  const openConfig = (game) => {
    setSelectedGame(game);
    // Fill form with existing config if present, or defaults
    const conf = game.configuration || {};
    setConfigForm({
        rtp: conf.rtp || 96.0,
        volatility: conf.volatility || 'medium',
        min_bet: conf.min_bet || 0.1,
        max_bet: conf.max_bet || 100,
        max_win_multiplier: conf.max_win_multiplier || 5000,
        paytable_id: conf.paytable_id || 'standard'
    });
    setIsConfigOpen(true);
  };

  const handleSaveConfig = async () => {
    try {
        await api.put(`/v1/games/${selectedGame.id}`, configForm);
        setIsConfigOpen(false);
        fetchGames();
        toast.success("Game Configuration Saved");
    } catch (err) { toast.error("Failed to save config"); }
  };

  return (
    <div className="space-y-6">
        <div className="flex justify-between items-center">
            <h2 className="text-3xl font-bold tracking-tight">Game Management</h2>
            <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                <DialogTrigger asChild>
                    <Button><Plus className="w-4 h-4 mr-2" /> Add Game</Button>
                </DialogTrigger>
                <DialogContent>
                    <DialogHeader><DialogTitle>Add New Game</DialogTitle></DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Game Name</Label>
                            <Input value={newGame.name} onChange={e => setNewGame({...newGame, name: e.target.value})} />
                        </div>
                        <div className="space-y-2">
                            <Label>Provider</Label>
                            <Input value={newGame.provider} onChange={e => setNewGame({...newGame, provider: e.target.value})} />
                        </div>
                        <div className="space-y-2">
                            <Label>Category</Label>
                            <Input value={newGame.category} onChange={e => setNewGame({...newGame, category: e.target.value})} />
                        </div>
                        <Button onClick={handleAddGame} className="w-full">Save Game</Button>
                    </div>
                </DialogContent>
            </Dialog>
        </div>

        {/* Config Dialog */}
        <Dialog open={isConfigOpen} onOpenChange={setIsConfigOpen}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle>Configure: {selectedGame?.name}</DialogTitle>
                    <CardDescription>Internal Game Math & Settings</CardDescription>
                </DialogHeader>
                <div className="grid grid-cols-2 gap-4 py-4">
                    <div className="space-y-2">
                        <Label>RTP (%)</Label>
                        <Input type="number" value={configForm.rtp} onChange={e => setConfigForm({...configForm, rtp: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                        <Label>Volatility</Label>
                        <Select value={configForm.volatility} onValueChange={v => setConfigForm({...configForm, volatility: v})}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="low">Low</SelectItem>
                                <SelectItem value="medium">Medium</SelectItem>
                                <SelectItem value="high">High</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="space-y-2">
                        <Label>Min Bet ($)</Label>
                        <Input type="number" value={configForm.min_bet} onChange={e => setConfigForm({...configForm, min_bet: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                        <Label>Max Bet ($)</Label>
                        <Input type="number" value={configForm.max_bet} onChange={e => setConfigForm({...configForm, max_bet: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                        <Label>Max Win (x)</Label>
                        <Input type="number" value={configForm.max_win_multiplier} onChange={e => setConfigForm({...configForm, max_win_multiplier: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                        <Label>Paytable ID</Label>
                        <Input value={configForm.paytable_id} onChange={e => setConfigForm({...configForm, paytable_id: e.target.value})} />
                    </div>
                </div>
                <DialogFooter>
                    <Button onClick={handleSaveConfig}>Save Configuration</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>

        <Card>
            <CardHeader><CardTitle>All Games</CardTitle></CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Provider</TableHead>
                            <TableHead>RTP</TableHead>
                            <TableHead>Volatility</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Action</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {games.map(game => (
                            <TableRow key={game.id}>
                                <TableCell className="font-medium">{game.name}</TableCell>
                                <TableCell>{game.provider}</TableCell>
                                <TableCell>{game.configuration?.rtp || '-'}</TableCell>
                                <TableCell className="capitalize">{game.configuration?.volatility || '-'}</TableCell>
                                <TableCell>
                                    <Badge variant={game.status === 'active' ? 'default' : 'secondary'}>{game.status}</Badge>
                                </TableCell>
                                <TableCell className="text-right flex justify-end gap-2">
                                    <Button size="sm" variant="outline" onClick={() => openConfig(game)}>
                                        <Settings2 className="w-4 h-4 mr-1" /> Config
                                    </Button>
                                    <Switch 
                                        checked={game.status === 'active'}
                                        onCheckedChange={() => handleToggle(game.id)}
                                    />
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    </div>
  );
};

export default GameManagement;
