import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { toast } from 'sonner';
import { 
  Beaker, Play, Save, Download, Eye, TrendingUp, Users, Shield, Heart,
  Dna, Brain, Archive, Plus, RefreshCw, BarChart3, FileDown, Folder,
  Settings, Gift, Target, AlertTriangle
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';

const SimulationLab = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Game Math State
  const [gameSimConfig, setGameSimConfig] = useState({
    game_id: 'slot_001',
    game_name: 'Big Win Slots',
    game_type: 'slots',
    spins_to_simulate: 10000,
    rtp_override: 96.5,
    seed: null
  });
  const [gameSimResult, setGameSimResult] = useState(null);
  
  // Portfolio State
  const [portfolioGames, setPortfolioGames] = useState([]);
  
  // Bonus State
  const [bonusConfig, setBonusConfig] = useState({
    bonus_type: 'welcome',
    current_percentage: 100,
    new_percentage: 150,
    current_wagering: 35,
    new_wagering: 40,
    expected_participants: 1000
  });

  const fetchRuns = async () => {
    try {
      const res = await api.get('/v1/simulation-lab/runs');
      setRuns(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchRuns(); }, []);

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
      fetchRuns();
    } catch (err) {
      toast.error('Simülasyon başarısız');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      completed: 'default',
      running: 'secondary',
      failed: 'destructive',
      draft: 'outline'
    };
    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  const getTypeBadge = (type) => {
    const labels = {
      game_math: '🎰 Game Math',
      portfolio: '📈 Portfolio',
      bonus: '🎁 Bonus',
      cohort_ltv: '👥 Cohort/LTV',
      risk: '🛡️ Risk',
      rg: '❤️ RG',
      ab_variant: '🧬 A/B',
      mixed: '🧠 Mixed'
    };
    return <Badge variant="outline">{labels[type] || type}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Beaker className="w-8 h-8 text-purple-600" /> 🧪 Simulation Lab
        </h2>
        <Button onClick={fetchRuns}>
          <RefreshCw className="w-4 h-4 mr-2" /> Yenile
        </Button>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <ScrollArea className="w-full whitespace-nowrap rounded-md border">
          <TabsList className="w-full flex justify-start">
            <TabsTrigger value="overview"><Eye className="w-4 h-4 mr-2" /> Overview</TabsTrigger>
            <TabsTrigger value="game-math"><Target className="w-4 h-4 mr-2" /> 🎰 Game Math</TabsTrigger>
            <TabsTrigger value="portfolio"><TrendingUp className="w-4 h-4 mr-2" /> 📈 Portfolio</TabsTrigger>
            <TabsTrigger value="bonus"><Gift className="w-4 h-4 mr-2" /> 🎁 Bonus</TabsTrigger>
            <TabsTrigger value="cohort"><Users className="w-4 h-4 mr-2" /> 👥 Cohort/LTV</TabsTrigger>
            <TabsTrigger value="risk"><Shield className="w-4 h-4 mr-2" /> 🛡️ Risk</TabsTrigger>
            <TabsTrigger value="rg"><Heart className="w-4 h-4 mr-2" /> ❤️ RG</TabsTrigger>
            <TabsTrigger value="ab-sandbox"><Dna className="w-4 h-4 mr-2" /> 🧬 A/B Sandbox</TabsTrigger>
            <TabsTrigger value="scenario"><Brain className="w-4 h-4 mr-2" /> 🧠 Scenario Builder</TabsTrigger>
            <TabsTrigger value="archive"><Archive className="w-4 h-4 mr-2" /> 📁 Archive</TabsTrigger>
          </TabsList>
        </ScrollArea>

        {/* 1️⃣ OVERVIEW */}
        <TabsContent value="overview" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Lab Genel Durum</CardTitle>
                <CardDescription>Son simülasyonlar ve özet</CardDescription>
              </div>
              <Button><Plus className="w-4 h-4 mr-2" /> Yeni Simülasyon</Button>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4 mb-6">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{runs.length}</div>
                    <p className="text-xs text-muted-foreground">Toplam Simülasyon</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{runs.filter(r => r.status === 'completed').length}</div>
                    <p className="text-xs text-muted-foreground">Tamamlanan</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{runs.filter(r => r.status === 'running').length}</div>
                    <p className="text-xs text-muted-foreground">Çalışan</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{runs.filter(r => r.status === 'draft').length}</div>
                    <p className="text-xs text-muted-foreground">Taslak</p>
                  </CardContent>
                </Card>
              </div>

              <h3 className="font-bold mb-4">Son Simülasyonlar</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created By</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.slice(0, 10).map(run => (
                    <TableRow key={run.id}>
                      <TableCell className="font-medium">{run.name}</TableCell>
                      <TableCell>{getTypeBadge(run.simulation_type)}</TableCell>
                      <TableCell>{getStatusBadge(run.status)}</TableCell>
                      <TableCell className="text-xs">{run.created_by}</TableCell>
                      <TableCell className="text-xs">{new Date(run.created_at).toLocaleString('tr-TR')}</TableCell>
                      <TableCell className="text-xs">{run.duration_seconds ? `${run.duration_seconds}s` : '-'}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost"><Eye className="w-4 h-4" /></Button>
                          <Button size="sm" variant="ghost"><Download className="w-4 h-4" /></Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {runs.length === 0 && <p className="text-center text-muted-foreground py-8">Henüz simülasyon yok</p>}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 2️⃣ GAME MATH SIMULATOR */}
        <TabsContent value="game-math" className="mt-4">
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
                    <Button variant="outline"><BarChart3 className="w-4 h-4 mr-2" /> Show Graphs</Button>
                    <Button variant="outline"><Download className="w-4 h-4 mr-2" /> Export CSV</Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* 3️⃣ PORTFOLIO SIMULATOR */}
        <TabsContent value="portfolio" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">📈 Portfolio RTP & Revenue Simulator</CardTitle>
              <CardDescription>Portföy RTP ve trafik değişikliklerinin GGR/NGR etkisi</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Button variant="outline"><Download className="w-4 h-4 mr-2" /> Import from Live Data</Button>
                  <Button variant="outline"><Folder className="w-4 h-4 mr-2" /> Load Saved Scenario</Button>
                  <Button><Play className="w-4 h-4 mr-2" /> Run Portfolio Simulation</Button>
                </div>
                <p className="text-muted-foreground">Portfolio simülasyon arayüzü yakında eklenecek</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 4️⃣ BONUS SIMULATOR */}
        <TabsContent value="bonus" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🎁 Bonus & Campaign Simulator</CardTitle>
              <CardDescription>Bonus parametrelerinin ekonomik etkisi</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Bonus Type</Label>
                    <Select value={bonusConfig.bonus_type} onValueChange={v => setBonusConfig({...bonusConfig, bonus_type: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="welcome">Welcome Bonus</SelectItem>
                        <SelectItem value="reload">Reload Bonus</SelectItem>
                        <SelectItem value="cashback">Cashback</SelectItem>
                        <SelectItem value="free_spins">Free Spins</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Current Bonus %</Label>
                    <Input type="number" value={bonusConfig.current_percentage} onChange={e => setBonusConfig({...bonusConfig, current_percentage: parseInt(e.target.value)})} />
                  </div>
                  <div className="space-y-2">
                    <Label>New Bonus %</Label>
                    <Input type="number" value={bonusConfig.new_percentage} onChange={e => setBonusConfig({...bonusConfig, new_percentage: parseInt(e.target.value)})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Current Wagering</Label>
                    <Input type="number" value={bonusConfig.current_wagering} onChange={e => setBonusConfig({...bonusConfig, current_wagering: parseInt(e.target.value)})} />
                  </div>
                  <div className="space-y-2">
                    <Label>New Wagering</Label>
                    <Input type="number" value={bonusConfig.new_wagering} onChange={e => setBonusConfig({...bonusConfig, new_wagering: parseInt(e.target.value)})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Expected Participants</Label>
                    <Input type="number" value={bonusConfig.expected_participants} onChange={e => setBonusConfig({...bonusConfig, expected_participants: parseInt(e.target.value)})} />
                  </div>
                </div>
                <Button><Play className="w-4 h-4 mr-2" /> Run Bonus Simulation</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 5️⃣ COHORT/LTV */}
        <TabsContent value="cohort" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">👥 Player Cohort / LTV Simulator</CardTitle>
              <CardDescription>Segment LTV ve davranış simülasyonu</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Cohort/LTV simülasyon arayüzü yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 6️⃣ RISK */}
        <TabsContent value="risk" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🛡️ Risk & Fraud Scenario Simulator</CardTitle>
              <CardDescription>Risk kuralı değişikliklerinin etkisi</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Risk simülasyon arayüzü yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 7️⃣ RG */}
        <TabsContent value="rg" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">❤️ RG & Limits Impact Simulator</CardTitle>
              <CardDescription>RG limit politikalarının gelir etkisi</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">RG simülasyon arayüzü yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 8️⃣ A/B SANDBOX */}
        <TabsContent value="ab-sandbox" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🧬 A/B Variant Sandbox</CardTitle>
              <CardDescription>A/B test simülasyonu</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">A/B sandbox yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 9️⃣ SCENARIO BUILDER */}
        <TabsContent value="scenario" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🧠 Scenario Builder (Multi-Module)</CardTitle>
              <CardDescription>Çok modüllü karmaşık senaryolar</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Scenario builder yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 🔟 ARCHIVE */}
        <TabsContent value="archive" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">📁 Simulation Runs & Results Archive</CardTitle>
              <CardDescription>Tüm geçmiş simülasyonlar</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Simulation ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Owner</TableHead>
                    <TableHead>Tags</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map(run => (
                    <TableRow key={run.id}>
                      <TableCell className="font-mono text-xs">{run.id}</TableCell>
                      <TableCell className="font-medium">{run.name}</TableCell>
                      <TableCell>{getTypeBadge(run.simulation_type)}</TableCell>
                      <TableCell>{getStatusBadge(run.status)}</TableCell>
                      <TableCell className="text-xs">{run.created_by}</TableCell>
                      <TableCell>
                        {run.tags?.map(tag => <Badge key={tag} variant="outline" className="mr-1 text-xs">{tag}</Badge>)}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost"><Eye className="w-4 h-4" /></Button>
                          <Button size="sm" variant="ghost"><RefreshCw className="w-4 h-4" /></Button>
                          <Button size="sm" variant="ghost"><Download className="w-4 h-4" /></Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SimulationLab;