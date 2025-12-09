import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { Plus } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';

const GameManagement = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newGame, setNewGame] = useState({ name: '', provider: '', category: 'Slot', rtp: 96.0 });

  const fetchGames = async () => {
    try {
        const res = await api.get('/v1/games');
        setGames(res.data);
    } catch (err) {
        console.error(err);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => { fetchGames(); }, []);

  const handleToggle = async (id) => {
    try {
        await api.post(`/v1/games/${id}/toggle`);
        fetchGames();
        toast.success("Game status updated");
    } catch (err) {
        toast.error("Failed to update status");
    }
  };

  const handleAddGame = async () => {
    try {
        await api.post('/v1/games', newGame);
        setIsAddOpen(false);
        fetchGames();
        toast.success("Game added successfully");
    } catch (err) {
        toast.error("Failed to add game");
    }
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
                    <DialogHeader>
                        <DialogTitle>Add New Game</DialogTitle>
                    </DialogHeader>
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
                        <div className="space-y-2">
                            <Label>RTP (%)</Label>
                            <Input type="number" value={newGame.rtp} onChange={e => setNewGame({...newGame, rtp: e.target.value})} />
                        </div>
                        <Button onClick={handleAddGame} className="w-full">Save Game</Button>
                    </div>
                </DialogContent>
            </Dialog>
        </div>

        <Card>
            <CardHeader><CardTitle>All Games</CardTitle></CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Provider</TableHead>
                            <TableHead>Category</TableHead>
                            <TableHead>RTP</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Action</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {games.map(game => (
                            <TableRow key={game.id}>
                                <TableCell className="font-medium">{game.name}</TableCell>
                                <TableCell>{game.provider}</TableCell>
                                <TableCell>{game.category}</TableCell>
                                <TableCell>{game.rtp}%</TableCell>
                                <TableCell>
                                    <Badge variant={game.status === 'active' ? 'default' : 'secondary'}>{game.status}</Badge>
                                </TableCell>
                                <TableCell className="text-right">
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
