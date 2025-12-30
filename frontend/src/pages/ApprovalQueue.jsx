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
import { ListChecks, UserCheck, Shield, ClipboardCheck, History, UserPlus, CheckCircle, XCircle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';

const ApprovalQueue = () => {
  const [activeTab, setActiveTab] = useState("pending");
  const [requests, setRequests] = useState([]);
  const [rules, setRules] = useState([]);
  const [delegations, setDelegations] = useState([]);
  const [selectedReq, setSelectedReq] = useState(null);
  const [note, setNote] = useState("");

  const fetchData = useCallback(async () => {
    try {
      if (activeTab === 'pending' || activeTab === 'approved' || activeTab === 'rejected') {
        const status = activeTab === 'pending' ? 'pending' : activeTab;
        setRequests((await api.get(`/v1/approvals/requests?status=${status}`)).data);
      }
      if (activeTab === 'rules') setRules((await api.get('/v1/approvals/rules')).data);
      if (activeTab === 'delegations') setDelegations((await api.get('/v1/approvals/delegations')).data);
    } catch (err) {
      console.error(err);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAction = async (action) => {
    if (!selectedReq) return;
    try {
        await api.post(`/v1/approvals/requests/${selectedReq.id}/action`, { action, note });
        toast.success(`Request ${action}ed`);
        setSelectedReq(null);
        fetchData();
    } catch { toast.error("Action failed"); }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Approval Queue</h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
                <TabsTrigger value="pending"><ListChecks className="w-4 h-4 mr-2" /> Pending</TabsTrigger>
                <TabsTrigger value="approved"><CheckCircle className="w-4 h-4 mr-2" /> Approved</TabsTrigger>
                <TabsTrigger value="rejected"><XCircle className="w-4 h-4 mr-2" /> Rejected</TabsTrigger>
                <TabsTrigger value="rules"><Shield className="w-4 h-4 mr-2" /> Policies</TabsTrigger>
                <TabsTrigger value="delegations"><UserPlus className="w-4 h-4 mr-2" /> Delegations</TabsTrigger>
            </TabsList>

            {/* REQUEST LISTS */}
            {(activeTab === 'pending' || activeTab === 'approved' || activeTab === 'rejected') && (
                <div className="mt-4 grid md:grid-cols-3 gap-6">
                    <Card className="md:col-span-1">
                        <CardHeader><CardTitle>Requests</CardTitle></CardHeader>
                        <div className="space-y-2 p-4">
                            {requests.length === 0 && <div className="text-center text-muted-foreground">No requests found.</div>}
                            {requests.map(r => (
                                <div key={r.id} onClick={() => setSelectedReq(r)} className={`p-3 border rounded cursor-pointer hover:bg-secondary/50 ${selectedReq?.id === r.id ? 'border-primary bg-secondary/30' : ''}`}>
                                    <div className="flex justify-between mb-1">
                                        <Badge variant="outline" className="uppercase text-[10px]">{r.category}</Badge>
                                        <span className="text-xs text-muted-foreground">{new Date(r.created_at).toLocaleDateString()}</span>
                                    </div>
                                    <div className="font-bold text-sm truncate">{r.action_type.replace(/_/g, ' ')}</div>
                                    <div className="text-xs text-muted-foreground">By: {r.requester_admin}</div>
                                </div>
                            ))}
                        </div>
                    </Card>
                    
                    <Card className="md:col-span-2">
                        {selectedReq ? (
                            <>
                                <CardHeader><CardTitle>Request Detail</CardTitle><CardDescription>ID: {selectedReq.id}</CardDescription></CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div><span className="font-bold">Type:</span> {selectedReq.action_type}</div>
                                        <div><span className="font-bold">Target:</span> {selectedReq.related_entity_id}</div>
                                        <div><span className="font-bold">Requester:</span> {selectedReq.requester_admin}</div>
                                        <div><span className="font-bold">Role:</span> {selectedReq.requester_role}</div>
                                    </div>
                                    {selectedReq.amount && <div className="p-4 bg-secondary/20 rounded font-bold text-lg text-center">Amount: ${selectedReq.amount}</div>}
                                    
                                    {selectedReq.status === 'pending' && (
                                        <div className="pt-4 border-t space-y-4">
                                            <Textarea value={note} onChange={e=>setNote(e.target.value)} placeholder="Approval/Rejection Note..." />
                                            <div className="flex gap-4">
                                                <Button className="w-full bg-green-600 hover:bg-green-700" onClick={() => handleAction('approve')}>Approve</Button>
                                                <Button className="w-full" variant="destructive" onClick={() => handleAction('reject')}>Reject</Button>
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                            </>
                        ) : <div className="flex items-center justify-center h-40 text-muted-foreground">Select a request</div>}
                    </Card>
                </div>
            )}

            {/* RULES */}
            <TabsContent value="rules" className="mt-4">
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Action</TableHead><TableHead>Condition</TableHead><TableHead>Required Role</TableHead><TableHead>SLA</TableHead></TableRow></TableHeader>
                        <TableBody>{rules.map(r => (
                            <TableRow key={r.id}>
                                <TableCell className="font-medium">{r.action_type}</TableCell>
                                <TableCell>{r.condition}</TableCell>
                                <TableCell><Badge>{r.required_role}</Badge></TableCell>
                                <TableCell>{r.sla_hours}h</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* DELEGATIONS */}
            <TabsContent value="delegations" className="mt-4">
                <Card><CardContent className="p-10 text-center">Delegation Management (Coming Soon)</CardContent></Card>
            </TabsContent>
        </Tabs>
    </div>
  );
};

export default ApprovalQueue;
