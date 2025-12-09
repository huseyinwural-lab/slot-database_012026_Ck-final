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
import { Users, Target, Link as LinkIcon, DollarSign, Image as ImageIcon, BarChart, Handshake, Plus } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

const AffiliateManagement = () => {
  const [activeTab, setActiveTab] = useState("partners");
  const [affiliates, setAffiliates] = useState([]);
  const [offers, setOffers] = useState([]);
  const [links, setLinks] = useState([]);
  const [payouts, setPayouts] = useState([]);
  
  // Create State
  const [newAffiliate, setNewAffiliate] = useState({ username: '', email: '', company_name: '', model: 'revshare' });
  const [isAddOpen, setIsAddOpen] = useState(false);

  const fetchData = async () => {
    try {
        if (activeTab === 'partners') setAffiliates((await api.get('/v1/affiliates')).data);
        if (activeTab === 'offers') setOffers((await api.get('/v1/affiliates/offers')).data);
        if (activeTab === 'links') setLinks((await api.get('/v1/affiliates/links')).data);
        if (activeTab === 'payouts') setPayouts((await api.get('/v1/affiliates/payouts')).data);
    } catch (err) { toast.error("Load failed"); }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  const handleCreateAffiliate = async () => {
    try {
        await api.post('/v1/affiliates', newAffiliate);
        setIsAddOpen(false);
        fetchData();
        toast.success("Affiliate Created");
    } catch { toast.error("Failed"); }
  };

  const handleStatus = async (id, status) => {
    try {
        await api.put(`/v1/affiliates/${id}/status`, { status });
        toast.success("Status Updated");
        fetchData();
    } catch { toast.error("Failed"); }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Affiliate Program</h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
                <TabsTrigger value="partners"><Users className="w-4 h-4 mr-2" /> Partners</TabsTrigger>
                <TabsTrigger value="offers"><Target className="w-4 h-4 mr-2" /> Offers</TabsTrigger>
                <TabsTrigger value="links"><LinkIcon className="w-4 h-4 mr-2" /> Tracking</TabsTrigger>
                <TabsTrigger value="payouts"><DollarSign className="w-4 h-4 mr-2" /> Payouts</TabsTrigger>
                <TabsTrigger value="reports"><BarChart className="w-4 h-4 mr-2" /> Reports</TabsTrigger>
            </TabsList>

            <TabsContent value="partners" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                        <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Affiliate</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>New Partner</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Company / Username</Label><Input value={newAffiliate.username} onChange={e=>setNewAffiliate({...newAffiliate, username: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Email</Label><Input value={newAffiliate.email} onChange={e=>setNewAffiliate({...newAffiliate, email: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Model</Label>
                                    <Select value={newAffiliate.model} onValueChange={v=>setNewAffiliate({...newAffiliate, model: v})}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="revshare">RevShare</SelectItem><SelectItem value="cpa">CPA</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleCreateAffiliate} className="w-full">Create</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card>
                    <CardContent className="pt-6">
                        <Table>
                            <TableHeader><TableRow><TableHead>Partner</TableHead><TableHead>Email</TableHead><TableHead>Group</TableHead><TableHead>Balance</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {affiliates.map(a => (
                                    <TableRow key={a.id}>
                                        <TableCell className="font-medium">{a.company_name || a.username}</TableCell>
                                        <TableCell>{a.email}</TableCell>
                                        <TableCell>{a.group}</TableCell>
                                        <TableCell className="font-bold text-green-500">${a.balance}</TableCell>
                                        <TableCell><Badge variant={a.status==='active'?'default':'secondary'}>{a.status}</Badge></TableCell>
                                        <TableCell className="text-right">
                                            {a.status === 'pending' && (
                                                <Button size="sm" onClick={() => handleStatus(a.id, 'active')}>Approve</Button>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>

            <TabsContent value="offers" className="mt-4">
                <Card>
                    <CardContent className="pt-6">
                        <Table>
                            <TableHeader><TableRow><TableHead>Offer Name</TableHead><TableHead>Model</TableHead><TableHead>Default Rate</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {offers.map(o => (
                                    <TableRow key={o.id}>
                                        <TableCell>{o.name}</TableCell>
                                        <TableCell className="uppercase">{o.model}</TableCell>
                                        <TableCell>
                                            {o.model === 'cpa' ? `$${o.default_commission.cpa_amount}` : `${o.default_commission.revshare_percentage}%`}
                                        </TableCell>
                                        <TableCell><Badge variant="outline">{o.status}</Badge></TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>

            <TabsContent value="links" className="mt-4">
                <div className="p-10 text-center border border-dashed rounded text-muted-foreground">
                    Link Generator & Tracking Dashboard coming soon...
                </div>
            </TabsContent>

            <TabsContent value="payouts" className="mt-4">
                <Card>
                    <CardContent className="pt-6">
                        <Table>
                            <TableHeader><TableRow><TableHead>Affiliate</TableHead><TableHead>Amount</TableHead><TableHead>Period</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {payouts.length === 0 && <TableRow><TableCell colSpan={4} className="text-center">No payout history</TableCell></TableRow>}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>
        </Tabs>
    </div>
  );
};

export { AffiliateManagement };
