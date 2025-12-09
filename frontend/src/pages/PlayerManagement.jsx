import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import { 
  Users, Search, Filter, Download, MoreHorizontal, 
  ShieldAlert, Mail, Ban, Tag, ArrowUpDown, Calendar, DollarSign
} from 'lucide-react';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, 
  DropdownMenuSeparator, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';

const PlayerManagement = () => {
  const navigate = useNavigate();
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: 'all',
    search: '',
    vip_level: 'all',
    risk_score: 'all',
    country: 'all'
  });
  const [selectedPlayers, setSelectedPlayers] = useState([]);

  // Fetch Data
  const fetchPlayers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.status !== 'all') params.append('status', filters.status);
      if (filters.search) params.append('search', filters.search);
      if (filters.vip_level !== 'all') params.append('vip_level', filters.vip_level);
      if (filters.risk_score !== 'all') params.append('risk_score', filters.risk_score);
      if (filters.country !== 'all') params.append('country', filters.country);

      const res = await api.get(`/v1/players?${params.toString()}`);
      setPlayers(res.data);
    } catch (err) {
      toast.error('Failed to load players');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPlayers(); }, [filters]);

  const handleSelectAll = (checked) => {
    if (checked) setSelectedPlayers(players.map(p => p.id));
    else setSelectedPlayers([]);
  };

  const handleSelectOne = (id, checked) => {
    if (checked) setSelectedPlayers([...selectedPlayers, id]);
    else setSelectedPlayers(selectedPlayers.filter(pid => pid !== id));
  };

  const handleBulkAction = async (action) => {
    if (selectedPlayers.length === 0) return;
    if (!window.confirm(`Are you sure you want to ${action} ${selectedPlayers.length} players?`)) return;
    
    try {
      // Mock API call for bulk action
      // await api.post('/v1/players/bulk', { ids: selectedPlayers, action });
      toast.success(`Action ${action} queued for ${selectedPlayers.length} players`);
      setSelectedPlayers([]);
    } catch (err) { toast.error('Bulk action failed'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Users className="w-8 h-8 text-blue-600" /> Player Management
          </h2>
          <p className="text-muted-foreground">Manage user accounts, risk, and VIP status.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => toast.success("Exporting CSV...")}>
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
          <Button onClick={() => navigate('/players/create')}>
            <Users className="w-4 h-4 mr-2" /> Manual Reg
          </Button>
        </div>
      </div>

      {/* Filters Toolbar */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search by ID, Username, Email..." 
                className="pl-8" 
                value={filters.search}
                onChange={e => setFilters({...filters, search: e.target.value})}
              />
            </div>
            
            <Select value={filters.status} onValueChange={v => setFilters({...filters, status: v})}>
              <SelectTrigger className="w-[140px]"><SelectValue placeholder="Status" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
                <SelectItem value="banned">Banned</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filters.risk_score} onValueChange={v => setFilters({...filters, risk_score: v})}>
              <SelectTrigger className="w-[140px]"><SelectValue placeholder="Risk Level" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Risk</SelectItem>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>

            {/* Advanced Filters Popover */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="border-dashed">
                  <Filter className="w-4 h-4 mr-2" /> Advanced Filters
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80 space-y-4">
                <div className="space-y-2">
                  <h4 className="font-medium leading-none">More Filters</h4>
                  <p className="text-sm text-muted-foreground">Narrow down your search.</p>
                </div>
                <div className="grid gap-2">
                  <div className="grid grid-cols-2 items-center gap-2">
                    <Label htmlFor="min_dep">Min Deposit</Label>
                    <Input id="min_dep" placeholder="$0" type="number" />
                  </div>
                  <div className="grid grid-cols-2 items-center gap-2">
                    <Label htmlFor="country">Country</Label>
                    <Input id="country" placeholder="ISO Code" />
                  </div>
                  <div className="grid grid-cols-2 items-center gap-2">
                    <Label htmlFor="affiliate">Affiliate ID</Label>
                    <Input id="affiliate" placeholder="Ref code" />
                  </div>
                </div>
                <Button className="w-full" onClick={fetchPlayers}>Apply Filters</Button>
              </PopoverContent>
            </Popover>

            {selectedPlayers.length > 0 && (
              <div className="flex items-center gap-2 ml-auto bg-muted p-1 rounded-md">
                <Badge variant="secondary">{selectedPlayers.length} selected</Badge>
                <Button size="sm" variant="ghost" onClick={() => handleBulkAction('tag')}><Tag className="w-4 h-4" /></Button>
                <Button size="sm" variant="ghost" onClick={() => handleBulkAction('email')}><Mail className="w-4 h-4" /></Button>
                <Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleBulkAction('freeze')}><Ban className="w-4 h-4" /></Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Players Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[40px]">
                  <Checkbox 
                    checked={players.length > 0 && selectedPlayers.length === players.length}
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
                <TableHead>Player</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>VIP</TableHead>
                <TableHead className="text-right">Balance</TableHead>
                <TableHead className="text-right">Net Pos</TableHead>
                <TableHead>Last Login</TableHead>
                <TableHead>Affiliate</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={10} className="text-center h-24">Loading...</TableCell></TableRow>
              ) : players.length === 0 ? (
                <TableRow><TableCell colSpan={10} className="text-center h-24 text-muted-foreground">No players found</TableCell></TableRow>
              ) : (
                players.map((player) => (
                  <TableRow key={player.id} className="group">
                    <TableCell>
                      <Checkbox 
                        checked={selectedPlayers.includes(player.id)}
                        onCheckedChange={(checked) => handleSelectOne(player.id, checked)}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span 
                          className="font-medium hover:underline cursor-pointer text-blue-600"
                          onClick={() => navigate(`/players/${player.id}`)}
                        >
                          {player.username}
                        </span>
                        <span className="text-xs text-muted-foreground">{player.email}</span>
                        <div className="flex gap-1 mt-1">
                          {player.country && <Badge variant="outline" className="text-[10px] py-0 h-4">{player.country}</Badge>}
                          {player.kyc_status === 'approved' && <Badge variant="secondary" className="text-[10px] py-0 h-4 bg-green-100 text-green-800">KYC</Badge>}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={
                        player.status === 'active' ? 'default' : 
                        player.status === 'suspended' ? 'destructive' : 'secondary'
                      }>
                        {player.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {player.risk_score === 'high' ? (
                        <div className="flex items-center text-red-600 font-bold text-xs"><ShieldAlert className="w-3 h-3 mr-1" /> HIGH</div>
                      ) : (
                        <span className="text-xs text-muted-foreground">Low</span>
                      )}
                    </TableCell>
                    <TableCell><Badge variant="outline">Lvl {player.vip_level}</Badge></TableCell>
                    <TableCell className="text-right font-mono font-medium">${player.balance_real.toLocaleString()}</TableCell>
                    <TableCell className={`text-right font-mono text-xs ${(player.total_deposits - player.total_withdrawals) > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {/* Placeholder calculation, replace with real data */}
                      ${(player.balance_real * 1.5).toFixed(0)} 
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {player.last_login ? new Date(player.last_login).toLocaleDateString() : 'Never'}
                    </TableCell>
                    <TableCell className="text-xs max-w-[100px] truncate" title={player.affiliate_source || 'Direct'}>
                      {player.affiliate_source || 'Direct'}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem onClick={() => navigate(`/players/${player.id}`)}>View Details</DropdownMenuItem>
                          <DropdownMenuItem>View Transactions</DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600">Freeze Account</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default PlayerManagement;
