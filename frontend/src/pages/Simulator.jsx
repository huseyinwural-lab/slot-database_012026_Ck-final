import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import { Play, RotateCcw, Activity, Users, CreditCard, Clock } from 'lucide-react';

const Simulator = () => {
  const [logs, setLogs] = useState([]);
  
  // Player Sim State
  const [playerCount, setPlayerCount] = useState(10);
  const [playerRisk, setPlayerRisk] = useState("low");

  // Game Sim State
  const [gameCount, setGameCount] = useState(50);
  const [winRate, setWinRate] = useState(30);

  // Time Travel
  const [daysOffset, setDaysOffset] = useState(0);

  const fetchLogs = async () => {
    try {
        const res = await api.get('/v1/simulator/logs');
        setLogs(res.data);
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000); // Live poll logs
    return () => clearInterval(interval);
  }, []);

  const runPlayerSim = async () => {
    try {
        await api.post('/v1/simulator/players/start', { count: playerCount, risk_profile: playerRisk });
        toast.success("Player Simulation Started");
    } catch (e) { toast.error("Failed to start"); }
  };

  const runGameSim = async () => {
    try {
        await api.post('/v1/simulator/games/start', { count: gameCount, win_rate: winRate / 100 });
        toast.success("Game Simulation Started");
    } catch (e) { toast.error("Failed to start"); }
  };

  const runTimeTravel = async () => {
    try {
        await api.post('/v1/simulator/time-travel', { days_offset: daysOffset });
        toast.success(`Time warped by ${daysOffset} days`);
    } catch (e) { toast.error("Failed to time travel"); }
  };

  return (
    <div className="space-y-6">
        <div>
            <h2 className="text-3xl font-bold tracking-tight text-purple-400">Simulation Lab 🧪</h2>
            <p className="text-muted-foreground">Test system behavior with virtual agents and scenario runners.</p>
        </div>

        <Tabs defaultValue="players" className="w-full">
            <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
                <TabsTrigger value="players">Players</TabsTrigger>
                <TabsTrigger value="games">Game Engine</TabsTrigger>
                <TabsTrigger value="finance">Finance</TabsTrigger>
                <TabsTrigger value="timetravel">Time Travel</TabsTrigger>
            </TabsList>

            <div className="grid md:grid-cols-2 gap-6 mt-6">
                {/* Configuration Area */}
                <Card className="h-fit">
                    <CardHeader>
                        <CardTitle>Configuration</CardTitle>
                        <CardDescription>Adjust simulation parameters</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <TabsContent value="players" className="space-y-4 mt-0">
                            <div className="space-y-2">
                                <Label>Number of Players: {playerCount}</Label>
                                <Slider value={[playerCount]} onValueChange={(v) => setPlayerCount(v[0])} max={1000} step={10} />
                            </div>
                            <div className="space-y-2">
                                <Label>Risk Profile</Label>
                                <Select value={playerRisk} onValueChange={setPlayerRisk}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="low">Low Risk (Normal)</SelectItem>
                                        <SelectItem value="medium">Medium Risk</SelectItem>
                                        <SelectItem value="high">High Risk (Fraud)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <Button onClick={runPlayerSim} className="w-full bg-blue-600 hover:bg-blue-700">
                                <Users className="w-4 h-4 mr-2" /> Generate Players
                            </Button>
                        </TabsContent>

                        <TabsContent value="games" className="space-y-4 mt-0">
                            <div className="space-y-2">
                                <Label>Number of Rounds: {gameCount}</Label>
                                <Slider value={[gameCount]} onValueChange={(v) => setGameCount(v[0])} max={5000} step={50} />
                            </div>
                            <div className="space-y-2">
                                <Label>Target Win Rate: {winRate}%</Label>
                                <Slider value={[winRate]} onValueChange={(v) => setWinRate(v[0])} max={100} />
                            </div>
                            <Button onClick={runGameSim} className="w-full bg-green-600 hover:bg-green-700">
                                <Activity className="w-4 h-4 mr-2" /> Start Game Engine
                            </Button>
                        </TabsContent>

                         <TabsContent value="finance" className="space-y-4 mt-0">
                             <div className="p-4 border border-dashed rounded text-center text-muted-foreground">
                                <CreditCard className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                <p>Finance Sandbox Mock</p>
                                <p className="text-xs">Simulates deposit/withdrawal callbacks from providers like Stripe/Crypto.</p>
                             </div>
                             <Button onClick={() => toast.info("Simulated Deposit Callback Sent")} variant="outline" className="w-full">
                                Test Deposit Callback
                             </Button>
                         </TabsContent>

                         <TabsContent value="timetravel" className="space-y-4 mt-0">
                             <div className="space-y-2">
                                <Label>Days Offset: {daysOffset}</Label>
                                <div className="flex gap-2">
                                    <Button size="sm" variant="outline" onClick={() => setDaysOffset(daysOffset - 1)}>-</Button>
                                    <Input type="number" value={daysOffset} readOnly className="text-center" />
                                    <Button size="sm" variant="outline" onClick={() => setDaysOffset(daysOffset + 1)}>+</Button>
                                </div>
                             </div>
                             <Button onClick={runTimeTravel} className="w-full bg-purple-600 hover:bg-purple-700">
                                <Clock className="w-4 h-4 mr-2" /> Warp Time
                             </Button>
                         </TabsContent>
                    </CardContent>
                </Card>

                {/* Logs Area */}
                <Card className="h-[500px] flex flex-col">
                    <CardHeader className="border-b">
                        <div className="flex justify-between items-center">
                            <CardTitle>Live Execution Logs</CardTitle>
                            <Button variant="ghost" size="sm" onClick={fetchLogs}><RotateCcw className="w-4 h-4" /></Button>
                        </div>
                    </CardHeader>
                    <ScrollArea className="flex-1 p-4">
                        <div className="space-y-2 font-mono text-xs">
                            {logs.map((log) => (
                                <div key={log.id} className="p-2 border rounded bg-secondary/30">
                                    <div className="flex justify-between text-muted-foreground mb-1">
                                        <span className="uppercase font-bold text-primary">{log.type}</span>
                                        <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                    <div>{log.message}</div>
                                    {log.details && (
                                        <div className="mt-1 text-muted-foreground opacity-70">
                                            {JSON.stringify(log.details)}
                                        </div>
                                    )}
                                </div>
                            ))}
                            {logs.length === 0 && <div className="text-center text-muted-foreground mt-20">Waiting for simulation data...</div>}
                        </div>
                    </ScrollArea>
                </Card>
            </div>
        </Tabs>
    </div>
  );
};

export default Simulator;
