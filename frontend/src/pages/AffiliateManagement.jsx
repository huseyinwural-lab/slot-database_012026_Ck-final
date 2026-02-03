import React, { useEffect, useState } from 'react';
import useTableState from '@/hooks/useTableState';
import { TableEmptyState, TableErrorState, TableSkeletonRows } from '@/components/TableState';
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
import AffiliateReports from '../components/AffiliateReports';

const AffiliateManagement = () => {
  const [activeTab, setActiveTab] = useState("partners");

  const partnersTable = useTableState([]);
  const offersTable = useTableState([]);
  const linksTable = useTableState([]);
  const payoutsTable = useTableState([]);
  const creativesTable = useTableState([]);

  const affiliates = partnersTable.rows;
  const offers = offersTable.rows;
  const links = linksTable.rows;
  const payouts = payoutsTable.rows;
  const creatives = creativesTable.rows;
  
  // Dialog States
  const [isAffOpen, setIsAffOpen] = useState(false);
  const [isOfferOpen, setIsOfferOpen] = useState(false);
  const [isLinkOpen, setIsLinkOpen] = useState(false);
  const [isPayoutOpen, setIsPayoutOpen] = useState(false);
  const [isCreativeOpen, setIsCreativeOpen] = useState(false);

  // Forms
  const [newAffiliate, setNewAffiliate] = useState({ username: '', email: '', company_name: '', model: 'revshare' });
  const [newOffer, setNewOffer] = useState({ name: '', model: 'cpa', currency: 'USD', cpa_amount: 50, min_deposit: 20 });
  const [newLink, setNewLink] = useState({ affiliate_id: '', offer_id: '', landing_path: '/', reason: 'initial link' });
  const [newPayout, setNewPayout] = useState({ affiliate_id: '', amount: 0, currency: 'USD', method: 'bank', reference: '', reason: 'monthly payout' });
  const [newCreative, setNewCreative] = useState({ name: '', type: 'banner', url: '' });

  const fetchData = useCallback(async () => {
    const map501 = (table, status) => {
      if (status === 501) {
        table.setError('coming_soon');
        return true;
      }
      if (status === 500 || status === 502 || status === 503) {
        table.setError('db_unavailable');
        return true;
      }
      return false;
    };

    try {
      if (activeTab === 'partners') {
        await partnersTable.run(async () => {
          const res = await api.get('/v1/affiliates/partners');
          partnersTable.setRows(res.data || []);
        });
      }

      if (activeTab === 'offers') {
        await offersTable.run(async () => {
          const res = await api.get('/v1/affiliates/offers');
          offersTable.setRows(res.data || []);
        });
      }

      if (activeTab === 'links') {
        await linksTable.run(async () => {
          const res = await api.get('/v1/affiliates/partners');
          const partners = res.data || [];

          const all = [];
          for (const p of partners) {
            try {
              const r = await api.get(`/v1/affiliates/${p.id}/links`);
              for (const l of (r.data || [])) {
                all.push(l);
              }
            } catch {
              // ignore
            }
          }

          linksTable.setRows(all);
          partnersTable.setRows(partners); // dropdown

          const offersRes = await api.get('/v1/affiliates/offers');
          offersTable.setRows(offersRes.data || []); // dropdown
        });
      }

      if (activeTab === 'payouts') {
        await payoutsTable.run(async () => {
          const pRes = await api.get('/v1/affiliates/payouts');
          payoutsTable.setRows(pRes.data || []);

          const aRes = await api.get('/v1/affiliates/partners');
          partnersTable.setRows(aRes.data || []);
        });
      }

      if (activeTab === 'creatives') {
        await creativesTable.run(async () => {
          const res = await api.get('/v1/affiliates/creatives');
          creativesTable.setRows(res.data || []);
        });
      }

    } catch (err) {
      const status = err?.response?.status;

      // Convert 501 to comingSoon state (per Phase 2 policy)
      if (activeTab === 'partners') map501(partnersTable, status);
      if (activeTab === 'offers') map501(offersTable, status);
      if (activeTab === 'links') map501(linksTable, status);
      if (activeTab === 'payouts') map501(payoutsTable, status);
      if (activeTab === 'creatives') map501(creativesTable, status);

      toast.error('Unexpected error');
    }
  }, [activeTab, partnersTable, offersTable, linksTable, payoutsTable, creativesTable]);

  useEffect(() => {
    const t = setTimeout(() => {
      fetchData();
    }, 0);
    return () => clearTimeout(t);
  }, [activeTab, fetchData]);

  // Handlers
  const handleCreateAffiliate = async () => {
    try {
      await api.post('/v1/affiliates/partners', { name: newAffiliate.username, email: newAffiliate.email });
      setIsAffOpen(false);
      fetchData();
      toast.success('Partner created');
    } catch (e) {
      toast.error(e?.standardized?.message || e?.standardized?.code || 'Create partner failed');
    }
  };
  const handleCreateOffer = async () => {
    const payload = {
      name: newOffer.name,
      model: newOffer.model,
      currency: (newOffer.currency || 'USD'),
      cpa_amount: newOffer.model === 'cpa' ? Number(newOffer.cpa_amount || 0) : null,
      min_deposit: Number(newOffer.min_deposit || 0) || null,
    };

    try {
      await api.post('/v1/affiliates/offers', payload);
      setIsOfferOpen(false);
      fetchData();
      toast.success('Offer created');
    } catch (e) {
      toast.error(e?.standardized?.message || e?.standardized?.code || 'Create offer failed');
    }
  };
  const handleCreateLink = async () => {
    try {
      const payload = {
        partner_id: newLink.affiliate_id,
        offer_id: newLink.offer_id,
        landing_path: newLink.landing_path || '/',
        reason: newLink.reason || 'initial link',
      };
      const res = await api.post('/v1/affiliates/tracking-links', payload);
      setIsLinkOpen(false);
      fetchData();
      toast.success('Link generated');
      if (res?.data?.tracking_url) {
        try { await navigator.clipboard.writeText(res.data.tracking_url); toast.message('Copied to clipboard'); } catch { /* ignore */ }
      }
    } catch (e) {
      toast.error(e?.standardized?.message || e?.standardized?.code || 'Generate link failed');
    }
  };
  const handleCreatePayout = async () => {
    try {
      const payload = {
        partner_id: newPayout.affiliate_id,
        amount: Number(newPayout.amount || 0),
        currency: (newPayout.currency || 'USD'),
        method: newPayout.method || 'bank',
        reference: newPayout.reference || 'TX',
        reason: newPayout.reason || 'monthly payout',
      };
      await api.post('/v1/affiliates/payouts', payload);
      setIsPayoutOpen(false);
      fetchData();
      toast.success('Payout recorded');
    } catch (e) {
      toast.error(e?.standardized?.message || e?.standardized?.code || 'Record payout failed');
    }
  };
  const handleCreateCreative = async () => {
    try {
      const payload = {
        name: newCreative.name,
        type: newCreative.type,
        url: newCreative.url,
        size: newCreative.size,
        language: newCreative.language,
      };
      await api.post('/v1/affiliates/creatives', payload);
      setIsCreativeOpen(false);
      fetchData();
      toast.success('Creative added');
    } catch (e) {
      toast.error(e?.standardized?.message || e?.standardized?.code || 'Add creative failed');
    }
  };
  const [partnerReasonOpen, setPartnerReasonOpen] = useState(false);
  const [pendingPartnerStatus, setPendingPartnerStatus] = useState(null);

  const handleStatus = async (id, status) => {
    // status here is 'active'|'inactive'
    setPendingPartnerStatus({ id, status });
    setPartnerReasonOpen(true);
  };

  const confirmPartnerStatus = async (reason) => {
    if (!pendingPartnerStatus) return;

    try {
      const url = pendingPartnerStatus.status === 'active'
        ? `/v1/affiliates/partners/${pendingPartnerStatus.id}/activate`
        : `/v1/affiliates/partners/${pendingPartnerStatus.id}/deactivate`;

      await postWithReason(url, reason, {});
      toast.success(`Partner ${pendingPartnerStatus.status === 'active' ? 'activated' : 'deactivated'}`);
      setPartnerReasonOpen(false);
      setPendingPartnerStatus(null);
      fetchData();
    } catch (e) {
      toast.error(e?.standardized?.message || e?.standardized?.code || 'Status update failed');
    }
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
                        <TableBody>
                          {partnersTable.loading ? (
                            <TableSkeletonRows colSpan={5} rows={6} />
                          ) : partnersTable.error ? (
                            partnersTable.error === 'coming_soon' ? (
                              <TableEmptyState colSpan={5} title="Yakında" description="Affiliates servisi güncelleniyor." />
                            ) : (
                              <TableErrorState
                                colSpan={5}
                                title="Veri şu an çekilemiyor"
                                description="Veritabanına şu an ulaşılamıyor, lütfen az sonra tekrar deneyin."
                                onRetry={() => fetchData()}
                              />
                            )
                          ) : affiliates.length === 0 ? (
                            <TableEmptyState
                              colSpan={5}
                              title="Aradığınız kriterlere uygun kayıt bulunamadı"
                              description="Henüz partner yok."
                            />
                          ) : (
                            affiliates.map(a => (
                            <TableRow key={a.id}>
                                <TableCell className="font-medium">{a.company_name || a.username}</TableCell>
                                <TableCell>{a.email}</TableCell>
                                <TableCell className="font-bold text-green-500">${a.balance}</TableCell>
                                <TableCell><Badge variant={a.status==='active'?'default':'secondary'}>{a.status}</Badge></TableCell>
                                <TableCell className="text-right">
                                  {a.status === 'active' ? (
                                    <Button size="sm" variant="outline" onClick={() => handleStatus(a.id, 'inactive')}>Deactivate</Button>
                                  ) : (
                                    <Button size="sm" onClick={() => handleStatus(a.id, 'active')}>Activate</Button>
                                  )}
                                </TableCell>
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
                          <Button>
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
                                <TableCell>{o.model === 'cpa' ? `${o.cpa_amount ?? 0} ${o.currency}` : `0 ${o.currency}`}</TableCell>
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
                              <Button>
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
                                <TableCell>{l.code}</TableCell>
                                <TableCell className="font-mono text-xs text-muted-foreground truncate max-w-md">{l.tracking_url || l.url}</TableCell>
                                <TableCell className="text-right">
                                    <Button variant="ghost" size="sm" onClick={() => {navigator.clipboard.writeText(l.tracking_url || l.url); toast.success("Copied");}}><Copy className="w-4 h-4" /></Button>
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
                          <Button>
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
                          <Button>
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

            {/* REPORTS */}
            <TabsContent value="reports" className="mt-4">
              <AffiliateReports />
            </TabsContent>
        </Tabs>
        
        <ReasonDialog
          open={partnerReasonOpen}
          onOpenChange={(open) => {
            setPartnerReasonOpen(open);
            if (!open) setPendingPartnerStatus(null);
          }}
          onConfirm={confirmPartnerStatus}
          title={pendingPartnerStatus?.status === 'active' ? 'Activate Partner' : 'Deactivate Partner'}
          placeholder="Audit reason"
          confirmText={pendingPartnerStatus?.status === 'active' ? 'Activate' : 'Deactivate'}
        />
    </div>
    </RequireFeature>
  );
};

export { AffiliateManagement };
