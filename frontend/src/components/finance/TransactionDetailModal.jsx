import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { 
  CreditCard, CheckCircle, XCircle, Clock, ShieldAlert, FileText, 
  RefreshCw, Edit, Upload, Activity, Globe, Smartphone, User, ArrowRight,
  AlertTriangle, Lock
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../../services/api';

const TransactionDetailModal = ({ transaction, open, onOpenChange, onRefresh }) => {
  if (!transaction) return null;

  const [isLoading, setLoading] = useState(false);
  const [note, setNote] = useState("");

  const handleAction = async (action, reason = '') => {
    setLoading(true);
    try {
      await api.post(`/v1/finance/transactions/${transaction.id}/action`, { action, reason: reason || note });
      toast.success(`Action ${action} successful`);
      onRefresh();
      onOpenChange(false);
    } catch (err) {
      toast.error('Action failed');
    } finally {
      setLoading(false);
    }
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
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="details">General Info</TabsTrigger>
            <TabsTrigger value="risk">Risk & Compliance</TabsTrigger>
            <TabsTrigger value="timeline">Timeline & Logs</TabsTrigger>
            <TabsTrigger value="notes">Notes & Docs</TabsTrigger>
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
                           <div className="text-2xl font-bold text-red-500">-${transaction.fee}</div>
                       </div>
                       <div className="text-right">
                           <Label className="text-muted-foreground">Net Payout</Label>
                           <div className="text-2xl font-bold text-green-600">${transaction.net_amount?.toLocaleString() || transaction.amount.toLocaleString()}</div>
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
                           <Label className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Destination</Label>
                           <div className="p-2 border rounded bg-white font-mono text-xs break-all">
                               {transaction.destination_address || transaction.provider_tx_id || 'N/A'}
                           </div>
                       </div>
                   </div>

                   {/* Player Info Summary */}
                   <div className="border rounded-lg p-4 space-y-3">
                       <Label className="text-xs text-muted-foreground uppercase font-bold tracking-wider flex items-center gap-2">
                           <User className="w-3 h-3"/> Player Profile
                       </Label>
                       <div className="flex justify-between items-center">
                           <div>
                               <div className="font-bold text-blue-600">{transaction.player_username}</div>
                               <div className="text-xs text-muted-foreground">ID: {transaction.player_id}</div>
                           </div>
                           <div className="text-right text-xs">
                               <div>Balances</div>
                               <div className="font-mono">Real: <span className="text-green-600">${transaction.balance_before?.toLocaleString()}</span></div>
                           </div>
                       </div>
                   </div>
               </div>

               {/* Right Sidebar Actions */}
               <div className="space-y-4">
                   <div className="bg-slate-50 p-4 rounded-lg border space-y-3">
                       <h3 className="font-semibold text-sm">Quick Actions</h3>
                       {transaction.status !== 'completed' && transaction.status !== 'rejected' && (
                           <>
                               <Button className="w-full bg-green-600 hover:bg-green-700 h-10" onClick={() => handleAction('approve')}>
                                   <CheckCircle className="w-4 h-4 mr-2" /> 
                                   {isWithdrawal ? 'Approve Payout' : 'Approve Deposit'}
                               </Button>
                               <Button variant="destructive" className="w-full h-10" onClick={() => handleAction('reject')}>
                                   <XCircle className="w-4 h-4 mr-2" /> Reject
                               </Button>
                               <Button variant="secondary" className="w-full h-10" onClick={() => handleAction('pending_review')}>
                                   <ShieldAlert className="w-4 h-4 mr-2" /> Send to Review
                               </Button>
                           </>
                       )}
                       {isWithdrawal && transaction.status === 'processing' && (
                           <Button className="w-full bg-blue-600 hover:bg-blue-700 h-10" onClick={() => handleAction('mark_paid')}>
                               <CheckCircle className="w-4 h-4 mr-2" /> Mark as Paid
                           </Button>
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

          {/* TAB: RISK */}
          <TabsContent value="risk" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-6">
                    <div className="border rounded-lg p-4 bg-orange-50/50 border-orange-100">
                        <h4 className="font-bold flex items-center gap-2 mb-4 text-orange-800">
                            <ShieldAlert className="w-5 h-5"/> Risk Assessment
                        </h4>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-sm">Risk Score at Transaction</span>
                                <Badge variant="outline" className="uppercase">{transaction.risk_score_at_time || 'Low'}</Badge>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm">KYC Status</span>
                                <Badge variant={transaction.kyc_status_at_time === 'approved' ? 'default' : 'destructive'}>
                                    {transaction.kyc_status_at_time || 'Pending'}
                                </Badge>
                            </div>
                            <div className="space-y-2">
                                <span className="text-sm font-medium">Flags</span>
                                <div className="flex flex-wrap gap-2">
                                    {(transaction.limit_flags || []).map(f => <Badge key={f} variant="secondary" className="text-xs">{f}</Badge>)}
                                    {(transaction.velocity_flags || []).map(f => <Badge key={f} variant="secondary" className="text-xs">{f}</Badge>)}
                                    {(!transaction.limit_flags?.length && !transaction.velocity_flags?.length) && <span className="text-xs text-muted-foreground">No active flags.</span>}
                                </div>
                            </div>
                        </div>
                    </div>

                    {isWithdrawal && (
                        <div className="border rounded-lg p-4">
                            <h4 className="font-bold flex items-center gap-2 mb-4">
                                <Activity className="w-5 h-5"/> Bonus Wagering
                            </h4>
                            {transaction.wagering_info ? (
                                <div className="space-y-4">
                                    <div className="flex justify-between text-sm">
                                        <span>Progress</span>
                                        <span className={transaction.wagering_info.is_met ? "text-green-600 font-bold" : "text-orange-600 font-bold"}>
                                            {transaction.wagering_info.is_met ? "COMPLETED" : "PENDING"}
                                        </span>
                                    </div>
                                    <Progress value={(transaction.wagering_info.current / transaction.wagering_info.required) * 100} className="h-2" />
                                    <div className="flex justify-between text-xs text-muted-foreground">
                                        <span>${transaction.wagering_info.current} Wagered</span>
                                        <span>Goal: ${transaction.wagering_info.required}</span>
                                    </div>
                                    {!transaction.wagering_info.is_met && (
                                        <div className="p-2 bg-red-50 text-red-700 text-xs rounded flex items-center gap-2">
                                            <Lock className="w-3 h-3" /> Withdrawal locked until wagering completed.
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-sm text-muted-foreground">No active bonus wagering requirements.</div>
                            )}
                        </div>
                    )}
                </div>

                <div className="space-y-4">
                     <h4 className="font-bold">Fraud Action Center</h4>
                     <Button variant="outline" className="w-full text-red-600 hover:bg-red-50 justify-start">
                         <ShieldAlert className="w-4 h-4 mr-2" /> Flag Account for Fraud
                     </Button>
                     <Button variant="outline" className="w-full justify-start">
                         <FileText className="w-4 h-4 mr-2" /> View AML Report
                     </Button>
                     <Button variant="outline" className="w-full justify-start">
                         <Activity className="w-4 h-4 mr-2" /> View Player Session Logs
                     </Button>
                </div>
            </div>
          </TabsContent>

          {/* TAB: TIMELINE */}
          <TabsContent value="timeline" className="mt-6">
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
              
              <Separator />
              
              <div className="space-y-2">
                  <Label>Receipts & Docs</Label>
                  <div className="border border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-muted-foreground gap-2 cursor-pointer hover:bg-slate-50">
                      <Upload className="w-8 h-8" />
                      <span className="text-sm">Drag & Drop receipt or Click to Upload</span>
                  </div>
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
