import React, { useState } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Play, Save, BarChart3, Download } from 'lucide-react';
import { toast } from 'sonner';

const GameMathSimulator = ({ onRunComplete }) => {
  const [loading, setLoading] = useState(false);
  const [gameSimConfig, setGameSimConfig] = useState({
    game_id: 'slot_001',
    game_name: 'Big Win Slots',
    game_type: 'slots',
    spins_to_simulate: 10000,
    rtp_override: 96.5,
    seed: null
  });
  const [gameSimResult, setGameSimResult] = useState(null);

  const handleRunGameSim = async () => {
    setLoading(true);
    try {
      const run = {
        id: 'run_' + Date.now(),
        name: `Game Math - ${gameSimConfig.game_name}`,
        simulation_type: 'game_math',
        status: 'draft',
        created_by: 'Admin',
        notes: `${gameSimConfig.spins_to_simulate} spins simulation`
      };
      await api.post('/v1/simulation-lab/runs', run);
      
      const simData = {
        ...gameSimConfig,
        run_id: run.id
      };
      const result = await api.post('/v1/simulation-lab/game-math', simData);
      setGameSimResult(result.data);
      toast.success('Simülasyon tamamlandı!');
      if(onRunComplete) onRunComplete();
    } catch (err) {
      toast.error('Simülasyon başarısız');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6">
      {/* Input Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">🎰 Game Math Simulator</CardTitle>
          <CardDescription>Oyun matematiği simülasyonu (Slots/Table/Crash)</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="slots">
            <TabsList>
              <TabsTrigger value="slots">Slots</TabsTrigger>
              <TabsTrigger value="table">Table/Live</TabsTrigger>
              <TabsTrigger value="crash">Crash Games</TabsTrigger>
            </TabsList>
            
            <TabsContent value="slots" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Game ID</Label>
                  <Select value={gameSimConfig.game_id} onValueChange={v => setGameSimConfig({...gameSimConfig, game_id: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="slot_001">Big Win Slots (96.5%)</SelectItem>
                      <SelectItem value="slot_002">Mega Fortune (94.2%)</SelectItem>
                      <SelectItem value="slot_003">Book of Legends (97.1%)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Spins to Simulate</Label>
                  <Select value={gameSimConfig.spins_to_simulate.toString()} onValueChange={v => setGameSimConfig({...gameSimConfig, spins_to_simulate: parseInt(v)})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1000">1,000 (Quick Test)</SelectItem>
                      <SelectItem value="10000">10,000</SelectItem>
                      <SelectItem value="100000">100,000</SelectItem>
                      <SelectItem value="1000000">1,000,000</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>RTP Override (%)</Label>
                  <Input type="number" step="0.1" value={gameSimConfig.rtp_override} onChange={e => setGameSimConfig({...gameSimConfig, rtp_override: parseFloat(e.target.value)})} />
                </div>
                <div className="space-y-2">
                  <Label>Random Seed</Label>
                  <Input placeholder="Boş = random" value={gameSimConfig.seed || ''} onChange={e => setGameSimConfig({...gameSimConfig, seed: e.target.value || null})} />
                </div>
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button onClick={handleRunGameSim} disabled={loading}>
                  <Play className="w-4 h-4 mr-2" /> {loading ? 'Çalışıyor...' : 'Simülasyonu Başlat'}
                </Button>
                <Button variant="outline"><Save className="w-4 h-4 mr-2" /> Save Scenario</Button>
              </div>
            </TabsContent>
            
            <TabsContent value="table" className="space-y-4 mt-4">
              <p className="text-muted-foreground">Table/Live simülasyon özellikleri yakında eklenecek</p>
            </TabsContent>
            
            <TabsContent value="crash" className="space-y-4 mt-4">
              <p className="text-muted-foreground">Crash game simülasyonu yakında eklenecek</p>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Results */}
      {gameSimResult && (
        <Card>
          <CardHeader>
            <CardTitle>Simülasyon Sonuçları</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">{gameSimResult.results.simulated_rtp}%</div>
                  <p className="text-xs text-muted-foreground">Simulated RTP</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">{gameSimResult.results.volatility}</div>
                  <p className="text-xs text-muted-foreground">Volatility Index</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">{gameSimResult.results.hit_frequency}%</div>
                  <p className="text-xs text-muted-foreground">Hit Frequency</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">${gameSimResult.results.max_single_win?.toLocaleString()}</div>
                  <p className="text-xs text-muted-foreground">Max Single Win</p>
                </CardContent>
              </Card>
            </div>

            <h3 className="font-bold mb-4">Win Distribution</h3>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Win Range</TableHead>
                  <TableHead>Count</TableHead>
                  <TableHead>Percentage</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(gameSimResult.distribution || {}).map(([range, count]) => (
                  <TableRow key={range}>
                    <TableCell className="font-medium">{range}</TableCell>
                    <TableCell>{count.toLocaleString()}</TableCell>
                    <TableCell>{((count / gameSimResult.results.total_spins) * 100).toFixed(2)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            
            <div className="flex gap-2 mt-4">
              <Button variant="outline" disabled title="Not implemented yet"><BarChart3 className="w-4 h-4 mr-2" /> Show Graphs</Button>
              <Button variant="outline" disabled title="Not implemented yet"><Download className="w-4 h-4 mr-2" /> Export CSV</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GameMathSimulator;
