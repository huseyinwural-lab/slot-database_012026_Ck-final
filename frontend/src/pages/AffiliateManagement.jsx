import React, { useEffect, useState } from 'react';
import { useCallback } from 'react';
import api from '../services/api';
import { postWithReason } from '../services/apiReason';
import ReasonDialog from '../components/ReasonDialog';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Users, Target, Link as LinkIcon, DollarSign, Image as ImageIcon, BarChart, Handshake, Plus, ExternalLink, Copy } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

import RequireFeature from '../components/RequireFeature';

const AffiliateManagement = () => {
  const [activeTab, setActiveTab] = useState("partners");
  const [affiliates, setAffiliates] = useState([]);
  const [offers, setOffers] = useState([]);
  const [links, setLinks] = useState([]);
  const [payouts, setPayouts] = useState([]);
  const [creatives, setCreatives] = useState([]);
  
  // Dialog States
  const [isAffOpen, setIsAffOpen] = useState(false);
  const [isOfferOpen, setIsOfferOpen] = useState(false);
  const [isLinkOpen, setIsLinkOpen] = useState(false);
  const [isPayoutOpen, setIsPayoutOpen] = useState(false);
  const [isCreativeOpen, setIsCreativeOpen] = useState(false);

  // Forms
  const [newAffiliate, setNewAffiliate] = useState({ username: '', email: '', company_name: '', model: 'revshare' });
  const [newOffer, setNewOffer] = useState({ name: '', model: 'cpa', cpa_amount: 50, revshare_percentage: 25 });
  const [newLink, setNewLink] = useState({ affiliate_id: '', offer_id: '', name: 'Main Tracker' });
  const [newPayout, setNewPayout] = useState({ affiliate_id: '', amount: 0, period_start: '', period_end: '' });
  const [newCreative, setNewCreative] = useState({ name: '', type: 'banner', url: '' });

  const fetchData = useCallback(async () => {
    try {
        if (activeTab === 'partners') setAffiliates((await api.get('/v1/affiliates')).data);
        if (activeTab === 'offers') setOffers((await api.get('/v1/affiliates/offers')).data);
        if (activeTab === 'links') {
            // Backend has no list-all links endpoint (only /affiliates/{affiliate_id}/links)
            // So we keep links as empty list to avoid deceptive click/toast.
            setLinks([]);
            setAffiliates((await api.get('/v1/affiliates')).data); // Need for dropdown
            setOffers((await api.get('/v1/affiliates/offers')).data); // Need for dropdown
        }
        if (activeTab === 'payouts') {
            setPayouts((await api.get('/v1/affiliates/payouts')).data);
            setAffiliates((await api.get('/v1/affiliates')).data);
        }
        if (activeTab === 'creatives') setCreatives((await api.get('/v1/affiliates/creatives')).data);
    } catch (err) {
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
      toast.error('Unexpected error');
    }
  }, [activeTab]);

  useEffect(() => {
    const t = setTimeout(() => {
      fetchData();
    }, 0);
    return () => clearTimeout(t);
  }, [activeTab, fetchData]);

  // Handlers
  const handleCreateAffiliate = async () => {
    try { await api.post('/v1/affiliates', newAffiliate); setIsAffOpen(false); fetchData(); toast.success("Affiliate Created"); } catch { toast.error("Failed"); }
  };
  const handleCreateOffer = async () => {
    const payload = {
        name: newOffer.name, model: newOffer.model,
        default_commission: { model: newOffer.model, cpa_amount: newOffer.cpa_amount, revshare_percentage: newOffer.revshare_percentage }
    };
    try { await api.post('/v1/affiliates/offers', payload); setIsOfferOpen(false); fetchData(); toast.success("Offer Created"); } catch { toast.error("Failed"); }
  };
  const handleCreateLink = async () => {
    // Backend does not support global link creation; it requires /affiliates/{affiliate_id}/links with a unique `code`.
    toast.message('Not available in this environment');
  };
  const handleCreatePayout = async () => {
    const payload = { ...newPayout, period_start: new Date().toISOString(), period_end: new Date().toISOString() };
    try { await api.post('/v1/affiliates/payouts', payload); setIsPayoutOpen(false); fetchData(); toast.success("Payout Recorded"); } catch { toast.error("Failed"); }
  };
  const handleCreateCreative = async () => {
    try { await api.post('/v1/affiliates/creatives', newCreative); setIsCreativeOpen(false); fetchData(); toast.success("Creative Added"); } catch { toast.error("Failed"); }
  };
  const handleStatus = async (id, status) => {
    try { await api.put(`/v1/affiliates/${id}/status`, { status }); toast.success("Status Updated"); fetchData(); } catch { toast.error("Failed"); }
  };

  return (
    <RequireFeature feature="can_manage_affiliates">
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Affiliate Program</h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid grid-cols-6 w-full lg:w-[800px]">
                <TabsTrigger value="partners"><Users className="w-4 h-4 mr-2" /> Partners</TabsTrigger>
                <TabsTrigger value="offers"><Target className="w-4 h-4 mr-2" /> Offers</TabsTrigger>
                <TabsTrigger value="links"><LinkIcon className="w-4 h-4 mr-2" /> Tracking</TabsTrigger>
                <TabsTrigger value="payouts"><DollarSign className="w-4 h-4 mr-2" /> Payouts</TabsTrigger>
                <TabsTrigger value="creatives"><ImageIcon className="w-4 h-4 mr-2" /> Creatives</TabsTrigger>
                <TabsTrigger value="reports"><BarChart className="w-4 h-4 mr-2" /> Reports</TabsTrigger>
            </TabsList>

            {/* PARTNERS */}
            <TabsContent value="partners" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isAffOpen} onOpenChange={setIsAffOpen}>
                        <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Partner</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>New Partner</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Company / Username</Label><Input value={newAffiliate.username} onChange={e=>setNewAffiliate({...newAffiliate, username: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Email</Label><Input value={newAffiliate.email} onChange={e=>setNewAffiliate({...newAffiliate, email: e.target.value})} /></div>
                                <Button onClick={handleCreateAffiliate} className="w-full">Create</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Partner</TableHead><TableHead>Email</TableHead><TableHead>Balance</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader>
                        <TableBody>{affiliates.map(a => (
                            <TableRow key={a.id}>
                                <TableCell className="font-medium">{a.company_name || a.username}</TableCell>
                                <TableCell>{a.email}</TableCell>
                                <TableCell className="font-bold text-green-500">${a.balance}</TableCell>
                                <TableCell><Badge variant={a.status==='active'?'default':'secondary'}>{a.status}</Badge></TableCell>
                                <TableCell className="text-right">{a.status === 'pending' && <Button size="sm" onClick={() => handleStatus(a.id, 'active')}>Approve</Button>}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* OFFERS */}
            <TabsContent value="offers" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isOfferOpen} onOpenChange={setIsOfferOpen}>
                        <DialogTrigger asChild>
                          <Button disabled title="Not available in this environment">
                            <Plus className="w-4 h-4 mr-2" /> New Offer
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Create Offer</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Offer Name</Label><Input value={newOffer.name} onChange={e=>setNewOffer({...newOffer, name: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Model</Label>
                                    <Select value={newOffer.model} onValueChange={v=>setNewOffer({...newOffer, model: v})}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="cpa">CPA</SelectItem><SelectItem value="revshare">RevShare</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                {newOffer.model === 'cpa' && <div className="space-y-2"><Label>CPA Amount ($)</Label><Input type="number" value={newOffer.cpa_amount} onChange={e=>setNewOffer({...newOffer, cpa_amount: e.target.value})} /></div>}
                                {newOffer.model === 'revshare' && <div className="space-y-2"><Label>RevShare (%)</Label><Input type="number" value={newOffer.revshare_percentage} onChange={e=>setNewOffer({...newOffer, revshare_percentage: e.target.value})} /></div>}
                                <Button onClick={handleCreateOffer} className="w-full">Create Offer</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Offer</TableHead><TableHead>Model</TableHead><TableHead>Rate</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                        <TableBody>{offers.map(o => (
                            <TableRow key={o.id}>
                                <TableCell>{o.name}</TableCell>
                                <TableCell className="uppercase">{o.model}</TableCell>
                                <TableCell>{o.model === 'cpa' ? `$${o.default_commission.cpa_amount}` : `${o.default_commission.revshare_percentage}%`}</TableCell>
                                <TableCell><Badge variant="outline">{o.status}</Badge></TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* LINKS */}
            <TabsContent value="links" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isLinkOpen} onOpenChange={setIsLinkOpen}>
                        <DialogTrigger asChild>
                              <Button disabled title="Not available in this environment">
                                <Plus className="w-4 h-4 mr-2" /> Generate Link
                              </Button>
                            </DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Tracking Link</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Link Name</Label><Input value={newLink.name} onChange={e=>setNewLink({...newLink, name: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Affiliate</Label>
                                    <Select value={newLink.affiliate_id} onValueChange={v=>setNewLink({...newLink, affiliate_id: v})}>
                                        <SelectTrigger><SelectValue placeholder="Select Partner" /></SelectTrigger>
                                        <SelectContent>{affiliates.map(a => <SelectItem key={a.id} value={a.id}>{a.username}</SelectItem>)}</SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2"><Label>Offer</Label>
                                    <Select value={newLink.offer_id} onValueChange={v=>setNewLink({...newLink, offer_id: v})}>
                                        <SelectTrigger><SelectValue placeholder="Select Offer" /></SelectTrigger>
                                        <SelectContent>{offers.map(o => <SelectItem key={o.id} value={o.id}>{o.name}</SelectItem>)}</SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleCreateLink} className="w-full">Generate</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Tracking URL</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader>
                        <TableBody>{links.map(l => (
                            <TableRow key={l.id}>
                                <TableCell>{l.name}</TableCell>
                                <TableCell className="font-mono text-xs text-muted-foreground truncate max-w-md">{l.url}</TableCell>
                                <TableCell className="text-right">
                                    <Button variant="ghost" size="sm" onClick={() => {navigator.clipboard.writeText(l.url); toast.success("Copied");}}><Copy className="w-4 h-4" /></Button>
                                </TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* PAYOUTS */}
            <TabsContent value="payouts" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isPayoutOpen} onOpenChange={setIsPayoutOpen}>
                        <DialogTrigger asChild>
                          <Button disabled title="Not available in this environment">
                            <Plus className="w-4 h-4 mr-2" /> Record Payout
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Issue Payout</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Affiliate</Label>
                                    <Select value={newPayout.affiliate_id} onValueChange={v=>setNewPayout({...newPayout, affiliate_id: v})}>
                                        <SelectTrigger><SelectValue placeholder="Select Partner" /></SelectTrigger>
                                        <SelectContent>{affiliates.map(a => <SelectItem key={a.id} value={a.id}>{a.username}</SelectItem>)}</SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2"><Label>Amount ($)</Label><Input type="number" value={newPayout.amount} onChange={e=>setNewPayout({...newPayout, amount: e.target.value})} /></div>
                                <Button onClick={handleCreatePayout} className="w-full">Save Payout Record</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Partner</TableHead><TableHead>Amount</TableHead><TableHead>Date</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                        <TableBody>{payouts.map(p => (
                            <TableRow key={p.id}>
                                <TableCell>{p.affiliate_id.substring(0,8)}...</TableCell>
                                <TableCell className="font-bold">${p.amount}</TableCell>
                                <TableCell>{new Date(p.created_at).toLocaleDateString()}</TableCell>
                                <TableCell><Badge variant="outline">{p.status}</Badge></TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* CREATIVES */}
            <TabsContent value="creatives" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isCreativeOpen} onOpenChange={setIsCreativeOpen}>
                        <DialogTrigger asChild>
                          <Button disabled title="Not available in this environment">
                            <Plus className="w-4 h-4 mr-2" /> Add Creative
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Upload Asset</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Name</Label><Input value={newCreative.name} onChange={e=>setNewCreative({...newCreative, name: e.target.value})} /></div>
                                <div className="space-y-2"><Label>URL</Label><Input value={newCreative.url} onChange={e=>setNewCreative({...newCreative, url: e.target.value})} placeholder="https://..." /></div>
                                <Button onClick={handleCreateCreative} className="w-full">Add</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {creatives.map(c => (
                        <Card key={c.id} className="overflow-hidden">
                            <div className="aspect-video bg-secondary flex items-center justify-center text-muted-foreground">
                                {c.preview_url ? <img src={c.preview_url} alt={c.name} className="w-full h-full object-cover" /> : <ImageIcon className="w-8 h-8" />}
                            </div>
                            <div className="p-2 text-sm font-medium truncate">{c.name}</div>
                        </Card>
                    ))}
                </div>
            </TabsContent>
        </Tabs>
    </div>
    </RequireFeature>
  );
};

export { AffiliateManagement };
