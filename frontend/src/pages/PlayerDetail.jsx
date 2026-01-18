import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { ArrowLeft, Save, Ban, CheckCircle, Upload, DollarSign, Shield, FileText, History, Activity, MessageSquare, Gift } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const PlayerDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [player, setPlayer] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [kycDocs, setKycDocs] = useState([]);
  const [logs, setLogs] = useState([]);
  const [bonuses, setBonuses] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Balance Adjustment State
  const [isAdjOpen, setIsAdjOpen] = useState(false);
  const [adjForm, setAdjForm] = useState({ amount: 0, type: 'real', note: '' });

  const fetchData = useCallback(async () => {
    try {
      const [pRes, tRes, kRes, lRes, bRes] = await Promise.all([
        api.get(`/v1/players/${id}`),
        api.get(`/v1/players/${id}/transactions`),
        api.get(`/v1/players/${id}/kyc`),
        api.get(`/v1/players/${id}/logs`),
        api.get(`/v1/bonuses/players/${id}`),
      ]);
      setPlayer(pRes.data);
      setTransactions(tRes.data);
      setKycDocs(kRes.data);
      setLogs(lRes.data);
      setBonuses(bRes.data || []);
    } catch (err) {
      toast.error("Failed to load player data");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleStatusChange = async (newStatus) => {
    try {
        await api.put(`/v1/players/${id}`, { status: newStatus });
        setPlayer({ ...player, status: newStatus });
        toast.success(`Player ${newStatus}`);
    } catch (err) { toast.error("Failed"); }
  };

  const handleBalanceAdj = async () => {
    try {
        const res = await api.post(`/v1/players/${id}/balance`, adjForm);
        toast.success(res.data.message);
        setIsAdjOpen(false);
        fetchData();
    } catch (err) { toast.error("Adjustment failed"); }
  };

  const handleKycReview = async (docId, status) => {
    try {
        await api.post(`/v1/kyc/${docId}/review`, { status });
        toast.success(`Document ${status}`);
        fetchData();
    } catch (err) { toast.error("Failed"); }
  };

  if (loading) return <div>Loading...</div>;
  if (!player) return <div>Player not found</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/players')}>
            <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
            <div className="flex items-center gap-3">
                <h2 className="text-3xl font-bold tracking-tight">{player.username}</h2>
                <Badge variant={player.risk_score === 'high' ? 'destructive' : 'outline'}>{player.risk_score} risk</Badge>
            </div>
            <p className="text-muted-foreground">{player.email} • {player.country} • Joined {new Date(player.registered_at).toLocaleDateString()}</p>
        </div>
        <div className="ml-auto flex gap-2">
            <Dialog open={isAdjOpen} onOpenChange={setIsAdjOpen}>
                <DialogTrigger asChild>
                    <Button variant="outline"><DollarSign className="w-4 h-4 mr-2" /> Adjust Balance</Button>
                </DialogTrigger>
                <DialogContent>
                    <DialogHeader><DialogTitle>Manual Balance Adjustment</DialogTitle></DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Amount (+/-)</Label>
                            <Input type="number" value={adjForm.amount} onChange={e => setAdjForm({...adjForm, amount: e.target.value})} />
                        </div>
                        <div className="space-y-2">
                            <Label>Wallet</Label>
                            <Select value={adjForm.type} onValueChange={v => setAdjForm({...adjForm, type: v})}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="real">Real Money</SelectItem>
                                    <SelectItem value="bonus">Bonus Money</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Admin Note (Mandatory)</Label>
                            <Textarea value={adjForm.note} onChange={e => setAdjForm({...adjForm, note: e.target.value})} />
                        </div>
                        <Button onClick={handleBalanceAdj} className="w-full">Process Adjustment</Button>
                    </div>
                </DialogContent>
            </Dialog>

            {player.status === 'active' ? (
                <Button variant="destructive" onClick={() => handleStatusChange('suspended')}>
                    <Ban className="w-4 h-4 mr-2" /> Suspend Account
                </Button>
            ) : (
                <Button variant="default" onClick={() => handleStatusChange('active')}>
                    <CheckCircle className="w-4 h-4 mr-2" /> Unfreeze Account
                </Button>
            )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Sidebar Info */}
        <Card className="md:col-span-1 h-fit">
            <CardHeader><CardTitle>Wallet</CardTitle></CardHeader>
            <CardContent className="space-y-4">
                <div className="p-4 bg-green-950/20 border border-green-900/50 rounded-lg">
                    <Label className="text-green-500">Real Balance</Label>
                    <div className="text-2xl font-bold text-green-400">${player.balance_real.toFixed(2)}</div>
                </div>
                <div className="p-4 bg-yellow-950/20 border border-yellow-900/50 rounded-lg">
                    <Label className="text-yellow-500">Bonus Balance</Label>
                    <div className="text-xl font-bold text-yellow-400">${player.balance_bonus.toFixed(2)}</div>
                </div>
                <div className="space-y-1">
                    <div className="flex justify-between text-sm"><span>VIP Level</span><span>{player.vip_level}</span></div>
                    <div className="flex justify-between text-sm"><span>KYC Status</span><span className="uppercase">{player.kyc_status}</span></div>
                </div>
                <div className="pt-4 border-t">
                    <Label className="mb-2 block">Tags</Label>
                    <div className="flex flex-wrap gap-2">
                        {player.tags.map(t => <Badge key={t} variant="secondary">{t}</Badge>)}
                        <Badge variant="outline" className="cursor-pointer">+ Add</Badge>
                    </div>
                </div>
            </CardContent>
        </Card>

        {/* Tabs Area */}
        <div className="md:col-span-3">
            <Tabs defaultValue="profile">
                <TabsList className="grid w-full grid-cols-7">
                    <TabsTrigger value="profile"><UserIcon className="w-4 h-4 mr-2 hidden md:block" /> Profile</TabsTrigger>
                    <TabsTrigger value="kyc"><FileText className="w-4 h-4 mr-2 hidden md:block" /> KYC</TabsTrigger>
                    <TabsTrigger value="finance"><DollarSign className="w-4 h-4 mr-2 hidden md:block" /> Finance</TabsTrigger>
                    <TabsTrigger value="bonuses"><Gift className="w-4 h-4 mr-2 hidden md:block" /> Bonuses</TabsTrigger>
                    <TabsTrigger value="games"><Activity className="w-4 h-4 mr-2 hidden md:block" /> Games</TabsTrigger>
                    <TabsTrigger value="logs"><History className="w-4 h-4 mr-2 hidden md:block" /> Logs</TabsTrigger>
                    <TabsTrigger value="notes"><MessageSquare className="w-4 h-4 mr-2 hidden md:block" /> Notes</TabsTrigger>
                </TabsList>
                
                <TabsContent value="profile" className="mt-6 space-y-6">
                    <Card>
                        <CardHeader><CardTitle>Personal Information</CardTitle></CardHeader>
                        <CardContent className="grid md:grid-cols-2 gap-6">
                            <div className="space-y-2"><Label>First Name</Label><Input value={player.first_name || ''} readOnly /></div>
                            <div className="space-y-2"><Label>Last Name</Label><Input value={player.last_name || ''} readOnly /></div>
                            <div className="space-y-2"><Label>Email</Label><Input value={player.email} readOnly /></div>
                            <div className="space-y-2"><Label>Phone</Label><Input value={player.phone || '-'} readOnly /></div>
                            <div className="space-y-2"><Label>Address</Label><Input value={player.address || '-'} readOnly /></div>
                            <div className="space-y-2"><Label>Country</Label><Input value={player.country} readOnly /></div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="kyc" className="mt-6">
                    <Card>
                        <CardHeader><CardTitle>Documents</CardTitle></CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Date</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader>
                                <TableBody>
                                    {kycDocs.length === 0 && <TableRow><TableCell colSpan={4} className="text-center">No documents</TableCell></TableRow>}
                                    {kycDocs.map(doc => (
                                        <TableRow key={doc.id}>
                                            <TableCell className="capitalize font-medium">{doc.type.replace('_', ' ')}</TableCell>
                                            <TableCell>{new Date(doc.uploaded_at).toLocaleDateString()}</TableCell>
                                            <TableCell><Badge variant={doc.status === 'approved' ? 'default' : 'secondary'}>{doc.status}</Badge></TableCell>
                                            <TableCell className="text-right">
                                                {doc.status === 'pending' && (
                                                    <div className="flex justify-end gap-2">
                                                        <Button size="sm" onClick={() => handleKycReview(doc.id, 'approved')}>Approve</Button>
                                                        <Button size="sm" variant="destructive" onClick={() => handleKycReview(doc.id, 'rejected')}>Reject</Button>
                                                    </div>
                                                )}
                                                <Button variant="link" size="sm">View File</Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="finance" className="mt-6">
                    <Card>
                        <CardHeader><CardTitle>Transaction History</CardTitle></CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Type</TableHead><TableHead>Method</TableHead><TableHead>Amount</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                                <TableBody>
                                    {transactions.map(tx => (
                                        <TableRow key={tx.id}>
                                            <TableCell>{new Date(tx.created_at).toLocaleString()}</TableCell>
                                            <TableCell className="uppercase text-xs font-bold">{tx.type}</TableCell>
                                            <TableCell>{tx.method}</TableCell>
                                            <TableCell className={tx.type === 'deposit' || tx.type === 'adjustment' ? "text-green-500" : "text-red-500"}>
                                                ${tx.amount}
                                            </TableCell>
                                            <TableCell><Badge variant="outline">{tx.status}</Badge></TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="bonuses" className="mt-6">
                    <Card>
                        <CardHeader><CardTitle>Bonus History</CardTitle></CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Type</TableHead><TableHead>Amount</TableHead><TableHead>Status</TableHead><TableHead>Expires</TableHead></TableRow></TableHeader>
                                <TableBody>
                                    {bonuses.length === 0 && <TableRow><TableCell colSpan={5} className="text-center">No bonuses</TableCell></TableRow>}
                                    {bonuses.map(bonus => (
                                        <TableRow key={bonus.id}>
                                            <TableCell>{new Date(bonus.created_at).toLocaleDateString()}</TableCell>
                                            <TableCell className="capitalize">{bonus.type}</TableCell>
                                            <TableCell className="text-green-500">${bonus.amount}</TableCell>
                                            <TableCell><Badge variant={bonus.status === 'active' ? 'default' : 'secondary'}>{bonus.status}</Badge></TableCell>
                                            <TableCell>{bonus.expires_at ? new Date(bonus.expires_at).toLocaleDateString() : 'Never'}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="games" className="mt-6">
                    <Card>
                        <CardHeader><CardTitle>Game Activity</CardTitle></CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Game</TableHead><TableHead>Bet</TableHead><TableHead>Win</TableHead><TableHead>Result</TableHead></TableRow></TableHeader>
                                <TableBody>
                                    <TableRow><TableCell colSpan={5} className="text-center">No game activity</TableCell></TableRow>
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="logs" className="mt-6">
                    <Card>
                        <CardHeader><CardTitle>Login & Security Logs</CardTitle></CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>IP Address</TableHead><TableHead>Location</TableHead><TableHead>Device</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                                <TableBody>
                                    {logs.map((log, i) => (
                                        <TableRow key={i}>
                                            <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                                            <TableCell className="font-mono text-xs">{log.ip_address}</TableCell>
                                            <TableCell>{log.location}</TableCell>
                                            <TableCell className="text-xs text-muted-foreground">{log.device_info}</TableCell>
                                            <TableCell><Badge variant={log.status === 'success' ? 'default' : 'destructive'}>{log.status}</Badge></TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="notes" className="mt-6">
                    <Card>
                        <CardHeader><CardTitle>Admin Notes</CardTitle></CardHeader>
                        <CardContent>
                            <Textarea placeholder="Add a note about this player..." className="mb-4" />
                            <Button>Add Note</Button>
                            <div className="mt-6 space-y-4">
                                <div className="p-4 border rounded bg-muted/50">
                                    <p className="text-sm">User requested high roller bonus via chat. Approved by Manager.</p>
                                    <p className="text-xs text-muted-foreground mt-2">By Admin • 2 days ago</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
      </div>
    </div>
  );
};

// Simple Icon Wrapper for Tabs
const UserIcon = (props) => <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>;

export default PlayerDetail;
