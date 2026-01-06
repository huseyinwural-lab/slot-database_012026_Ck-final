import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, Eye, Filter } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import PlayerActionsDrawer from '../components/PlayerActionsDrawer';

const PlayerList = () => {
  const navigate = useNavigate();
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [opsOpen, setOpsOpen] = useState(false);
  const [opsPlayer, setOpsPlayer] = useState(null);
  
  // Filters
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [vipLevel, setVipLevel] = useState("all");
  const [riskScore, setRiskScore] = useState("all");

  const fetchPlayers = async () => {
    setLoading(true);
    try {
      const params = { search };
      if (status !== "all") params.status = status;
      if (vipLevel !== "all") params.vip_level = vipLevel;
      if (riskScore !== "all") params.risk_score = riskScore;
      
      const res = await api.get('/v1/players', { params });
      setPlayers(res.data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlayers();
  }, []);

  const handleFilter = () => fetchPlayers();

  const handleExportXlsx = async () => {
    console.info('export_xlsx_clicked');
    try {
      const params = { search };
      if (status !== "all") params.status = status;
      if (vipLevel !== "all") params.vip_level = vipLevel;
      if (riskScore !== "all") params.risk_score = riskScore;

      const res = await api.get('/v1/players/export.xlsx', {
        params,
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `players_export_${new Date().toISOString()}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Player Management</h2>
        <Button onClick={handleExportXlsx}>Export Excel</Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
                <Input
                    placeholder="Search ID, Username, Email..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleFilter()}
                />
            </div>
            <div className="w-[150px]">
                <Select value={status} onValueChange={setStatus}>
                    <SelectTrigger><SelectValue placeholder="Status" /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="suspended">Suspended</SelectItem>
                        <SelectItem value="banned">Banned</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <div className="w-[150px]">
                <Select value={vipLevel} onValueChange={setVipLevel}>
                    <SelectTrigger><SelectValue placeholder="VIP Level" /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All VIP</SelectItem>
                        <SelectItem value="1">Level 1</SelectItem>
                        <SelectItem value="5">Level 5 (High)</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <div className="w-[150px]">
                <Select value={riskScore} onValueChange={setRiskScore}>
                    <SelectTrigger><SelectValue placeholder="Risk" /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Risk</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <Button onClick={handleFilter} variant="secondary"><Filter className="w-4 h-4 mr-2" /> Filter</Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>User / Email</TableHead>
                <TableHead>Registered</TableHead>
                <TableHead>Country</TableHead>
                <TableHead>Balance</TableHead>
                <TableHead>VIP</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={9} className="text-center">Loading...</TableCell></TableRow>
              ) : players.map((player) => (
                <TableRow key={player.id}>
                  <TableCell className="font-mono text-xs text-muted-foreground">{player.id.substring(0,8)}...</TableCell>
                  <TableCell>
                    <div className="font-medium">{player.username}</div>
                    <div className="text-xs text-muted-foreground">{player.email}</div>
                  </TableCell>
                  <TableCell className="text-xs">{new Date(player.registered_at).toLocaleDateString()}</TableCell>
                  <TableCell>{player.country}</TableCell>
                  <TableCell>
                    <div className="text-green-500 font-bold">${player.balance_real.toFixed(2)}</div>
                    <div className="text-xs text-yellow-500">B: ${player.balance_bonus.toFixed(2)}</div>
                  </TableCell>
                  <TableCell>Lvl {player.vip_level}</TableCell>
                  <TableCell>
                    <Badge variant={player.risk_score === 'high' ? 'destructive' : 'outline'}>{player.risk_score}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={player.status === 'active' ? 'default' : 'secondary'}>
                      {player.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => navigate(`/players/${player.id}`)}>
                        <Eye className="w-4 h-4" />
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

export default PlayerList;
