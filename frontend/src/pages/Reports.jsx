import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { BarChart3, TrendingUp, DollarSign, Users, Gamepad2, FileText, Download, Calendar, Activity } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

const Reports = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [overview, setOverview] = useState(null);
  const [financial, setFinancial] = useState([]);
  const [players, setPlayers] = useState([]);
  const [games, setGames] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [exports, setExports] = useState([]);

  const fetchData = async () => {
    try {
        if (activeTab === 'overview') setOverview((await api.get('/v1/reports/overview')).data);
        if (activeTab === 'financial') setFinancial((await api.get('/v1/reports/financial')).data);
        if (activeTab === 'players') setPlayers((await api.get('/v1/reports/players/ltv')).data);
        if (activeTab === 'games') setGames((await api.get('/v1/reports/games')).data);
        if (activeTab === 'scheduled') setSchedules((await api.get('/v1/reports/schedules')).data);
        if (activeTab === 'exports') setExports((await api.get('/v1/reports/exports')).data);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  const handleExport = async (type) => {
    try {
        await api.post('/v1/reports/exports', { type, requested_by: "admin" });
        toast.success("Export started");
        setActiveTab("exports");
    } catch { toast.error("Failed"); }
  };

  return (
    <div className="flex h-[calc(100vh-100px)]">
        {/* SIDEBAR NAVIGATION */}
        <div className="w-64 border-r bg-card p-4 space-y-2 overflow-y-auto">
            <h3 className="font-bold mb-4 flex items-center gap-2"><BarChart3 className="w-5 h-5 text-primary" /> Reports</h3>
            <Button variant={activeTab==='overview'?'secondary':'ghost'} className="w-full justify-start" onClick={()=>setActiveTab('overview')}><Activity className="w-4 h-4 mr-2" /> Overview</Button>
            <Button variant={activeTab==='financial'?'secondary':'ghost'} className="w-full justify-start" onClick={()=>setActiveTab('financial')}><DollarSign className="w-4 h-4 mr-2" /> Financial</Button>
            <Button variant={activeTab==='players'?'secondary':'ghost'} className="w-full justify-start" onClick={()=>setActiveTab('players')}><Users className="w-4 h-4 mr-2" /> Players</Button>
            <Button variant={activeTab==='games'?'secondary':'ghost'} className="w-full justify-start" onClick={()=>setActiveTab('games')}><Gamepad2 className="w-4 h-4 mr-2" /> Games</Button>
            <Button variant={activeTab==='scheduled'?'secondary':'ghost'} className="w-full justify-start" onClick={()=>setActiveTab('scheduled')}><Calendar className="w-4 h-4 mr-2" /> Scheduled</Button>
            <Button variant={activeTab==='exports'?'secondary':'ghost'} className="w-full justify-start" onClick={()=>setActiveTab('exports')}><Download className="w-4 h-4 mr-2" /> Export Center</Button>
        </div>

        {/* CONTENT AREA */}
        <ScrollArea className="flex-1 p-6">
            {activeTab === 'overview' && overview && (
                <div className="space-y-6">
                    <div className="grid grid-cols-4 gap-4">
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">GGR</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">${overview.ggr.toLocaleString()}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">NGR</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">${overview.ngr.toLocaleString()}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Players</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{overview.active_players}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Bonus Cost</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">${overview.bonus_cost.toLocaleString()}</div></CardContent></Card>
                    </div>
                    <Button onClick={() => handleExport("overview_pdf")}>Download PDF Report</Button>
                </div>
            )}

            {activeTab === 'financial' && (
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>GGR</TableHead><TableHead>NGR</TableHead><TableHead>Deposits</TableHead><TableHead>Withdrawals</TableHead></TableRow></TableHeader>
                        <TableBody>{financial.map((f, i) => (
                            <TableRow key={i}>
                                <TableCell>{f.date}</TableCell>
                                <TableCell>${f.ggr}</TableCell>
                                <TableCell>${f.ngr}</TableCell>
                                <TableCell>${f.deposits}</TableCell>
                                <TableCell>${f.withdrawals}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            )}

            {activeTab === 'players' && (
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Player ID</TableHead><TableHead>Deposits</TableHead><TableHead>Withdrawals</TableHead><TableHead>Net Revenue</TableHead><TableHead>VIP</TableHead></TableRow></TableHeader>
                        <TableBody>{players.map((p, i) => (
                            <TableRow key={i}>
                                <TableCell>{p.player_id}</TableCell>
                                <TableCell>${p.deposits}</TableCell>
                                <TableCell>${p.withdrawals}</TableCell>
                                <TableCell className="font-bold text-green-500">${p.net_revenue}</TableCell>
                                <TableCell>{p.vip}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            )}

            {activeTab === 'games' && (
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Game</TableHead><TableHead>Provider</TableHead><TableHead>Bets</TableHead><TableHead>Wins</TableHead><TableHead>GGR</TableHead></TableRow></TableHeader>
                        <TableBody>{games.map((g, i) => (
                            <TableRow key={i}>
                                <TableCell>{g.game}</TableCell>
                                <TableCell>{g.provider}</TableCell>
                                <TableCell>${g.bets.toLocaleString()}</TableCell>
                                <TableCell>${g.wins.toLocaleString()}</TableCell>
                                <TableCell className="font-bold">${g.ggr.toLocaleString()}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            )}

            {activeTab === 'exports' && (
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Export ID</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>Link</TableHead></TableRow></TableHeader>
                        <TableBody>{exports.map((e) => (
                            <TableRow key={e.id}>
                                <TableCell>{e.id.substring(0,8)}</TableCell>
                                <TableCell>{e.type}</TableCell>
                                <TableCell><Badge>{e.status}</Badge></TableCell>
                                <TableCell><Button variant="link" size="sm" asChild><a href={e.download_url}>Download</a></Button></TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            )}
        </ScrollArea>
    </div>
  );
};

export { Reports };
