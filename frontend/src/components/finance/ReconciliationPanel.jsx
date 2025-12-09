import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Upload, CheckCircle, AlertTriangle, FileText } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../services/api';

const ReconciliationPanel = () => {
    const [reports, setReports] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [provider, setProvider] = useState('Stripe');
    const [loading, setLoading] = useState(false);

    const handleUpload = async () => {
        if (!selectedFile) return;
        setLoading(true);
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        try {
            await api.post(`/v1/finance/reconciliation/upload?provider=${provider}`, formData);
            toast.success("File Processed");
            // Refresh list
        } catch {
            toast.error("Processing Failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
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
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>File</Label>
                            <Input type="file" accept=".csv" onChange={e => setSelectedFile(e.target.files[0])} />
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
                            <TableHeader><TableRow><TableHead>Provider</TableHead><TableHead>Date</TableHead><TableHead>Mismatches</TableHead><TableHead>Status</TableHead><TableHead>Report</TableHead></TableRow></TableHeader>
                            <TableBody>
                                <TableRow>
                                    <TableCell>Stripe</TableCell>
                                    <TableCell>Today</TableCell>
                                    <TableCell className="text-red-500 font-bold">3</TableCell>
                                    <TableCell><Badge>Completed</Badge></TableCell>
                                    <TableCell><Button size="sm" variant="ghost"><FileText className="w-4 h-4" /></Button></TableCell>
                                </TableRow>
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>

            {/* Mismatch Detail Mock */}
            <Card className="border-red-200 bg-red-50/20">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-700"><AlertTriangle className="w-5 h-5"/> Critical Mismatches Found</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Ref ID</TableHead><TableHead>DB Amount</TableHead><TableHead>Provider Amount</TableHead><TableHead>Diff</TableHead></TableRow></TableHeader>
                        <TableBody>
                            <TableRow>
                                <TableCell><Badge variant="destructive">Amount Mismatch</Badge></TableCell>
                                <TableCell className="font-mono">tx_123456</TableCell>
                                <TableCell>$100.00</TableCell>
                                <TableCell>$95.00</TableCell>
                                <TableCell className="text-red-600 font-bold">-$5.00</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell><Badge variant="outline">Missing in DB</Badge></TableCell>
                                <TableCell className="font-mono">tx_999999</TableCell>
                                <TableCell>-</TableCell>
                                <TableCell>$50.00</TableCell>
                                <TableCell>-</TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
};

export default ReconciliationPanel;
