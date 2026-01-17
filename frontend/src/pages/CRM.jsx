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
import { Megaphone, Users, Mail, MessageSquare, Send, Plus, Smartphone, Bell } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';

import RequireFeature from '../components/RequireFeature';

const CRM = () => {
  const [activeTab, setActiveTab] = useState("campaigns");
  const [campaigns, setCampaigns] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [segments, setSegments] = useState([]);
  const [channels, setChannels] = useState([]);
  
  // Create Campaign State
  const [newCampaign, setNewCampaign] = useState({ name: '', channel: 'email', segment_id: '', template_id: '' });
  const [isCampOpen, setIsCampOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      if (activeTab === 'campaigns') setCampaigns((await api.get('/v1/crm/campaigns')).data);
      if (activeTab === 'templates') setTemplates((await api.get('/v1/crm/templates')).data);
      if (activeTab === 'segments') setSegments((await api.get('/v1/crm/segments')).data);
      if (activeTab === 'channels') setChannels((await api.get('/v1/crm/channels')).data);
    } catch (err) {
      // Standard states:
      // - FEATURE_DISABLED -> ModuleDisabled (handled by RequireFeature)
      // - MODULE_TEMPORARILY_DISABLED -> banner
      // - 404 -> Coming soon
      const code = err?.standardized?.code;
      if (code === 'MODULE_TEMPORARILY_DISABLED') {
        toast.message('Temporarily disabled');
        return;
      }
      if (code === 'FEATURE_DISABLED') {
        return;
      }
      if (err?.standardized?.status === 404) {
        toast.message('Coming soon / Not implemented');
        return;
      }
      toast.error('Load failed');
    }
  }, [activeTab]);

  useEffect(() => {
    const t = setTimeout(() => {
      fetchData();
    }, 0);
    return () => clearTimeout(t);
  }, [activeTab, fetchData]);

  const handleCreateCampaign = async () => {
    toast.message('Not available in this environment');
  };

  const handleSendCampaign = async (id) => {
    try {
      const res = await api.post(`/v1/crm/campaigns/${id}/send`, {
        to: [process.env.REACT_APP_CRM_TEST_RECIPIENT || 'huseyinwural@gmail.com'],
        subject: `CRM Campaign ${id}`,
        html: `<p>CRM campaign <strong>${id}</strong> sent.</p>`,
      });
      toast.success('Campaign sent');
      fetchData();
      return res.data;
    } catch (err) {
      const code = err?.response?.data?.error_code;
      if (code) {
        toast.error(code);
      } else {
        toast.error('Send failed');
      }
    }
  };

  return (
    <RequireFeature feature="can_use_crm">
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">CRM & Communications</h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
                <TabsTrigger value="campaigns"><Megaphone className="w-4 h-4 mr-2" /> Campaigns</TabsTrigger>
                <TabsTrigger value="templates"><Mail className="w-4 h-4 mr-2" /> Templates</TabsTrigger>
                <TabsTrigger value="segments"><Users className="w-4 h-4 mr-2" /> Segments</TabsTrigger>
                <TabsTrigger value="channels"><MessageSquare className="w-4 h-4 mr-2" /> Channels</TabsTrigger>
            </TabsList>

            <TabsContent value="campaigns" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isCampOpen} onOpenChange={setIsCampOpen}>
                        <DialogTrigger asChild>
                          <Button onClick={() => setIsCampOpen(true)}>
                            <Plus className="w-4 h-4 mr-2" /> New Campaign
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Create Campaign</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Name</Label><Input value={newCampaign.name} onChange={e=>setNewCampaign({...newCampaign, name: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Channel</Label>
                                    <Select value={newCampaign.channel} onValueChange={v=>setNewCampaign({...newCampaign, channel: v})}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="email">Email</SelectItem><SelectItem value="sms">SMS</SelectItem><SelectItem value="push">Push</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2"><Label>Segment (Mock ID)</Label><Input value={newCampaign.segment_id} onChange={e=>setNewCampaign({...newCampaign, segment_id: e.target.value})} placeholder="Segment ID" /></div>
                                <div className="space-y-2"><Label>Template (Mock ID)</Label><Input value={newCampaign.template_id} onChange={e=>setNewCampaign({...newCampaign, template_id: e.target.value})} placeholder="Template ID" /></div>
                                <Button disabled title="Not available in this environment" className="w-full">Create Draft</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card>
                    <CardContent className="pt-6">
                        <Table>
                            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Channel</TableHead><TableHead>Status</TableHead><TableHead>Sent</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {campaigns.map(c => (
                                    <TableRow key={c.id}>
                                        <TableCell>{c.name}</TableCell>
                                        <TableCell><Badge variant="outline">{c.channel}</Badge></TableCell>
                                        <TableCell><Badge variant={c.status==='completed'?'default':'secondary'}>{c.status}</Badge></TableCell>
                                        <TableCell>{c.stats?.sent || 0}</TableCell>
                                        <TableCell className="text-right">
                                            {c.status === 'draft' && (
                                              <Button size="sm" onClick={() => handleSendCampaign(c.id)}>
                                                <Send className="w-4 h-4 mr-1" /> Send
                                              </Button>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>

            <TabsContent value="templates" className="mt-4">
                <Card>
                    <CardContent className="pt-6">
                        <Table>
                            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Channel</TableHead><TableHead>Subject/Body</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {templates.map(t => (
                                    <TableRow key={t.id}>
                                        <TableCell>{t.name}</TableCell>
                                        <TableCell className="uppercase">{t.channel}</TableCell>
                                        <TableCell className="text-muted-foreground truncate max-w-xs">{t.subject || t.body_text}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>

            <TabsContent value="segments" className="mt-4">
                <Card>
                    <CardContent className="pt-6">
                        <Table>
                            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Size (Est)</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {segments.map(s => (
                                    <TableRow key={s.id}>
                                        <TableCell>{s.name}</TableCell>
                                        <TableCell className="capitalize">{s.type}</TableCell>
                                        <TableCell>{s.estimated_size}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>

            <TabsContent value="channels" className="mt-4">
                <div className="grid md:grid-cols-3 gap-4">
                    {channels.map(c => (
                        <Card key={c.id}>
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-sm font-medium">{c.name}</CardTitle>
                                {c.type === 'email' ? <Mail className="h-4 w-4" /> : c.type === 'sms' ? <Smartphone className="h-4 w-4" /> : <Bell className="h-4 w-4" />}
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold uppercase">{c.provider}</div>
                                <p className="text-xs text-muted-foreground mt-1">{c.enabled ? 'Enabled' : 'Disabled'}</p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </TabsContent>
        </Tabs>
    </div>
    </RequireFeature>
  );
};

export { CRM };
