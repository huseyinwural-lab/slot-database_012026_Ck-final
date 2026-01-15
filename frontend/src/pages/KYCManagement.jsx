import React, { useCallback, useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { FileText, CheckCircle, XCircle, Clock, ShieldAlert, History, ZoomIn, Download } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';

const KYCManagement = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [stats, setStats] = useState(null);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [rejectReason, setRejectReason] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === 'dashboard') {
        const res = await api.get('/v1/kyc/dashboard');
        setStats(res.data);
      } else if (activeTab === 'queue') {
        const res = await api.get('/v1/kyc/queue');
        setQueue(res.data);
      }
    } catch (err) {
      toast.error("Load failed");
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleReview = async (doc, status) => {
    try {
        await api.post(`/v1/kyc/documents/${doc.id}/review`, { 
            status, 
            reason: status === 'rejected' ? rejectReason : null 
        });
        toast.success(`Document ${status}`);
        setSelectedDoc(null);
        fetchData();
    } catch (err) { toast.error("Action failed"); }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">KYC Verification Center</h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
                <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
                <TabsTrigger value="queue">Verification Queue</TabsTrigger>
                <TabsTrigger value="rules">Rules & Levels</TabsTrigger>
            </TabsList>

            <TabsContent value="dashboard" className="mt-6">
                {stats ? (
                    <div className="space-y-6">
                        <div className="grid gap-4 md:grid-cols-4">
                            <Card>
                                <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Pending</CardTitle></CardHeader>
                                <CardContent><div className="text-2xl font-bold text-yellow-500">{stats.pending_count}</div></CardContent>
                            </Card>
                            <Card>
                                <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">In Review</CardTitle></CardHeader>
                                <CardContent><div className="text-2xl font-bold text-blue-500">{stats.in_review_count}</div></CardContent>
                            </Card>
                            <Card>
                                <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Approved Today</CardTitle></CardHeader>
                                <CardContent><div className="text-2xl font-bold text-green-500">{stats.approved_today}</div></CardContent>
                            </Card>
                            <Card>
                                <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">High Risk</CardTitle></CardHeader>
                                <CardContent><div className="text-2xl font-bold text-red-500">{stats.high_risk_pending}</div></CardContent>
                            </Card>
                        </div>
                        <div className="grid md:grid-cols-2 gap-6">
                            <Card>
                                <CardHeader><CardTitle>Level Distribution</CardTitle></CardHeader>
                                <CardContent>
                                    {Object.entries(stats.level_distribution).map(([k, v]) => (
                                        <div key={k} className="flex justify-between py-2 border-b last:border-0">
                                            <span>{k}</span><span className="font-mono font-bold">{v} users</span>
                                        </div>
                                    ))}
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader><CardTitle>SLA Performance</CardTitle></CardHeader>
                                <CardContent className="flex items-center justify-center h-40">
                                    <div className="text-center">
                                        <div className="text-4xl font-bold">{stats.avg_review_time_mins} min</div>
                                        <div className="text-muted-foreground">Avg Review Time</div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                ) : <div>Loading stats...</div>}
            </TabsContent>

            <TabsContent value="queue" className="mt-6">
                <Card>
                    <CardHeader><CardTitle>Pending Documents</CardTitle></CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader><TableRow><TableHead>User</TableHead><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>Submitted</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {queue.map(doc => (
                                    <TableRow key={doc.id}>
                                        <TableCell className="font-medium">{doc.player_username}</TableCell>
                                        <TableCell className="capitalize">{doc.type.replace('_', ' ')}</TableCell>
                                        <TableCell><Badge variant="outline">{doc.status}</Badge></TableCell>
                                        <TableCell>{new Date(doc.uploaded_at).toLocaleString()}</TableCell>
                                        <TableCell className="text-right">
                                            <Dialog>
                                                <DialogTrigger asChild>
                                                    <Button size="sm" onClick={() => setSelectedDoc(doc)}>Review</Button>
                                                </DialogTrigger>
                                                <DialogContent className="max-w-3xl">
                                                    <DialogHeader><DialogTitle>Document Review</DialogTitle></DialogHeader>
                                                    <div className="grid md:grid-cols-2 gap-6 py-4">
                                                        <div className="border rounded bg-black/50 flex items-center justify-center min-h-[300px]">
                                                            {/* Placeholder for Image */}
                                                            <div className="text-center">
                                                                <FileText className="w-12 h-12 mx-auto mb-2 text-muted-foreground" />
                                                                <p>Preview: {doc.file_url}</p>
                                                                {(() => {
                                                                  const downloadUrl = doc.download_url;
                                                                  const isPlaceholder =
                                                                    !downloadUrl ||
                                                                    String(downloadUrl).includes('via.placeholder.com') ||
                                                                    String(downloadUrl).includes('placehold.co');

                                                                  const isAvailable = !isPlaceholder;

                                                                  return (
                                                                    <Button
                                                                      variant="link"
                                                                      size="sm"
                                                                      disabled={!isAvailable}
                                                                      title={
                                                                        !isAvailable
                                                                          ? 'Document file not available'
                                                                          : 'Download'
                                                                      }
                                                                      onClick={async () => {
                                                                        if (!isAvailable) return;
                                                                        try {
                                                                          // Minimal, robust approach:
                                                                          // Use native anchor navigation to trigger attachment download.
                                                                          const a = document.createElement('a');
                                                                          a.href = downloadUrl;
                                                                          a.target = '_blank';
                                                                          a.rel = 'noopener noreferrer';
                                                                          document.body.appendChild(a);
                                                                          a.click();
                                                                          a.remove();
                                                                        } catch (e) {
                                                                          const status = e?.response?.status;
                                                                          toast.error(
                                                                            `Document download failed${status ? ` (${status})` : ''}`
                                                                          );
                                                                        }
                                                                      }}
                                                                    >
                                                                      <Download className="w-4 h-4 mr-1" /> Download
                                                                    </Button>
                                                                  );
                                                                })()}
                                                            </div>
                                                        </div>
                                                        <div className="space-y-4">
                                                            <div>
                                                                <Label>User</Label>
                                                                <div className="font-bold text-lg">{doc.player_username}</div>
                                                            </div>
                                                            <div>
                                                                <Label>Document Type</Label>
                                                                <div className="capitalize">{doc.type.replace('_', ' ')}</div>
                                                            </div>
                                                            <div>
                                                                <Label>Rejection Reason (if rejecting)</Label>
                                                                <Textarea value={rejectReason} onChange={e => setRejectReason(e.target.value)} placeholder="Explain why..." />
                                                            </div>
                                                            <div className="grid grid-cols-2 gap-4 pt-4">
                                                                <Button variant="destructive" onClick={() => handleReview(doc, 'rejected')}>
                                                                    <XCircle className="w-4 h-4 mr-2" /> Reject
                                                                </Button>
                                                                <Button className="bg-green-600 hover:bg-green-700" onClick={() => handleReview(doc, 'approved')}>
                                                                    <CheckCircle className="w-4 h-4 mr-2" /> Approve
                                                                </Button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </DialogContent>
                                            </Dialog>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>

            <TabsContent value="rules" className="mt-6">
                <Card>
                    <CardHeader><CardTitle>KYC Levels</CardTitle><CardDescription>Configuration</CardDescription></CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="p-4 border rounded">
                                <div className="font-bold">Level 1 - Basic</div>
                                <div className="text-sm text-muted-foreground">Req: ID Card</div>
                            </div>
                            <div className="p-4 border rounded">
                                <div className="font-bold">Level 2 - Verified</div>
                                <div className="text-sm text-muted-foreground">Req: ID + Address Proof</div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </TabsContent>
        </Tabs>
    </div>
  );
};

export default KYCManagement;
