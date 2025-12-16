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
import { Scale, AlertTriangle, UserX, Shield, FileText, Activity, Plus } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

const ResponsibleGaming = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [rules, setRules] = useState([]);
  const [cases, setCases] = useState([]);
  
  // Rule Creation
  const [isRuleOpen, setIsRuleOpen] = useState(false);
  const [newRule, setNewRule] = useState({ name: '', severity: 'medium', description: '' });

  const fetchData = async () => {
    try {
        if (activeTab === 'dashboard') setDashboard((await api.get('/v1/rg/dashboard')).data);
        if (activeTab === 'alerts') setAlerts((await api.get('/v1/rg/alerts')).data);
        if (activeTab === 'rules') setRules((await api.get('/v1/rg/rules')).data);
        if (activeTab === 'cases') setCases((await api.get('/v1/rg/cases')).data);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  const handleCreateRule = async () => {
    try { await api.post('/v1/rg/rules', newRule); setIsRuleOpen(false); fetchData(); toast.success("Rule Created"); } catch { toast.error("Failed"); }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2"><Scale className="w-8 h-8 text-green-600" /> Responsible Gaming</h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
                <TabsTrigger value="dashboard"><Activity className="w-4 h-4 mr-2" /> Overview</TabsTrigger>
                <TabsTrigger value="alerts"><AlertTriangle className="w-4 h-4 mr-2" /> Alerts</TabsTrigger>
                <TabsTrigger value="profile"><UserX className="w-4 h-4 mr-2" /> Player Profile</TabsTrigger>
                <TabsTrigger value="rules"><Shield className="w-4 h-4 mr-2" /> Rules</TabsTrigger>
                <TabsTrigger value="cases"><FileText className="w-4 h-4 mr-2" /> Cases</TabsTrigger>
            </TabsList>

            {/* DASHBOARD */}
            <TabsContent value="dashboard" className="mt-4">
                {dashboard ? (
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Self Exclusions</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{dashboard.active_self_exclusions}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Cool Offs</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-500">{dashboard.active_cool_offs}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Limits</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-500">{dashboard.players_with_limits}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">High Loss Alerts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-orange-500">{dashboard.high_loss_alerts_7d}</div></CardContent></Card>
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
                                <TableCell>{new Date(a.created_at).toLocaleTimeString()}</TableCell>
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
                            <DialogHeader><DialogTitle>New RG Rule</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Rule Name</Label><Input value={newRule.name} onChange={e=>setNewRule({...newRule, name: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Severity</Label>
                                    <Select value={newRule.severity} onValueChange={v=>setNewRule({...newRule, severity: v})}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="low">Low</SelectItem><SelectItem value="medium">Medium</SelectItem><SelectItem value="high">High</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleCreateRule} className="w-full">Create</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Severity</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                        <TableBody>{rules.map(r => (
                            <TableRow key={r.id}>
                                <TableCell>{r.name}</TableCell>
                                <TableCell><Badge>{r.severity}</Badge></TableCell>
                                <TableCell>{r.active ? 'Active' : 'Inactive'}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* PROFILE PLACEHOLDER */}
            <TabsContent value="profile" className="mt-4"><Card><CardContent className="p-10 text-center text-muted-foreground">Select a player to view RG Profile (Coming Soon via Player Detail)</CardContent></Card></TabsContent>
            
            {/* CASES */}
            <TabsContent value="cases" className="mt-4"><Card><CardContent className="p-10 text-center text-muted-foreground">Case Management System (Mocked)</CardContent></Card></TabsContent>
        </Tabs>
    </div>
  );
};

export default ResponsibleGaming;
