import React, { useCallback, useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Crown, Plus, Trash2, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';

const VipGames = () => {
  const [vipGames, setVipGames] = useState([]);
  const [allGames, setAllGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [search, setSearch] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const res = await api.get('/v1/games');
      // Handle both Array and Paginated Response
      const all = Array.isArray(res.data) ? res.data : (res.data.items || []);
      setAllGames(all);
      setVipGames(all.filter(g => g.tags && g.tags.includes('VIP')));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const toggleVipStatus = async (game, isVip) => {
    try {
        const currentTags = game.tags || [];
        let newTags;
        if (isVip) {
            if (currentTags.includes('VIP')) return;
            newTags = [...currentTags, 'VIP'];
        } else {
            newTags = currentTags.filter(t => t !== 'VIP');
        }
        
        await api.put(`/v1/games/${game.id}/details`, { tags: newTags });
        toast.success(isVip ? "Added to VIP" : "Removed from VIP");
        fetchData();
    } catch (err) {
        toast.error("Failed to update status");
    }
  };

  const filteredCandidates = allGames.filter(g => 
    !g.tags?.includes('VIP') && 
    g.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
        <div className="flex justify-between items-center">
            <div>
                <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                    <Crown className="w-8 h-8 text-yellow-500" /> VIP Games
                </h2>
                <p className="text-muted-foreground">Manage exclusive games for high-value players.</p>
            </div>
            
            <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                <DialogTrigger asChild>
                    <Button className="bg-yellow-600 hover:bg-yellow-700 text-white">
                        <Plus className="w-4 h-4 mr-2" /> Add VIP Game
                    </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Select Games to Mark as VIP</DialogTitle>
                        <div className="pt-2">
                            <div className="relative">
                                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input placeholder="Search games..." className="pl-8" value={search} onChange={e => setSearch(e.target.value)} />
                            </div>
                        </div>
                    </DialogHeader>
                    <div className="space-y-2 mt-2">
                        {filteredCandidates.length === 0 && <div className="text-center py-4 text-muted-foreground">No games found.</div>}
                        {filteredCandidates.map(g => (
                            <div key={g.id} className="flex justify-between items-center p-3 border rounded hover:bg-secondary/50">
                                <div>
                                    <div className="font-medium">{g.name}</div>
                                    <div className="text-xs text-muted-foreground">{g.provider}</div>
                                </div>
                                <Button size="sm" variant="outline" onClick={() => toggleVipStatus(g, true)}>Add</Button>
                            </div>
                        ))}
                    </div>
                </DialogContent>
            </Dialog>
        </div>

        <Card className="border-t-4 border-t-yellow-500">
            <CardHeader>
                <CardTitle>Exclusive VIP Collection</CardTitle>
                <CardDescription>These games are highlighted in the VIP Lobby.</CardDescription>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Game Name</TableHead>
                            <TableHead>Provider</TableHead>
                            <TableHead>Category</TableHead>
                            <TableHead>RTP</TableHead>
                            <TableHead className="text-right">Action</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {vipGames.length === 0 && (
                            <TableRow><TableCell colSpan={5} className="text-center py-10 text-muted-foreground">No VIP games assigned yet.</TableCell></TableRow>
                        )}
                        {vipGames.map(game => (
                            <TableRow key={game.id}>
                                <TableCell className="font-medium flex items-center gap-2">
                                    <Crown className="w-3 h-3 text-yellow-500" />
                                    {game.name}
                                </TableCell>
                                <TableCell>{game.provider}</TableCell>
                                <TableCell><Badge variant="secondary">{game.category}</Badge></TableCell>
                                <TableCell>{game.configuration?.rtp}%</TableCell>
                                <TableCell className="text-right">
                                    <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-700 hover:bg-red-100/10" onClick={() => toggleVipStatus(game, false)}>
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
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

export default VipGames;
