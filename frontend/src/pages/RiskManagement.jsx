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
import { toast } from 'sonner';
import { ShieldAlert, AlertTriangle, Search, Activity, Lock, Smartphone, FileText, UserMinus, Plus, Zap, CreditCard, MapPin, Skull, Ban, LayoutTemplate } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';

const RiskManagement = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [rules, setRules] = useState([]);
  const [cases, setCases] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [velocity, setVelocity] = useState([]);
  const [blacklist, setBlacklist] = useState([]);
  
  // Rule Creation
  const [isRuleOpen, setIsRuleOpen] = useState(false);
  const [newRule, setNewRule] = useState({ name: '', category: 'account', severity: 'medium', score_impact: 10 });

  // Blacklist Creation
  const [isBlacklistOpen, setIsBlacklistOpen] = useState(false);
  const [newBan, setNewBan] = useState({ type: 'ip', value: '', reason: '' });

  // Case Management
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseNote, setCaseNote] = useState("");

  const fetchData = async () => {
    try {
        if (activeTab === 'dashboard') setDashboard((await api.get('/v1/risk/dashboard')).data);
        if (activeTab === 'rules') setRules((await api.get('/v1/risk/rules')).data);
        if (activeTab === 'velocity') setVelocity((await api.get('/v1/risk/velocity')).data);
        if (activeTab === 'blacklist') setBlacklist((await api.get('/v1/risk/blacklist')).data);
        if (activeTab === 'cases') setCases((await api.get('/v1/risk/cases')).data);
        if (activeTab === 'alerts') setAlerts((await api.get('/v1/risk/alerts')).data);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  const handleCreateRule = async () => {
    try { await api.post('/v1/risk/rules', newRule); setIsRuleOpen(false); fetchData(); toast.success("Rule Created"); } catch { toast.error("Failed"); }
  };

  const handleCreateBan = async () => {
    try { await api.post('/v1/risk/blacklist', { ...newBan, added_by: 'admin' }); setIsBlacklistOpen(false); fetchData(); toast.success("Entry Blacklisted"); } catch { toast.error("Failed"); }
  };

  const handleToggleRule = async (id) => {
    try { await api.post(`/v1/risk/rules/${id}/toggle`); fetchData(); toast.success("Updated"); } catch { toast.error("Failed"); }
  };

  const handleCaseStatus = async (status) => {
    if (!selectedCase) return;
    try { 
        await api.put(`/v1/risk/cases/${selectedCase.id}/status`, { status, note: caseNote });
        toast.success(`Case ${status}`);
        setSelectedCase(null);
        fetchData();
    } catch { toast.error("Failed"); }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2"><ShieldAlert className="w-8 h-8 text-red-600" /> Risk & Fraud Engine</h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <ScrollArea className="w-full whitespace-nowrap rounded-md border">
                <TabsList className="w-full flex justify-start">
                    <TabsTrigger value="dashboard"><Activity className="w-4 h-4 mr-2" /> Overview</TabsTrigger>
                    <TabsTrigger value="alerts"><AlertTriangle className="w-4 h-4 mr-2" /> Live Alerts</TabsTrigger>
                    <TabsTrigger value="cases"><FileText className="w-4 h-4 mr-2" /> Cases</TabsTrigger>
                    <TabsTrigger value="investigation"><Search className="w-4 h-4 mr-2" /> Investigation</TabsTrigger>
                    <TabsTrigger value="rules"><Lock className="w-4 h-4 mr-2" /> Rules</TabsTrigger>
                    <TabsTrigger value="velocity"><Zap className="w-4 h-4 mr-2" /> Velocity</TabsTrigger>
                    <TabsTrigger value="payment"><CreditCard className="w-4 h-4 mr-2" /> Payment</TabsTrigger>
                    <TabsTrigger value="geo"><MapPin className="w-4 h-4 mr-2" /> IP & Geo</TabsTrigger>
                    <TabsTrigger value="bonus"><Skull className="w-4 h-4 mr-2" /> Bonus Abuse</TabsTrigger>
                    <TabsTrigger value="blacklist"><Ban className="w-4 h-4 mr-2" /> Blacklist</TabsTrigger>
                    <TabsTrigger value="visuals"><LayoutTemplate className="w-4 h-4 mr-2" /> Logic</TabsTrigger>
                </TabsList>
            </ScrollArea>

            {/* DASHBOARD */}
            <TabsContent value="dashboard" className="mt-4">
                {dashboard ? (
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card className="border-l-4 border-red-500"><CardHeader className="pb-2"><CardTitle className="text-sm">Daily Alerts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{dashboard.daily_alerts}</div></CardContent></Card>
                        <Card className="border-l-4 border-orange-500"><CardHeader className="pb-2"><CardTitle className="text-sm">Open Fraud Cases</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{dashboard.open_cases}</div></CardContent></Card>
                        <Card className="border-l-4 border-yellow-500"><CardHeader className="pb-2"><CardTitle className="text-sm">Bonus Abuse</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{dashboard.bonus_abuse_alerts}</div></CardContent></Card>
                        <Card className="border-l-4 border-blue-500"><CardHeader className="pb-2"><CardTitle className="text-sm">High Risk Players</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{dashboard.high_risk_players}</div></CardContent></Card>
                    </div>
                ) : <div>Loading...</div>}
            </TabsContent>

            {/* VELOCITY */}
            <TabsContent value="velocity" className="mt-4">
                <Card>
                    <CardHeader><CardTitle>Velocity Checks</CardTitle><CardDescription>High frequency event detection</CardDescription></CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Event</TableHead><TableHead>Threshold</TableHead><TableHead>Action</TableHead></TableRow></TableHeader>
                            <TableBody>{velocity.map(v => (
                                <TableRow key={v.id}>
                                    <TableCell>{v.name}</TableCell>
                                    <TableCell className="uppercase">{v.event_type}</TableCell>
                                    <TableCell>{v.threshold_count} in {v.time_window_minutes}m</TableCell>
                                    <TableCell><Badge>{v.action}</Badge></TableCell>
                                </TableRow>
                            ))}</TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>

            {/* BLACKLIST */}
            <TabsContent value="blacklist" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isBlacklistOpen} onOpenChange={setIsBlacklistOpen}>
                        <DialogTrigger asChild><Button variant="destructive"><Ban className="w-4 h-4 mr-2" /> Add to Blacklist</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Block Entity</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Type</Label>
                                    <Select value={newBan.type} onValueChange={v=>setNewBan({...newBan, type: v})}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="ip">IP Address</SelectItem><SelectItem value="device">Device Hash</SelectItem><SelectItem value="email_domain">Email Domain</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2"><Label>Value</Label><Input value={newBan.value} onChange={e=>setNewBan({...newBan, value: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Reason</Label><Input value={newBan.reason} onChange={e=>setNewBan({...newBan, reason: e.target.value})} /></div>
                                <Button onClick={handleCreateBan} className="w-full bg-red-600 hover:bg-red-700">Block</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Value</TableHead><TableHead>Reason</TableHead><TableHead>Date</TableHead></TableRow></TableHeader>
                        <TableBody>{blacklist.map(b => (
                            <TableRow key={b.id}>
                                <TableCell className="uppercase font-bold text-xs">{b.type}</TableCell>
                                <TableCell className="font-mono">{b.value}</TableCell>
                                <TableCell>{b.reason}</TableCell>
                                <TableCell>{new Date(b.added_at).toLocaleDateString()}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* INVESTIGATION HUB */}
            <TabsContent value="investigation" className="mt-4">
                <Card>
                    <CardHeader><CardTitle>Deep Investigation</CardTitle></CardHeader>
                    <CardContent className="flex items-center justify-center h-64 border-2 border-dashed rounded-lg">
                        <div className="text-center text-muted-foreground">
                            <Search className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>Select a Player or Case to view Timeline & Graph</p>
                            <Button variant="secondary" className="mt-4">Search Subject</Button>
                        </div>
                    </CardContent>
                </Card>
            </TabsContent>

            {/* VISUALS */}
            <TabsContent value="visuals" className="mt-4">
                <div className="grid md:grid-cols-2 gap-6">
                    <Card>
                        <CardHeader><CardTitle>Risk Score Logic</CardTitle></CardHeader>
                        <CardContent>
                            <div className="space-y-2 text-sm font-mono p-4 bg-secondary/20 rounded">
                                <p>1. Event Trigger (Login/Deposit/Bet)</p>
                                <p>↓</p>
                                <p>2. Check Whitelist (Exit if True)</p>
                                <p>↓</p>
                                <p>3. Check Velocity & Rules</p>
                                <p>↓</p>
                                <p>4. Sum Rule Impacts (+10, +50...)</p>
                                <p>↓</p>
                                <p>5. If Score > Threshold → Action</p>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader><CardTitle>Bonus Fraud Loop</CardTitle></CardHeader>
                        <CardContent>
                            <div className="space-y-2 text-sm font-mono p-4 bg-secondary/20 rounded">
                                <p>1. Bonus Claim Request</p>
                                <p>↓</p>
                                <p>2. Device Fingerprint Check</p>
                                <p>↓</p>
                                <p>3. IP/Geo Check</p>
                                <p>↓</p>
                                <p>4. Abuse History Check</p>
                                <p>↓</p>
                                <p>5. Approve or Block</p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </TabsContent>

            {/* PLACEHOLDERS FOR OTHER TABS */}
            <TabsContent value="rules" className="mt-4"><Card><CardContent className="p-10 text-center">Rules Engine (Existing)</CardContent></Card></TabsContent>
            <TabsContent value="payment" className="mt-4"><Card><CardContent className="p-10 text-center">Payment Risk Analysis (BIN/Card)</CardContent></Card></TabsContent>
            <TabsContent value="geo" className="mt-4"><Card><CardContent className="p-10 text-center">IP & Geo Intelligence (VPN/Proxy)</CardContent></Card></TabsContent>
            <TabsContent value="bonus" className="mt-4"><Card><CardContent className="p-10 text-center">Bonus Abuse Analytics</CardContent></Card></TabsContent>
            <TabsContent value="alerts" className="mt-4"><Card><CardContent className="p-10 text-center">Live Alerts (Existing)</CardContent></Card></TabsContent>
            <TabsContent value="cases" className="mt-4"><Card><CardContent className="p-10 text-center">Case Management (Existing)</CardContent></Card></TabsContent>

        </Tabs>
    </div>
  );
};

export default RiskManagement;
