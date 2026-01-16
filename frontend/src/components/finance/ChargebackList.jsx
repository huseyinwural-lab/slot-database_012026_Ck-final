import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ShieldAlert, Paperclip, Gavel, AlertTriangle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import api from '../../services/api';

const getStatusBadge = (status) => {
  const map = {
    open: { label: 'Open', variant: 'secondary' },
    evidence_gathering: { label: 'Evidence Gathering', variant: 'secondary' },
    evidence_submitted: { label: 'Evidence Submitted', variant: 'outline' },
    won: { label: 'Won', variant: 'default' },
    lost: { label: 'Lost', variant: 'destructive' },
  };
  const cfg = map[status] || { label: status || 'Unknown', variant: 'outline' };
  return (
    <Badge
      variant={cfg.variant}
      className={
        status === 'lost'
          ? 'bg-red-500/10 text-red-500'
          : status === 'open'
          ? 'bg-orange-500/10 text-orange-500'
          : ''
      }
    >
      {cfg.label}
    </Badge>
  );
};

const getRiskBadge = (score) => {
  if (score == null) return <span className="text-xs text-muted-foreground">-</span>;
  let level = 'Low';
  let cls = 'bg-green-50 text-green-700 border-green-200';
  if (score >= 80) {
    level = 'Critical';
    cls = 'bg-red-50 text-red-700 border-red-200';
  } else if (score >= 60) {
    level = 'High';
    cls = 'bg-orange-50 text-orange-700 border-orange-200';
  } else if (score >= 30) {
    level = 'Medium';
    cls = 'bg-yellow-50 text-yellow-700 border-yellow-200';
  }
  return (
    <Badge variant="outline" className={`text-xs ${cls}`}>
      {score} ({level})
    </Badge>
  );
};

const formatDeadline = (dueDate) => {
  if (!dueDate) return '-';
  const d = new Date(dueDate);
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const days = Math.round(diffMs / (1000 * 60 * 60 * 24));
  if (days < 0) return `${Math.abs(days)} days ago`;
  if (days === 0) return 'Today';
  if (days === 1) return '1 day';
  return `${days} days`;
};

const ChargebackList = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedCase, setSelectedCase] = useState(null);
  const [evidenceUrl, setEvidenceUrl] = useState('');

  const [guidelinesOpen, setGuidelinesOpen] = useState(false);
  const [guidelines, setGuidelines] = useState(null);
  const [guidelinesLoading, setGuidelinesLoading] = useState(false);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await api.get('/v1/finance/chargebacks');
      setCases(res.data || []);
    } catch (err) {
      toast.error('Failed to load chargeback cases');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  // P1 decision: Evidence upload is NOT implemented in this environment.
  const openEvidenceDialog = () => {
    // no-op (button is disabled)
  };

  const handleUploadEvidence = async () => {
    // no-op (modal not reachable)
  };

  const openGuidelines = async () => {
    setGuidelinesOpen(true);
    if (guidelines) return;

    setGuidelinesLoading(true);
    try {
      const res = await api.get('/v1/finance/chargebacks/guidelines');
      setGuidelines(res.data);
    } catch (err) {
      toast.error('Failed to load guidelines');
    } finally {
      setGuidelinesLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-red-500" /> Chargeback Cases
        </h3>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => {
              api
                .get('/v1/finance/chargebacks/export', { responseType: 'blob' })
                .then((res) => {
                  const url = window.URL.createObjectURL(new Blob([res.data]));
                  const link = document.createElement('a');
                  link.href = url;
                  link.setAttribute('download', `finance_chargebacks_${new Date().toISOString()}.csv`);
                  document.body.appendChild(link);
                  link.click();
                  link.remove();
                })
                .catch(() => {
                  toast.error('Export failed');
                });
            }}
          >
            Export CSV
          </Button>
          <Button variant="outline" onClick={openGuidelines}>
            <Gavel className="w-4 h-4 mr-2" /> Represent Guidelines
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">
            Overview of all open and historical chargeback cases. Use this table to track deadlines and upload
            evidence.
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
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
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    Loading chargeback cases...
                  </TableCell>
                </TableRow>
              ) : cases.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No chargeback cases found. Cases will appear here when created from transactions or via payment
                    provider webhooks.
                  </TableCell>
                </TableRow>
              ) : (
                cases.map((cb) => (
                  <TableRow key={cb.id}>
                    <TableCell className="font-mono text-xs">{cb.id}</TableCell>
                    <TableCell className="text-xs">
                      <div className="font-medium">TX: {cb.transaction_id}</div>
                      <div className="text-[10px] text-muted-foreground">Player: {cb.player_id}</div>
                    </TableCell>
                    <TableCell>{getRiskBadge(cb.risk_score_at_time)}</TableCell>
                    <TableCell>
                      {cb.fraud_cluster_id ? (
                        <div className="flex items-center gap-1 text-red-600 text-xs">
                          <AlertTriangle className="w-3 h-3" /> {cb.fraud_cluster_id}
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>${cb.amount?.toFixed(2)}</TableCell>
                    <TableCell className="text-xs">{cb.reason_code}</TableCell>
                    <TableCell className="text-xs font-semibold text-red-600">
                      {formatDeadline(cb.due_date)}
                    </TableCell>
                    <TableCell>{getStatusBadge(cb.status)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled
                        title="Evidence upload is not available in this environment"
                      >
                        <Paperclip className="w-4 h-4 mr-2" /> Upload Evidence
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Evidence upload is disabled in this environment (P1). */}
      {/* Guidelines Modal (P0) */}
      <Dialog open={guidelinesOpen} onOpenChange={setGuidelinesOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{guidelines?.title || 'Represent Guidelines'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            {guidelinesLoading ? (
              <div className="text-sm text-muted-foreground">Loading...</div>
            ) : guidelines?.sections?.length ? (
              guidelines.sections.map((s, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="text-sm font-semibold">{s.heading}</div>
                  <div className="text-sm text-muted-foreground whitespace-pre-line">{s.body}</div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted-foreground">No content.</div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setGuidelinesOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
};

export default ChargebackList;
