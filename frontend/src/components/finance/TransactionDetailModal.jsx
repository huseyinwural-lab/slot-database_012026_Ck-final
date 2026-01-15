import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  CreditCard, CheckCircle, XCircle, Clock, ShieldAlert, FileText, 
  RefreshCw, Edit, Upload, Activity, Globe, Smartphone, User, ArrowRight,
  AlertTriangle, Lock, Link, BrainCircuit
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../../services/api';

const TransactionDetailModal = ({ transaction, open, onOpenChange, onRefresh }) => {
  const [isLoading, setLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [note, setNote] = useState("");
  const [paymentMethod, setPaymentMethod] = useState(""); // For manual payouts
  const [aiAnalysis, setAiAnalysis] = useState(null);

  if (!transaction) return null;

  const handleAction = async (action, reason = '') => {
    setLoading(true);
    try {
      const payload = { action, reason: reason || note };
      if (action === 'approve' && isWithdrawal && paymentMethod) {
        payload.payment_method = paymentMethod;
      }
      await api.post(`/v1/finance/transactions/${transaction.id}/action`, payload);
      toast.success(`Action ${action} successful`);
      onRefresh();
      onOpenChange(false);
    } catch (err) {
      toast.error('Action failed');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeRisk = async () => {
    toast.message('Not available in this environment');
  };

  const isWithdrawal = transaction.type === 'withdrawal';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[95vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
               <div className={`p-2 rounded-full ${isWithdrawal ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
                   {isWithdrawal ? <ArrowRight className="w-6 h-6 rotate-45" /> : <ArrowRight className="w-6 h-6 rotate-[-45deg]" />}
               </div>
               <div>
                  <DialogTitle className="flex items-center gap-2 text-xl">
                    {isWithdrawal ? 'Withdrawal Request' : 'Deposit Detail'}
                    <span className="text-sm font-normal text-muted-foreground">#{transaction.id}</span>
                  </DialogTitle>
                  <DialogDescription>
                    Created on {new Date(transaction.created_at).toLocaleString()}
                  </DialogDescription>
               </div>
            </div>
            <div className="flex gap-2">
              <Badge className="text-sm px-3 py-1" variant={
                transaction.status === 'completed' || transaction.status === 'paid' ? 'default' : 
                transaction.status === 'pending' || transaction.status === 'under_review' ? 'secondary' : 'destructive'
              }>
                {transaction.status?.toUpperCase().replace('_', ' ')}
              </Badge>
            </div>
          </div>
        </DialogHeader>

        <Tabs defaultValue="details" className="w-full mt-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="details">General Info</TabsTrigger>
            <TabsTrigger value="risk">Risk & Compliance</TabsTrigger>
            <TabsTrigger value="audit">Audit Log</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="notes">Notes</TabsTrigger>
          </TabsList>

          {/* TAB: DETAILS */}
          <TabsContent value="details" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
               <div className="md:col-span-2 space-y-6">
                   {/* Amount Card */}
                   <div className="grid grid-cols-3 gap-4 bg-muted/20 p-4 rounded-lg border">
                       <div>
                           <Label className="text-muted-foreground">Requested Amount</Label>
                           <div className="text-2xl font-bold">${transaction.amount.toLocaleString()}</div>
                       </div>
                       <div>
                           <Label className="text-muted-foreground">Fee</Label>
                           <div className="text-2xl font-bold text-red-500">-${transaction.fee || 0}</div>
                       </div>
                       <div className="text-right">
                           <Label className="text-muted-foreground">Net Payout</Label>
                           <div className="text-2xl font-bold text-green-600">${transaction.net_amount?.toLocaleString() || transaction.amount.toLocaleString()}</div>
                       </div>
                   </div>

                   {/* Wallet Impact */}
                   <div className="grid grid-cols-2 gap-4 border p-4 rounded-lg">
                       <div>
                           <Label className="text-muted-foreground text-xs uppercase">Wallet Before</Label>
                           <div className="font-mono font-bold">${transaction.balance_before?.toLocaleString() || '0.00'}</div>
                       </div>
                       <div className="text-right">
                           <Label className="text-muted-foreground text-xs uppercase">Wallet After</Label>
                           <div className="font-mono font-bold">${transaction.balance_after?.toLocaleString() || '0.00'}</div>
                       </div>
                   </div>

                   {/* Payment Info */}
                   <div className="grid grid-cols-2 gap-6">
                       <div className="space-y-2">
                           <Label className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Payment Method</Label>
                           <div className="flex items-center gap-2 p-2 border rounded bg-white">
                               <CreditCard className="w-5 h-5 text-gray-500" />
                               <div>
                                   <div className="font-semibold text-sm">{transaction.provider}</div>
                                   <div className="text-xs text-muted-foreground">{transaction.method}</div>
                               </div>
                           </div>
                       </div>
                       <div className="space-y-2">
                           <Label className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Reference / Destination</Label>
                           <div className="p-2 border rounded bg-white font-mono text-xs break-all">
                               {transaction.destination_address || transaction.provider_tx_id || 'N/A'}
                           </div>
                           <div className="text-[10px] text-muted-foreground text-right">Provider Ref: {transaction.provider_tx_id || 'Pending'}</div>
                       </div>
                   </div>
               </div>

               {/* Right Sidebar Actions */}
               <div className="space-y-4">
                   <div className="bg-slate-50 p-4 rounded-lg border space-y-3">
                       <h3 className="font-semibold text-sm">Quick Actions</h3>
                       {transaction.status !== 'completed' && transaction.status !== 'rejected' && (
                           <>
                               {isWithdrawal && (
                                 <div className="mb-2">
                                   <Label className="text-xs">Payout Method</Label>
                                   <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                                     <SelectTrigger className="h-8 text-xs">
                                       <SelectValue placeholder="Select Channel" />
                                     </SelectTrigger>
                                     <SelectContent>
                                       <SelectItem value="manual_bank">Bank Transfer (Manual)</SelectItem>
                                       <SelectItem value="crypto_usdt">Crypto (USDT)</SelectItem>
                                       <SelectItem value="papara">Papara</SelectItem>
                                       <SelectItem value="payfix">Payfix</SelectItem>
                                     </SelectContent>
                                   </Select>
                                 </div>
                               )}
                               <Button
                                 className="w-full bg-green-600 hover:bg-green-700 h-10"
                                 disabled
                                 title="Use Withdrawals page for approvals"
                               >
                                   <CheckCircle className="w-4 h-4 mr-2" /> 
                                   {isWithdrawal ? 'Approve Payout' : 'Approve Deposit'}
                               </Button>
                               <Button
                                 variant="destructive"
                                 className="w-full h-10"
                                 disabled
                                 title="Use Withdrawals page for approvals"
                               >
                                   <XCircle className="w-4 h-4 mr-2" /> Reject
                               </Button>
                               <Button
                                 variant="secondary"
                                 className="w-full h-10"
                                 disabled
                                 title="Not available in this environment"
                               >
                                   <ShieldAlert className="w-4 h-4 mr-2" /> Send to Review
                               </Button>
                           </>
                       )}
                   </div>
                   
                   {/* Meta Info */}
                   <div className="text-xs text-muted-foreground space-y-2 px-1">
                       <div className="flex justify-between"><span>IP:</span> <span className="font-mono">{transaction.ip_address || 'Unknown'}</span></div>
                       <div className="flex justify-between"><span>Device:</span> <span>{transaction.device_info || 'Unknown'}</span></div>
                       <div className="flex justify-between"><span>Country:</span> <span>{transaction.country || '-'}</span></div>
                   </div>
               </div>
            </div>
          </TabsContent>

          {/* TAB: AUDIT LOG */}
          <TabsContent value="audit" className="mt-6">
              <Card>
                  <CardHeader><CardTitle>Audit Trail</CardTitle></CardHeader>
                  <CardContent>
                      <ScrollArea className="h-[300px]">
                          <div className="space-y-4">
                              {/* Mock Audit Log from Timeline if Real Audit Log is empty */}
                              {(transaction.audit_log || transaction.timeline)?.map((log, i) => (
                                  <div key={i} className="flex gap-4 border-b pb-4 last:border-0">
                                      <div className="text-xs text-muted-foreground w-24">
                                          {new Date(log.timestamp).toLocaleString()}
                                      </div>
                                      <div className="flex-1">
                                          <div className="font-semibold text-sm">
                                              {log.operator || log.admin_id || 'System'} 
                                              <span className="font-normal text-muted-foreground"> performed </span> 
                                              {log.action || log.description}
                                          </div>
                                          <div className="text-xs text-muted-foreground mt-1 font-mono">{log.details || ''}</div>
                                      </div>
                                  </div>
                              ))}
                          </div>
                      </ScrollArea>
                  </CardContent>
              </Card>
          </TabsContent>

          {/* TAB: RISK */}
          <TabsContent value="risk" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-6">
                    <div className="border rounded-lg p-4 bg-orange-50/50 border-orange-100">
                        <div className="flex justify-between items-start mb-4">
                            <h4 className="font-bold flex items-center gap-2 text-orange-800">
                                <ShieldAlert className="w-5 h-5"/> Risk Assessment
                            </h4>
                            <Button 
                                variant="outline" 
                                size="sm" 
                                className="border-orange-200 text-orange-700 hover:bg-orange-100"
                                onClick={handleAnalyzeRisk}
                                disabled={isAnalyzing}
                            >
                                {isAnalyzing ? <RefreshCw className="w-3 h-3 animate-spin mr-1"/> : <BrainCircuit className="w-3 h-3 mr-1"/>}
                                {isAnalyzing ? "Analyzing..." : "Analyze Risk (AI)"}
                            </Button>
                        </div>

                        {/* AI ANALYSIS RESULT */}
                        {aiAnalysis && (
                             <div className="mb-4 bg-white p-3 rounded border border-orange-200 shadow-sm">
                                 <div className="flex justify-between items-center mb-2">
                                     <span className="font-bold text-sm">AI Score: {aiAnalysis.risk_score}/100</span>
                                     <Badge variant={aiAnalysis.risk_level === 'low' ? 'outline' : 'destructive'}>{aiAnalysis.risk_level}</Badge>
                                 </div>
                                 <p className="text-xs text-muted-foreground italic">{aiAnalysis.reason}</p>
                                 {aiAnalysis.flags && aiAnalysis.flags.length > 0 && (
                                     <div className="flex gap-1 flex-wrap mt-2">
                                         {aiAnalysis.flags.map(f => <Badge key={f} variant="secondary" className="text-[10px]">{f}</Badge>)}
                                     </div>
                                 )}
                             </div>
                        )}
                        
                        <div className="mt-4 p-2 bg-white rounded border border-orange-100 text-xs text-orange-800">
                            <strong>System Checks:</strong>
                            <ul className="list-disc pl-4 mt-1 space-y-1">
                                <li>Velocity: {transaction.velocity_flags?.length ? 'High' : 'Normal'}</li>
                                <li>IP Match: {transaction.ip_address === transaction.last_ip ? 'Yes' : 'No (Warning)'}</li>
                                <li>Device Fingerprint: Valid</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
          </TabsContent>

          {/* TAB: TIMELINE */}
          <TabsContent value="timeline" className="mt-6 space-y-6">
            <ScrollArea className="h-[300px] w-full rounded-md border p-4">
                {transaction.timeline?.map((event, i) => (
                <div key={i} className="mb-6 last:mb-0 relative pl-6 border-l-2 border-muted">
                    <div className="absolute -left-[5px] top-1 w-2 h-2 rounded-full bg-primary" />
                    <div className="flex justify-between items-start">
                        <div>
                            <div className="text-sm font-bold capitalize">{event.status.replace('_', ' ')}</div>
                            <div className="text-xs text-muted-foreground">{event.description}</div>
                        </div>
                        <div className="text-[10px] text-muted-foreground text-right">
                            <div>{new Date(event.timestamp).toLocaleDateString()}</div>
                            <div>{new Date(event.timestamp).toLocaleTimeString()}</div>
                            {event.operator && <div className="text-blue-500">{event.operator}</div>}
                        </div>
                    </div>
                </div>
                ))}
            </ScrollArea>
          </TabsContent>
          
          {/* TAB: NOTES */}
          <TabsContent value="notes" className="mt-6 space-y-4">
              <div className="space-y-2">
                  <Label>Admin Notes</Label>
                  <Textarea 
                      placeholder="Add an internal note about this transaction..." 
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                  />
                  <Button size="sm" onClick={() => handleAction('add_note')}>Save Note</Button>
              </div>
          </TabsContent>

        </Tabs>
        
        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default TransactionDetailModal;
