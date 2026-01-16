import React, { useEffect, useState, useCallback } from 'react';
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
import RequireFeature from '../components/RequireFeature';

// NOTE: This page is heavily interactive and uses internal state updates during data loading.
// Existing eslint config in this repo does not include react-hooks exhaustive-deps rule.

import { 
  Beaker, Plus, Edit, Copy, Trash2, BarChart3, Download, 
  Power, Target, Clock, Dna, TrendingUp, Trophy, FileText,
  AlertTriangle, GitCompare, Settings2, Folder
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';

const FeatureFlags = () => {
  const [activeTab, setActiveTab] = useState("flags");
  const [flags, setFlags] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [segments, setSegments] = useState([]);
  const [groups, setGroups] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [envComparison, setEnvComparison] = useState([]);
  
  const [isFlagModalOpen, setIsFlagModalOpen] = useState(false);
  const [newFlag, setNewFlag] = useState({
    flag_id: '',
    name: '',
    description: '',
    type: 'boolean',
    default_value: false,
    scope: 'both',
    environment: 'production',
    group: 'Payments',
    targeting: {}
  });

  const fetchData = useCallback(async () => {
    try {
      if (activeTab === 'flags') setFlags((await api.get('/v1/flags/')).data);
      if (activeTab === 'experiments') setExperiments((await api.get('/v1/flags/experiments')).data);
      if (activeTab === 'segments') setSegments((await api.get('/v1/flags/segments')).data);
      if (activeTab === 'audit') setAuditLogs((await api.get('/v1/flags/audit-log')).data);
      if (activeTab === 'env-compare') setEnvComparison((await api.get('/v1/flags/environment-comparison')).data);
      setGroups((await api.get('/v1/flags/groups')).data);
    } catch (err) {
      console.error(err);
      toast.error('Veri yüklenirken hata');
    }
  }, [activeTab]);

  // Avoid direct setState sync-in-effect lint by scheduling fetch.
  useEffect(() => {
    const t = setTimeout(() => {
      fetchData();
    }, 0);

    return () => clearTimeout(t);
  }, [activeTab, fetchData]);

  const handleToggleFlag = async (flagId) => {
    try {
      await api.post(`/v1/flags/${flagId}/toggle`);
      fetchData();
      toast.success('Flag updated');
    } catch { toast.error('Failed'); }
  };

  const handleKillSwitch = async () => {
    if (!window.confirm('⛔ Are you sure you want to disable all flags?')) return;
    try {
      await api.post('/v1/flags/kill-switch');
      fetchData();
      toast.success('Kill switch applied');
    } catch { toast.error('Failed'); }
  };

  const handleCreateFlag = async () => {
    try {
      const payload = { ...newFlag, last_updated_by: 'Admin' };
      await api.post('/v1/flags/', payload);
      setIsFlagModalOpen(false);
      fetchData();
      toast.success('Flag created');
    } catch { toast.error('Failed'); }
  };

  const handleStartExperiment = async (expId) => {
    try {
      await api.post(`/v1/flags/experiments/${expId}/start`);
      fetchData();
      toast.success('Deney başlatıldı');
    } catch { toast.error('Başarısız'); }
  };

  const handlePauseExperiment = async (expId) => {
    try {
      await api.post(`/v1/flags/experiments/${expId}/pause`);
      fetchData();
      toast.success('Deney duraklatıldı');
    } catch { toast.error('Başarısız'); }
  };

  const getStatusBadge = (status) => {
    const variants = {
      on: 'default',
      off: 'secondary',
      scheduled: 'outline',
      running: 'default',
      paused: 'secondary',
      completed: 'outline',
      draft: 'secondary'
    };
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>;
  };

  return (
    <RequireFeature feature="can_manage_experiments">
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Beaker className="w-8 h-8 text-purple-600" /> Feature Flags & A/B Testing
        </h2>
        <Button variant="destructive" onClick={handleKillSwitch} className="bg-red-600 hover:bg-red-700">
          <AlertTriangle className="w-4 h-4 mr-2" /> ⛔ Kill Switch
        </Button>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <ScrollArea className="w-full whitespace-nowrap rounded-md border">
          <TabsList className="w-full flex justify-start">
            <TabsTrigger value="flags"><Beaker className="w-4 h-4 mr-2" /> 🧪 Feature Flags</TabsTrigger>
            <TabsTrigger value="experiments"><Dna className="w-4 h-4 mr-2" /> 🧬 Experiments</TabsTrigger>
            <TabsTrigger value="segments"><Target className="w-4 h-4 mr-2" /> 🎯 Segments</TabsTrigger>
            <TabsTrigger value="analytics"><BarChart3 className="w-4 h-4 mr-2" /> 📈 Analytics</TabsTrigger>
            <TabsTrigger value="results"><Trophy className="w-4 h-4 mr-2" /> 🏆 Results</TabsTrigger>
            <TabsTrigger value="audit"><FileText className="w-4 h-4 mr-2" /> 🧾 Audit Log</TabsTrigger>
            <TabsTrigger value="env-compare"><GitCompare className="w-4 h-4 mr-2" /> 🔀 Env Compare</TabsTrigger>
            <TabsTrigger value="groups"><Folder className="w-4 h-4 mr-2" /> 📁 Groups</TabsTrigger>
          </TabsList>
        </ScrollArea>

        <TabsContent value="flags" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">🧪 Feature Flags</CardTitle>
                <CardDescription>Yeni özellikleri segmentlere göre aç/kapa</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button disabled title="Not available in this environment">
                  <Download className="w-4 h-4 mr-2" /> Export JSON
                </Button>
                <Dialog open={isFlagModalOpen} onOpenChange={setIsFlagModalOpen}>
                  <DialogTrigger asChild>
                    <Button><Plus className="w-4 h-4 mr-2" /> Create Flag</Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader><DialogTitle>Yeni Feature Flag</DialogTitle></DialogHeader>
                    <ScrollArea className="max-h-[600px]">
                      <div className="space-y-4 p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Flag ID</Label>
                            <Input placeholder="new_payment_flow" value={newFlag.flag_id} onChange={e=>setNewFlag({...newFlag, flag_id: e.target.value})} />
                          </div>
                          <div className="space-y-2">
                            <Label>Name</Label>
                            <Input placeholder="New Payment Flow" value={newFlag.name} onChange={e=>setNewFlag({...newFlag, name: e.target.value})} />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label>Description</Label>
                          <Textarea placeholder="Açıklama..." value={newFlag.description} onChange={e=>setNewFlag({...newFlag, description: e.target.value})} />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Type</Label>
                            <Select value={newFlag.type} onValueChange={v=>setNewFlag({...newFlag, type: v})}>
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="boolean">Boolean</SelectItem>
                                <SelectItem value="string">String</SelectItem>
                                <SelectItem value="number">Number</SelectItem>
                                <SelectItem value="json">JSON</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Scope</Label>
                            <Select value={newFlag.scope} onValueChange={v=>setNewFlag({...newFlag, scope: v})}>
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="frontend">Frontend</SelectItem>
                                <SelectItem value="backend">Backend</SelectItem>
                                <SelectItem value="both">Both</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Environment</Label>
                            <Select value={newFlag.environment} onValueChange={v=>setNewFlag({...newFlag, environment: v})}>
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="production">Production</SelectItem>
                                <SelectItem value="staging">Staging</SelectItem>
                                <SelectItem value="development">Development</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Group</Label>
                            <Select value={newFlag.group} onValueChange={v=>setNewFlag({...newFlag, group: v})}>
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Payments">Payments</SelectItem>
                                <SelectItem value="Games">Games</SelectItem>
                                <SelectItem value="Fraud">Fraud</SelectItem>
                                <SelectItem value="CMS">CMS</SelectItem>
                                <SelectItem value="CRM">CRM</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <Button onClick={handleCreateFlag} className="w-full">💾 Create Flag</Button>
                      </div>
                    </ScrollArea>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Flag ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Scope</TableHead>
                    <TableHead>Environment</TableHead>
                    <TableHead>Group</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {flags.map(flag => (
                    <TableRow key={flag.id}>
                      <TableCell className="font-mono text-xs">{flag.flag_id}</TableCell>
                      <TableCell className="font-medium">{flag.name}</TableCell>
                      <TableCell>{getStatusBadge(flag.status)}</TableCell>
                      <TableCell><Badge variant="outline">{flag.type}</Badge></TableCell>
                      <TableCell><Badge variant="outline">{flag.scope}</Badge></TableCell>
                      <TableCell><Badge variant="outline">{flag.environment}</Badge></TableCell>
                      <TableCell><Badge>{flag.group}</Badge></TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost" onClick={() => handleToggleFlag(flag.id)}>
                            <Power className="w-4 h-4" />
                          </Button>
                          <Button size="sm" variant="ghost"><Edit className="w-4 h-4" /></Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {flags.length === 0 && <p className="text-center text-muted-foreground py-8">Henüz flag yok</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="experiments" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">🧬 A/B Test Experiments</CardTitle>
                <CardDescription>Varyantları test et, kazananı seç</CardDescription>
              </div>
              <Button><Plus className="w-4 h-4 mr-2" /> Create Experiment</Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Variants</TableHead>
                    <TableHead>Primary Metric</TableHead>
                    <TableHead>Owner</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {experiments.map(exp => (
                    <TableRow key={exp.id}>
                      <TableCell className="font-medium">{exp.name}</TableCell>
                      <TableCell>{getStatusBadge(exp.status)}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {exp.variants.map(v => (
                            <Badge key={v.id} variant="outline" className="text-xs">{v.name}</Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell><Badge>{exp.primary_metric}</Badge></TableCell>
                      <TableCell className="text-xs">{exp.owner}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {exp.status === 'draft' && (
                            <Button size="sm" onClick={() => handleStartExperiment(exp.id)}>▶️ Start</Button>
                          )}
                          {exp.status === 'running' && (
                            <Button size="sm" variant="secondary" onClick={() => handlePauseExperiment(exp.id)}>⏸️ Pause</Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {experiments.length === 0 && <p className="text-center text-muted-foreground py-8">Henüz deney yok</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="segments" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">🎯 Segments & Targeting</CardTitle>
                <CardDescription>Kullanıcı segmentleri tanımla</CardDescription>
              </div>
              <Button><Plus className="w-4 h-4 mr-2" /> Create Segment</Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Segment Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Rules</TableHead>
                    <TableHead>Population</TableHead>
                    <TableHead>Usage</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {segments.map(seg => (
                    <TableRow key={seg.id}>
                      <TableCell className="font-medium">{seg.name}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{seg.description}</TableCell>
                      <TableCell><Badge variant="outline">{seg.rules.length} rules</Badge></TableCell>
                      <TableCell>{seg.population_size.toLocaleString()}</TableCell>
                      <TableCell>{seg.usage_count} flags/experiments</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {segments.length === 0 && <p className="text-center text-muted-foreground py-8">Henüz segment yok</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">📈 Flag Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">87.5%</div>
                    <p className="text-xs text-muted-foreground">Activation Rate</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">+12.3%</div>
                    <p className="text-xs text-muted-foreground">Conversion Impact</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">0.02%</div>
                    <p className="text-xs text-muted-foreground">Error Rate</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">45K</div>
                    <p className="text-xs text-muted-foreground">Users Exposed</p>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🏆 Experiment Results</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-center text-muted-foreground py-8">Deney sonuçları burada görüntülenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">🧾 Flag Audit Log</CardTitle>
              </div>
              <Button><Download className="w-4 h-4 mr-2" /> Export Log</Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Admin</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Target</TableHead>
                    <TableHead>Target Name</TableHead>
                    <TableHead>Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {auditLogs.map(log => (
                    <TableRow key={log.id}>
                      <TableCell className="font-medium">{log.admin_name}</TableCell>
                      <TableCell><Badge>{log.action}</Badge></TableCell>
                      <TableCell><Badge variant="outline">{log.target_type}</Badge></TableCell>
                      <TableCell className="text-xs">{log.target_name}</TableCell>
                      <TableCell className="text-xs">{new Date(log.timestamp).toLocaleString('tr-TR')}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {auditLogs.length === 0 && <p className="text-center text-muted-foreground py-8">Henüz log yok</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="env-compare" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🔀 Environment Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Flag Name</TableHead>
                    <TableHead>Production</TableHead>
                    <TableHead>Staging</TableHead>
                    <TableHead>Differences</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {envComparison.map(comp => (
                    <TableRow key={comp.flag_id}>
                      <TableCell className="font-medium">{comp.flag_name}</TableCell>
                      <TableCell>
                        {comp.production?.status ? (
                          <Badge variant={comp.production.status === 'on' ? 'default' : 'secondary'}>
                            {comp.production.status}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground text-xs">Not in prod</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {comp.staging?.status ? (
                          <Badge variant={comp.staging.status === 'on' ? 'default' : 'secondary'}>
                            {comp.staging.status}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground text-xs">Not in staging</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {comp.differences.length > 0 ? (
                          comp.differences.map((diff, idx) => (
                            <Badge key={idx} variant="destructive" className="text-xs mr-1">{diff}</Badge>
                          ))
                        ) : (
                          <Badge variant="outline" className="text-xs">✅ Synced</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="groups" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">📁 Flag Groups</CardTitle>
              </div>
              <Button><Plus className="w-4 h-4 mr-2" /> Create Group</Button>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {groups.map(group => (
                  <Card key={group.id}>
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-bold text-lg">{group.name}</h3>
                          <p className="text-xs text-muted-foreground mt-1">{group.description}</p>
                          <div className="mt-4">
                            <Badge>{group.flag_count} flags</Badge>
                          </div>
                        </div>
                        <Folder className="w-8 h-8 text-muted-foreground" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
    </RequireFeature>
  );
};

export { FeatureFlags };