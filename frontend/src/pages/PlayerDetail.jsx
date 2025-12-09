import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import { ArrowLeft, Save, Ban, CheckCircle } from 'lucide-react';

const PlayerDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [player, setPlayer] = useState(null);
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [pRes, gRes] = await Promise.all([
            api.get(`/v1/players/${id}`),
            api.get(`/v1/players/${id}/games`)
        ]);
        setPlayer(pRes.data);
        setGames(gRes.data);
      } catch (err) {
        toast.error("Failed to load player data");
        navigate('/players');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, navigate]);

  const handleStatusChange = async (newStatus) => {
    try {
        await api.put(`/v1/players/${id}`, { status: newStatus });
        setPlayer({ ...player, status: newStatus });
        toast.success(`Player ${newStatus}`);
    } catch (err) {
        toast.error("Failed to update status");
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!player) return <div>Player not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/players')}>
            <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
            <h2 className="text-3xl font-bold tracking-tight">{player.username}</h2>
            <p className="text-muted-foreground">{player.email} • {player.country}</p>
        </div>
        <div className="ml-auto flex gap-2">
            {player.status === 'active' ? (
                <Button variant="destructive" onClick={() => handleStatusChange('suspended')}>
                    <Ban className="w-4 h-4 mr-2" /> Suspend
                </Button>
            ) : (
                <Button variant="default" onClick={() => handleStatusChange('active')}>
                    <CheckCircle className="w-4 h-4 mr-2" /> Activate
                </Button>
            )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="md:col-span-1 h-fit">
            <CardHeader>
                <CardTitle>Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div>
                    <Label className="text-muted-foreground">Status</Label>
                    <div className="mt-1">
                        <Badge variant={player.status === 'active' ? 'default' : 'destructive'}>{player.status}</Badge>
                    </div>
                </div>
                <div>
                    <Label className="text-muted-foreground">Real Balance</Label>
                    <div className="text-2xl font-bold text-green-500">${player.balance_real.toFixed(2)}</div>
                </div>
                <div>
                    <Label className="text-muted-foreground">Bonus Balance</Label>
                    <div className="text-xl font-bold text-yellow-500">${player.balance_bonus.toFixed(2)}</div>
                </div>
                <div>
                    <Label className="text-muted-foreground">Risk Score</Label>
                    <div className="mt-1">
                        <Badge variant={player.risk_score === 'high' ? 'destructive' : 'outline'}>{player.risk_score}</Badge>
                    </div>
                </div>
                <div>
                    <Label className="text-muted-foreground">VIP Level</Label>
                    <div className="text-lg font-medium">Level {player.vip_level}</div>
                </div>
            </CardContent>
        </Card>

        <div className="md:col-span-3">
            <Tabs defaultValue="profile">
                <TabsList>
                    <TabsTrigger value="profile">Profile</TabsTrigger>
                    <TabsTrigger value="kyc">KYC</TabsTrigger>
                    <TabsTrigger value="games">Game History</TabsTrigger>
                    <TabsTrigger value="logs">Logs</TabsTrigger>
                </TabsList>
                
                <TabsContent value="profile" className="space-y-4 mt-4">
                    <Card>
                        <CardHeader><CardTitle>Personal Information</CardTitle></CardHeader>
                        <CardContent className="grid gap-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Username</Label>
                                    <Input value={player.username} readOnly />
                                </div>
                                <div className="space-y-2">
                                    <Label>Email</Label>
                                    <Input value={player.email} readOnly />
                                </div>
                                <div className="space-y-2">
                                    <Label>Phone</Label>
                                    <Input value={player.phone || '-'} readOnly />
                                </div>
                                <div className="space-y-2">
                                    <Label>Country</Label>
                                    <Input value={player.country} readOnly />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="kyc" className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>KYC Documents</CardTitle>
                            <CardDescription>Status: <span className="font-bold uppercase">{player.kyc_status}</span></CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="text-center py-10 text-muted-foreground">
                                No documents uploaded yet.
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="games" className="mt-4">
                    <Card>
                        <CardHeader><CardTitle>Recent Gameplay</CardTitle></CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Game</TableHead>
                                        <TableHead>Provider</TableHead>
                                        <TableHead>Time</TableHead>
                                        <TableHead className="text-right">Bet</TableHead>
                                        <TableHead className="text-right">Win</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {games.map((g, i) => (
                                        <TableRow key={i}>
                                            <TableCell className="font-medium">{g.game}</TableCell>
                                            <TableCell>{g.provider}</TableCell>
                                            <TableCell className="text-muted-foreground">{new Date(g.time).toLocaleTimeString()}</TableCell>
                                            <TableCell className="text-right text-red-400">-${g.bet}</TableCell>
                                            <TableCell className="text-right text-green-400">+${g.win}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>
                
                <TabsContent value="logs" className="mt-4">
                     <Card>
                        <CardHeader><CardTitle>Activity Logs</CardTitle></CardHeader>
                        <CardContent>
                            <p className="text-muted-foreground">Login from IP 192.168.1.1 at {new Date().toLocaleString()}</p>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
      </div>
    </div>
  );
};

export default PlayerDetail;
