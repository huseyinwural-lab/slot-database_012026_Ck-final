import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  CreditCard, CheckCircle, XCircle, Clock, ShieldAlert, FileText, 
  RefreshCw, Edit, Upload, Activity, Globe, Smartphone, User
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../../services/api';

const DepositDetailModal = ({ transaction, open, onOpenChange, onRefresh }) => {
  if (!transaction) return null;

  const [isLoading, setLoading] = useState(false);

  const handleAction = async (action, reason = '') => {
    setLoading(true);
    try {
      await api.post(`/v1/finance/transactions/${transaction.id}/action`, { action, reason });
      toast.success(`Action ${action} successful`);
      onRefresh();
      onOpenChange(false);
    } catch (err) {
      toast.error('Action failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                Deposit Details
                <Badge variant="outline" className="font-mono">{transaction.id}</Badge>
              </DialogTitle>
              <DialogDescription>
                Created on {new Date(transaction.created_at).toLocaleString()}
              </DialogDescription>
            </div>
            <div className="flex gap-2">
              <Badge variant={
                transaction.status === 'completed' ? 'default' : 
                transaction.status === 'pending' ? 'secondary' : 'destructive'
              }>
                {transaction.status.toUpperCase()}
              </Badge>
            </div>
          </div>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left Column: Key Info */}
          <div className="md:col-span-2 space-y-6">
            {/* Amount Section */}
            <div className="p-4 bg-muted/30 rounded-lg border flex justify-between items-center">
              <div>
                <Label className="text-muted-foreground">Requested Amount</Label>
                <div className="text-2xl font-bold">${transaction.amount.toLocaleString()}</div>
              </div>
              <div className="text-right">
                <Label className="text-muted-foreground">Net Amount (After Fees)</Label>
                <div className="text-2xl font-bold text-green-600">${transaction.net_amount?.toLocaleString() || transaction.amount.toLocaleString()}</div>
                {transaction.fee > 0 && <div className="text-xs text-red-500">-${transaction.fee} Fee</div>}
              </div>
            </div>

            {/* Provider & Player Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Provider</Label>
                <div className="font-medium flex items-center gap-2">
                  <CreditCard className="w-4 h-4" />
                  {transaction.provider || 'Internal'}
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Provider Tx ID</Label>
                <div className="font-mono text-sm">{transaction.provider_tx_id || '-'}</div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Player</Label>
                <div className="font-medium flex items-center gap-2">
                  <User className="w-4 h-4" />
                  {transaction.player_username}
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Method</Label>
                <div className="font-medium">{transaction.method}</div>
              </div>
            </div>

            <Separator />

            {/* Technical Info */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">IP Address</Label>
                <div className="text-sm font-mono flex items-center gap-1">
                  <Globe className="w-3 h-3" /> {transaction.ip_address || 'Unknown'}
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Device</Label>
                <div className="text-sm flex items-center gap-1">
                  <Smartphone className="w-3 h-3" /> {transaction.device_info || 'Unknown'}
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Country</Label>
                <div className="text-sm font-bold">{transaction.country || '-'}</div>
              </div>
            </div>

            <Separator />

            <Tabs defaultValue="timeline" className="w-full">
              <TabsList>
                <TabsTrigger value="timeline">Timeline</TabsTrigger>
                <TabsTrigger value="raw">Raw Logs</TabsTrigger>
                <TabsTrigger value="notes">Notes</TabsTrigger>
              </TabsList>
              <TabsContent value="timeline" className="mt-4">
                <ScrollArea className="h-[200px] w-full rounded-md border p-4">
                  {transaction.timeline?.map((event, i) => (
                    <div key={i} className="mb-4 last:mb-0 relative pl-4 border-l-2 border-muted">
                      <div className="absolute -left-[5px] top-1 w-2 h-2 rounded-full bg-primary" />
                      <div className="text-sm font-medium">{event.status.toUpperCase()}</div>
                      <div className="text-xs text-muted-foreground">{event.description}</div>
                      <div className="text-[10px] text-muted-foreground mt-1">
                        {new Date(event.timestamp).toLocaleString()} by {event.operator || 'System'}
                      </div>
                    </div>
                  ))}
                  {(!transaction.timeline || transaction.timeline.length === 0) && (
                    <div className="text-center text-muted-foreground text-sm">No timeline events recorded.</div>
                  )}
                </ScrollArea>
              </TabsContent>
              <TabsContent value="raw">
                <div className="bg-slate-950 text-slate-50 p-4 rounded-md font-mono text-xs h-[200px] overflow-auto">
                  {transaction.raw_response ? JSON.stringify(transaction.raw_response, null, 2) : '// No raw logs available'}
                </div>
              </TabsContent>
              <TabsContent value="notes">
                <div className="space-y-2">
                  <div className="p-3 bg-secondary rounded-md text-sm">
                    {transaction.admin_note || 'No admin notes.'}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>

          {/* Right Column: Actions */}
          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Actions</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-2">
                {transaction.status === 'pending' && (
                  <>
                    <Button className="w-full bg-green-600 hover:bg-green-700" onClick={() => handleAction('approve')}>
                      <CheckCircle className="w-4 h-4 mr-2" /> Approve
                    </Button>
                    <Button variant="destructive" className="w-full" onClick={() => handleAction('reject')}>
                      <XCircle className="w-4 h-4 mr-2" /> Reject
                    </Button>
                    <Button variant="outline" className="w-full" onClick={() => handleAction('pending_review')}>
                      <Clock className="w-4 h-4 mr-2" /> Mark Pending Review
                    </Button>
                  </>
                )}
                
                <Button variant="secondary" className="w-full" onClick={() => handleAction('retry_callback')}>
                  <RefreshCw className="w-4 h-4 mr-2" /> Retry Callback
                </Button>
                
                <Button variant="outline" className="w-full">
                  <Edit className="w-4 h-4 mr-2" /> Edit Transaction
                </Button>

                <Button variant="outline" className="w-full text-orange-600 hover:text-orange-700 hover:bg-orange-50" onClick={() => handleAction('fraud')}>
                  <ShieldAlert className="w-4 h-4 mr-2" /> Open in Fraud
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Documents</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-2">
                <Button variant="outline" className="w-full">
                  <FileText className="w-4 h-4 mr-2" /> Export Receipt
                </Button>
                <Button variant="ghost" className="w-full">
                  <Upload className="w-4 h-4 mr-2" /> Upload Proof
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DepositDetailModal;
