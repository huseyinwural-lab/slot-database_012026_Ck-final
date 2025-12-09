import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ShieldAlert, Paperclip, Gavel, AlertTriangle } from 'lucide-react';

const ChargebackList = () => {
    return (
        <div className="space-y-6">
            <div className="flex justify-between">
                <h3 className="text-xl font-bold">Chargeback Cases</h3>
                <Button variant="outline"><Gavel className="w-4 h-4 mr-2" /> Represent Guidelines</Button>
            </div>

            <Card>
                <CardContent className="pt-6">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Case ID</TableHead>
                                <TableHead>Transaction</TableHead>
                                <TableHead>Risk Score (At Time)</TableHead>
                                <TableHead>Fraud Cluster</TableHead>
                                <TableHead>Amount</TableHead>
                                <TableHead>Reason Code</TableHead>
                                <TableHead>Deadline</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="text-right">Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            <TableRow>
                                <TableCell className="font-mono">CB-9921</TableCell>
                                <TableCell>tx_123 (User: highroller)</TableCell>
                                <TableCell><Badge variant="destructive">95 (Critical)</Badge></TableCell>
                                <TableCell><div className="flex items-center gap-1 text-red-600"><AlertTriangle className="w-3 h-3"/> Cluster #8821</div></TableCell>
                                <TableCell>$500.00</TableCell>
                                <TableCell>Fraud / Not Authorized</TableCell>
                                <TableCell className="text-red-600 font-bold">2 Days</TableCell>
                                <TableCell><Badge variant="destructive">Action Required</Badge></TableCell>
                                <TableCell className="text-right">
                                    <Button size="sm"><Paperclip className="w-4 h-4 mr-2"/> Upload Evidence</Button>
                                </TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell className="font-mono">CB-9922</TableCell>
                                <TableCell>tx_456</TableCell>
                                <TableCell><Badge variant="outline" className="bg-green-50 text-green-700">10 (Low)</Badge></TableCell>
                                <TableCell>-</TableCell>
                                <TableCell>$120.00</TableCell>
                                <TableCell>Product Not Received</TableCell>
                                <TableCell>15 Days</TableCell>
                                <TableCell><Badge variant="secondary">Evidence Submitted</Badge></TableCell>
                                <TableCell className="text-right">
                                    <Button size="sm" variant="ghost">View Details</Button>
                                </TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
};

export default ChargebackList;
