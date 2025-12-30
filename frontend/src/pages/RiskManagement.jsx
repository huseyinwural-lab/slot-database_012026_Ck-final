import React, { useCallback, useEffect, useState } from 'react';
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
import { ShieldAlert, AlertTriangle, Search, Activity, Lock, Smartphone, FileText, UserMinus, Plus, Zap, CreditCard, MapPin, Skull, Ban, LayoutTemplate, Briefcase, Paperclip } from 'lucide-react';
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
  const [evidence, setEvidence] = useState([]);
  
  // Rule Creation
  const [isRuleOpen, setIsRuleOpen] = useState(false);
  const [newRule, setNewRule] = useState({ name: '', category: 'account', severity: 'medium', score_impact: 10 });

  // Blacklist Creation
  const [isBlacklistOpen, setIsBlacklistOpen] = useState(false);
  const [newBan, setNewBan] = useState({ type: 'ip', value: '', reason: '' });

  // Evidence Creation
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);
  const [newEvidence, setNewEvidence] = useState({ related_id: '', type: 'note', description: '' });

  // Case Management
  const [selectedCase, setSelectedCase] = useState(null);
  const [caseNote, setCaseNote] = useState("");

  const fetchData = useCallback(async () => {
    try {
      if (activeTab === 'dashboard') setDashboard((await api.get('/v1/risk/dashboard')).data);
      if (activeTab === 'rules') setRules((await api.get('/v1/risk/rules')).data);
      if (activeTab === 'velocity') setVelocity((await api.get('/v1/risk/velocity')).data);
      if (activeTab === 'blacklist') setBlacklist((await api.get('/v1/risk/blacklist')).data);
      if (activeTab === 'cases') setCases((await api.get('/v1/risk/cases')).data);
      if (activeTab === 'alerts') setAlerts((await api.get('/v1/risk/alerts')).data);
      if (activeTab === 'investigation') setEvidence((await api.get('/v1/risk/evidence')).data);
    } catch (err) {
      console.error(err);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateRule = async () => {
    try { await api.post('/v1/risk/rules', newRule); setIsRuleOpen(false); fetchData(); toast.success("Rule Created"); } catch { toast.error("Failed"); }
  };

  const handleCreateBan = async () => {
    try { await api.post('/v1/risk/blacklist', { ...newBan, added_by: 'admin' }); setIsBlacklistOpen(false); fetchData(); toast.success("Entry Blacklisted"); } catch { toast.error("Failed"); }
  };

  const handleAddEvidence = async () => {
    try { await api.post('/v1/risk/evidence', { ...newEvidence, uploaded_by: 'admin' }); setIsEvidenceOpen(false); fetchData(); toast.success("Evidence Added"); } catch { toast.error("Failed"); }
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

            {/* INVESTIGATION HUB */}
            <TabsContent value="investigation" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isEvidenceOpen} onOpenChange={setIsEvidenceOpen}>
                        <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Evidence</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Add Note / Evidence</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Related ID (Player/Case)</Label><Input value={newEvidence.related_id} onChange={e=>setNewEvidence({...newEvidence, related_id: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Type</Label>
                                    <Select value={newEvidence.type} onValueChange={v=>setNewEvidence({...newEvidence, type: v})}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="note">Internal Note</SelectItem><SelectItem value="file">File/Document</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2"><Label>Description</Label><Textarea value={newEvidence.description} onChange={e=>setNewEvidence({...newEvidence, description: e.target.value})} /></div>
                                <Button onClick={handleAddEvidence} className="w-full">Save</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card>
                    <CardHeader><CardTitle>Evidence & Notes</CardTitle></CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Description</TableHead><TableHead>Related To</TableHead><TableHead>Time</TableHead></TableRow></TableHeader>
                            <TableBody>{evidence.map(e => (
                                <TableRow key={e.id}>
                                    <TableCell className="capitalize flex items-center gap-2">
                                        {e.type === 'file' ? <Paperclip className="w-4 h-4" /> : <Briefcase className="w-4 h-4" />} {e.type}
                                    </TableCell>
                                    <TableCell>{e.description}</TableCell>
                                    <TableCell className="font-mono">{e.related_id}</TableCell>
                                    <TableCell>{new Date(e.uploaded_at).toLocaleString()}</TableCell>
                                </TableRow>
                            ))}</TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>

            {/* ALERT LIST */}
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

            {/* PLACEHOLDERS */}
            <TabsContent value="devices" className="mt-4"><Card><CardContent className="p-10 text-center">Device Intelligence Graph (Coming Soon)</CardContent></Card></TabsContent>
            <TabsContent value="payment" className="mt-4"><Card><CardContent className="p-10 text-center">Payment Risk (Coming Soon)</CardContent></Card></TabsContent>
            <TabsContent value="geo" className="mt-4"><Card><CardContent className="p-10 text-center">IP & Geo Intelligence (Coming Soon)</CardContent></Card></TabsContent>
            <TabsContent value="bonus" className="mt-4"><Card><CardContent className="p-10 text-center">Bonus Abuse Analytics (Coming Soon)</CardContent></Card></TabsContent>
            <TabsContent value="visuals" className="mt-4"><Card><CardContent className="p-10 text-center">Logic Visualizer (Coming Soon)</CardContent></Card></TabsContent>

        </Tabs>
    </div>
  );
};

export default RiskManagement;
