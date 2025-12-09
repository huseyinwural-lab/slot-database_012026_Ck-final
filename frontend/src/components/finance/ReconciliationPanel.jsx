import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Upload, CheckCircle, AlertTriangle, FileText, Settings, PlayCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import api from '../../services/api';

const ReconciliationPanel = () => {
    const [reports, setReports] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [provider, setProvider] = useState('Stripe');
    const [loading, setLoading] = useState(false);
    
    // Scheduler
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [schedule, setSchedule] = useState({ frequency: 'daily', auto_fetch_enabled: false });

    const fetchHistory = async () => {
        try {
            const res = await api.get('/v1/finance/reconciliation');
            setReports(res.data);
        } catch {}
    };

    useEffect(() => { fetchHistory(); }, []);

    const handleUpload = async () => {
        if (!selectedFile) return;
        setLoading(true);
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        try {
            await api.post(`/v1/finance/reconciliation/upload?provider=${provider}`, formData);
            toast.success("File Processed");
            fetchHistory();
        } catch {
            toast.error("Processing Failed");
        } finally {
            setLoading(false);
        }
    };

    const handleRunAuto = async () => {
        try {
            await api.post('/v1/finance/reconciliation/run-auto', { provider });
            toast.success("Auto-fetch initiated");
            fetchHistory();
        } catch { toast.error("Auto-fetch failed"); }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setIsSettingsOpen(true)}>
                    <Settings className="w-4 h-4 mr-2" /> Auto-Scheduler
                </Button>
                <Button onClick={handleRunAuto}>
                    <PlayCircle className="w-4 h-4 mr-2" /> Run Auto-Match Now
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Upload Area */}
                <Card className="md:col-span-1">
                    <CardHeader><CardTitle>Upload Statement</CardTitle><CardDescription>CSV from Provider</CardDescription></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label>Provider</Label>
                            <Select value={provider} onValueChange={setProvider}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Stripe">Stripe</SelectItem>
                                    <SelectItem value="Papara">Papara</SelectItem>
                                    <SelectItem value="CoinPayments">CoinPayments</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>File (CSV)</Label>
                            <Input type="file" accept=".csv" onChange={e => setSelectedFile(e.target.files[0])} />
                            <p className="text-[10px] text-muted-foreground">Required cols: tx_id, amount, currency</p>
                        </div>
                        <Button className="w-full" onClick={handleUpload} disabled={loading}>
                            <Upload className="w-4 h-4 mr-2" /> 
                            {loading ? 'Processing...' : 'Start Reconciliation'}
                        </Button>
                    </CardContent>
                </Card>

                {/* History */}
                <Card className="md:col-span-2">
                    <CardHeader><CardTitle>Recent Reconciliations</CardTitle></CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Date</TableHead><TableHead>Mismatches</TableHead><TableHead>Alerts</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {reports.map(r => (
                                    <TableRow key={r.id}>
                                        <TableCell>{r.provider_name}</TableCell>
                                        <TableCell>{new Date(r.created_at).toLocaleDateString()}</TableCell>
                                        <TableCell className={r.mismatches > 0 ? "text-red-500 font-bold" : "text-green-600"}>{r.mismatches}</TableCell>
                                        <TableCell>{r.fraud_alerts > 0 ? <Badge variant="destructive">{r.fraud_alerts} Fraud</Badge> : '-'}</TableCell>
                                        <TableCell><Badge>{r.status}</Badge></TableCell>
                                    </TableRow>
                                ))}
                                {reports.length === 0 && <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">No reports yet.</TableCell></TableRow>}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>

            {/* Mismatch Detail Mock */}
            <Card className="border-red-200 bg-red-50/20">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-700"><AlertTriangle className="w-5 h-5"/> Mismatch & Fraud Report</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Ref ID</TableHead><TableHead>Currency</TableHead><TableHead>DB Amount</TableHead><TableHead>Prov Amount</TableHead><TableHead>Diff</TableHead><TableHead>Note</TableHead></TableRow></TableHeader>
                        <TableBody>
                            <TableRow>
                                <TableCell><Badge variant="destructive">Potential Fraud</Badge></TableCell>
                                <TableCell className="font-mono">tx_999_fraud</TableCell>
                                <TableCell>USD</TableCell>
                                <TableCell>-</TableCell>
                                <TableCell>$5,500.00</TableCell>
                                <TableCell className="text-red-600 font-bold">$5,500.00</TableCell>
                                <TableCell className="text-xs">Missing in DB (High Value)</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell><Badge className="bg-orange-500">FX Mismatch</Badge></TableCell>
                                <TableCell className="font-mono">tx_888_fx</TableCell>
                                <TableCell>EUR (1.10)</TableCell>
                                <TableCell>$115.00</TableCell>
                                <TableCell>€100.00 ($110.00)</TableCell>
                                <TableCell className="text-red-600">-$5.00</TableCell>
                                <TableCell className="text-xs">Exceeds 2% tolerance</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell><Badge variant="secondary">Adjustment</Badge></TableCell>
                                <TableCell className="font-mono">tx_777_adj</TableCell>
                                <TableCell>USD</TableCell>
                                <TableCell>$50.00</TableCell>
                                <TableCell>$50.00</TableCell>
                                <TableCell className="text-green-600">0.00</TableCell>
                                <TableCell className="text-xs">Matched with Manual Adj #adj_123</TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Auto-Scheduler Settings</DialogTitle></DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="flex items-center justify-between">
                            <Label>Enable Auto-Fetch from PSP APIs</Label>
                            <Switch checked={schedule.auto_fetch_enabled} onCheckedChange={c => setSchedule({...schedule, auto_fetch_enabled: c})} />
                        </div>
                        <div className="space-y-2">
                            <Label>Frequency</Label>
                            <Select value={schedule.frequency} onValueChange={v => setSchedule({...schedule, frequency: v})}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="hourly">Hourly</SelectItem>
                                    <SelectItem value="daily">Daily</SelectItem>
                                    <SelectItem value="weekly">Weekly</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>API Credentials</Label>
                            <Input type="password" value="********" disabled />
                            <p className="text-[10px] text-muted-foreground">Managed in Vault</p>
                        </div>
                    </div>
                    <DialogFooter><Button onClick={() => {toast.success("Saved"); setIsSettingsOpen(false)}}>Save Configuration</Button></DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default ReconciliationPanel;
