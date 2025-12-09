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
import { ShieldAlert, AlertTriangle, Search, Activity, Lock, Smartphone, FileText, UserMinus } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';

const RiskManagement = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [rules, setRules] = useState([]);
  const [cases, setCases] = useState([]);
  const [alerts, setAlerts] = useState([]);
  
  // Rule Creation
  const [isRuleOpen, setIsRuleOpen] = useState(false);
  const [newRule, setNewRule] = useState({ name: '', category: 'account', severity: 'medium', score_impact: 10 });

  // Case Management
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseNote, setCaseNote] = useState("");

  const fetchData = async () => {
    try {
        if (activeTab === 'dashboard') setDashboard((await api.get('/v1/risk/dashboard')).data);
        if (activeTab === 'rules') setRules((await api.get('/v1/risk/rules')).data);
        if (activeTab === 'cases') setCases((await api.get('/v1/risk/cases')).data);
        if (activeTab === 'alerts') setAlerts((await api.get('/v1/risk/alerts')).data);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  const handleCreateRule = async () => {
    try { await api.post('/v1/risk/rules', newRule); setIsRuleOpen(false); fetchData(); toast.success("Rule Created"); } catch { toast.error("Failed"); }
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
            <TabsList className="grid grid-cols-5 w-full lg:w-[700px]">
                <TabsTrigger value="dashboard"><Activity className="w-4 h-4 mr-2" /> Overview</TabsTrigger>
                <TabsTrigger value="alerts"><AlertTriangle className="w-4 h-4 mr-2" /> Live Alerts</TabsTrigger>
                <TabsTrigger value="cases"><FileText className="w-4 h-4 mr-2" /> Cases</TabsTrigger>
                <TabsTrigger value="rules"><Lock className="w-4 h-4 mr-2" /> Rules Engine</TabsTrigger>
                <TabsTrigger value="devices"><Smartphone className="w-4 h-4 mr-2" /> Devices</TabsTrigger>
            </TabsList>

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

            {/* ALERTS */}
            <TabsContent value="alerts" className="mt-4">
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Message</TableHead><TableHead>Severity</TableHead><TableHead>Time</TableHead></TableRow></TableHeader>
                        <TableBody>{alerts.map(a => (
                            <TableRow key={a.id}>
                                <TableCell className="uppercase font-bold text-xs">{a.type}</TableCell>
                                <TableCell>{a.message}</TableCell>
                                <TableCell><Badge variant={a.severity==='critical'?'destructive':'outline'}>{a.severity}</Badge></TableCell>
                                <TableCell>{new Date(a.timestamp).toLocaleTimeString()}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* RULES */}
            <TabsContent value="rules" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isRuleOpen} onOpenChange={setIsRuleOpen}>
                        <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Rule</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>New Risk Rule</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Rule Name</Label><Input value={newRule.name} onChange={e=>setNewRule({...newRule, name: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Category</Label>
                                    <Select value={newRule.category} onValueChange={v=>setNewRule({...newRule, category: v})}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="account">Account</SelectItem><SelectItem value="payment">Payment</SelectItem><SelectItem value="bonus_abuse">Bonus Abuse</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2"><Label>Score Impact</Label><Input type="number" value={newRule.score_impact} onChange={e=>setNewRule({...newRule, score_impact: e.target.value})} /></div>
                                <Button onClick={handleCreateRule} className="w-full">Save Rule</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Category</TableHead><TableHead>Impact</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader>
                        <TableBody>{rules.map(r => (
                            <TableRow key={r.id}>
                                <TableCell>{r.name}</TableCell>
                                <TableCell className="uppercase text-xs">{r.category}</TableCell>
                                <TableCell><Badge variant="secondary">+{r.score_impact}</Badge></TableCell>
                                <TableCell><Badge variant={r.status==='active'?'default':'outline'}>{r.status}</Badge></TableCell>
                                <TableCell className="text-right"><Button size="sm" variant="ghost" onClick={() => handleToggleRule(r.id)}>{r.status==='active'?'Pause':'Activate'}</Button></TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* CASES */}
            <TabsContent value="cases" className="mt-4">
                <div className="grid md:grid-cols-3 gap-6">
                    <Card className="md:col-span-1">
                        <CardHeader><CardTitle>Case List</CardTitle></CardHeader>
                        <div className="space-y-2 p-4">
                            {cases.map(c => (
                                <div key={c.id} onClick={() => setSelectedCase(c)} className={`p-3 border rounded cursor-pointer hover:bg-secondary/50 ${selectedCase?.id === c.id ? 'border-primary bg-secondary/30' : ''}`}>
                                    <div className="flex justify-between mb-1">
                                        <Badge variant="destructive">{c.risk_score}</Badge>
                                        <span className="text-xs text-muted-foreground">{new Date(c.created_at).toLocaleDateString()}</span>
                                    </div>
                                    <div className="font-bold text-sm">Player: {c.player_id}</div>
                                    <div className="text-xs text-muted-foreground">Rules: {c.triggered_rules.join(", ")}</div>
                                </div>
                            ))}
                        </div>
                    </Card>
                    <Card className="md:col-span-2">
                        {selectedCase ? (
                            <>
                                <CardHeader><CardTitle>Investigation: {selectedCase.id}</CardTitle><CardDescription>Status: {selectedCase.status.toUpperCase()}</CardDescription></CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="p-4 bg-secondary/20 rounded">
                                        <div className="font-bold mb-2">Evidence</div>
                                        <ul className="list-disc pl-5 text-sm">
                                            {selectedCase.triggered_rules.map(r => <li key={r}>{r}</li>)}
                                        </ul>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Analyst Note</Label>
                                        <Textarea value={caseNote} onChange={e => setCaseNote(e.target.value)} placeholder="Findings..." />
                                    </div>
                                    <div className="flex gap-2">
                                        <Button variant="destructive" onClick={() => handleCaseStatus('closed_confirmed')}><UserMinus className="w-4 h-4 mr-2" /> Confirm Fraud (Ban)</Button>
                                        <Button variant="outline" onClick={() => handleCaseStatus('closed_false_positive')}>False Positive</Button>
                                        <Button className="ml-auto" onClick={() => handleCaseStatus('escalated')}>Escalate</Button>
                                    </div>
                                </CardContent>
                            </>
                        ) : <div className="flex items-center justify-center h-40 text-muted-foreground">Select a case</div>}
                    </Card>
                </div>
            </TabsContent>

            {/* DEVICES */}
            <TabsContent value="devices" className="mt-4">
                <div className="p-10 text-center border border-dashed rounded text-muted-foreground">
                    Device Intelligence Graph Visualization (Coming Soon)
                </div>
            </TabsContent>
        </Tabs>
    </div>
  );
};

export default RiskManagement;
