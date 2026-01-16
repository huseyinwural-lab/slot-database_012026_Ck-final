import React, { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Upload, AlertTriangle, Settings, PlayCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import api from '../../services/api';

const ReconciliationPanel = () => {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [provider, setProvider] = useState('Stripe');
  const [loading, setLoading] = useState(false);

  // Scheduler
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [schedule, setSchedule] = useState({ provider: 'Stripe', frequency: 'daily', auto_fetch_enabled: false });
  const [scheduleLoading, setScheduleLoading] = useState(false);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await api.get('/v1/finance/reconciliation');
      setReports(res.data || []);
      if (!selectedReport && res.data && res.data.length > 0) {
        setSelectedReport(res.data[0]);
      }
    } catch (err) {
      toast.error('Failed to load reconciliation history');
    }
  }, [selectedReport]);

  const fetchSchedule = async (currentProvider = provider) => {
    setScheduleLoading(true);
    try {
      const res = await api.get('/v1/finance/reconciliation/config');
      const data = Array.isArray(res.data) ? res.data : [];
      const cfg = data.find((c) => c.provider === currentProvider) || data[0];
      if (cfg) {
        setSchedule({
          provider: cfg.provider,
          frequency: cfg.frequency || 'daily',
          auto_fetch_enabled: !!cfg.auto_fetch_enabled,
        });
      } else {
        setSchedule({ provider: currentProvider, frequency: 'daily', auto_fetch_enabled: false });
      }
    } catch (err) {
      toast.error('Failed to load scheduler config');
    } finally {
      setScheduleLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // P1 decision: upload-based reconciliation is not available in this environment.
  // (file upload/storage/processing lifecycle is out of scope)
  const handleUpload = async () => {
    // no-op (UI disabled)
  };

  const handleRunAuto = async () => {
    try {
      const res = await api.post('/v1/finance/reconciliation/run-auto', { provider });
      toast.success('Auto-fetch initiated');
      // Backend history may be empty in this environment; still show the returned report deterministically.
      if (res.data) {
        setReports((prev) => {
          const next = Array.isArray(prev) ? prev : [];
          const deduped = next.filter((r) => r?.id !== res.data?.id);
          return [res.data, ...deduped];
        });
        setSelectedReport(res.data);
      } else {
        await fetchHistory();
      }
    } catch (err) {
      toast.error('Auto-fetch failed');
    }
  };

  const handleOpenSettings = async () => {
    await fetchSchedule(provider);
    setIsSettingsOpen(true);
  };

  const handleSaveSchedule = async () => {
    if (!schedule) return;
    try {
      await api.post('/v1/finance/reconciliation/config', {
        provider: schedule.provider,
        frequency: schedule.frequency,
        auto_fetch_enabled: schedule.auto_fetch_enabled,
      });
      toast.success('Scheduler configuration saved');
      setIsSettingsOpen(false);
    } catch (err) {
      toast.error('Failed to save scheduler config');
    }
  };

  const renderStatusBadge = (status) => {
    const map = {
      matched: {
        label: 'Matched',
        className: 'bg-green-100 text-green-800 border-green-200',
      },
      mismatch_amount: {
        label: 'FX / Amount Mismatch',
        className: 'bg-orange-100 text-orange-800 border-orange-200',
      },
      missing_in_db: {
        label: 'Missing in DB',
        className: 'bg-red-100 text-red-700 border-red-200',
      },
      missing_in_provider: {
        label: 'Missing in Provider',
        className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      },
      potential_fraud: {
        label: 'Potential Fraud',
        className: 'bg-purple-100 text-purple-800 border-purple-200',
      },
      pending: {
        label: 'Pending',
        className: 'bg-slate-100 text-slate-800 border-slate-200',
      },
    };

    const cfg = map[status] || { label: status, className: 'bg-slate-100 text-slate-800' };
    return (
      <Badge className={`border shadow-none text-xs font-semibold ${cfg.className}`}>
        {cfg.label}
      </Badge>
    );
  };

  const activeReport = selectedReport && selectedReport.items ? selectedReport : null;

  return (
    <div className="space-y-6">
      <div className="flex justify-end gap-2">
        <Button
          variant="outline"
          onClick={() => {
            api
              .get('/v1/finance/reconciliation/export', {
                params: { provider },
                responseType: 'blob',
              })
              .then((res) => {
                const url = window.URL.createObjectURL(new Blob([res.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `finance_reconciliation_${new Date().toISOString()}.csv`);
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
        <Button variant="outline" onClick={handleOpenSettings}>
          <Settings className="w-4 h-4 mr-2" /> Auto-Scheduler
        </Button>
        <Button onClick={handleRunAuto}>
          <PlayCircle className="w-4 h-4 mr-2" /> Run Auto-Match Now
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Upload Area */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Upload Statement</CardTitle>
            <CardDescription>CSV from Provider</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Provider</Label>
              <Select
                value={provider}
                onValueChange={(val) => {
                  setProvider(val);
                  setSchedule((prev) => ({ ...(prev || {}), provider: val }));
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Stripe">Stripe</SelectItem>
                  <SelectItem value="Papara">Papara</SelectItem>
                  <SelectItem value="CoinPayments">CoinPayments</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>File (CSV)</Label>
              <Input
                type="file"
                accept=".csv"
                disabled
                title="Not available in this environment"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
              <p className="text-[10px] text-muted-foreground">Upload is not available in this environment.</p>
            </div>
            <Button
              className="w-full"
              onClick={handleUpload}
              disabled
              title="Not available in this environment"
            >
              <Upload className="w-4 h-4 mr-2" />
              Start Reconciliation
            </Button>
          </CardContent>
        </Card>

        {/* History */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Recent Reconciliations</CardTitle>
            <CardDescription>
              Latest reconciliation runs across all providers. Click a row to inspect mismatches and fraud alerts.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Provider</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>File</TableHead>
                  <TableHead>Total</TableHead>
                  <TableHead>Mismatches</TableHead>
                  <TableHead>Fraud Alerts</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((r) => (
                  <TableRow
                    key={r.id}
                    className={
                      activeReport && activeReport.id === r.id
                        ? 'cursor-pointer bg-slate-900/40'
                        : 'cursor-pointer hover:bg-slate-900/30'
                    }
                    onClick={() => setSelectedReport(r)}
                  >
                    <TableCell>{r.provider_name}</TableCell>
                    <TableCell>{new Date(r.created_at).toLocaleString()}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{r.file_name}</TableCell>
                    <TableCell>{r.total_records}</TableCell>
                    <TableCell className={r.mismatches > 0 ? 'text-red-500 font-bold' : 'text-green-500'}>
                      {r.mismatches}
                    </TableCell>
                    <TableCell>
                      {r.fraud_alerts > 0 ? (
                        <Badge variant="destructive">{r.fraud_alerts} Fraud</Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className="capitalize">{r.status || 'completed'}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
                {reports.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground">
                      No reports yet. Upload a CSV or run auto-match to generate your first reconciliation report.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Mismatch Detail */}
      <Card className="border-red-200 bg-red-50/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-700">
            <AlertTriangle className="w-5 h-5" /> Mismatch &amp; Fraud Report
          </CardTitle>
          {activeReport && (
            <CardDescription>
              Showing {activeReport.items?.length || 0} records for{' '}
              <span className="font-semibold">{activeReport.provider_name}</span> /{' '}
              <span className="font-mono text-xs">{activeReport.file_name}</span>
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {!activeReport ? (
            <div className="text-center text-muted-foreground py-8 text-sm">
              Select a reconciliation run from the history table above to inspect detailed mismatches and fraud alerts.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Ref ID</TableHead>
                  <TableHead>Currency / FX</TableHead>
                  <TableHead className="text-right">DB Amount (Base)</TableHead>
                  <TableHead className="text-right">Provider Amount</TableHead>
                  <TableHead className="text-right">Diff</TableHead>
                  <TableHead>Notes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeReport.items && activeReport.items.length > 0 ? (
                  activeReport.items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="whitespace-nowrap">{renderStatusBadge(item.status)}</TableCell>
                      <TableCell className="font-mono text-xs">{item.provider_ref}</TableCell>
                      <TableCell className="text-xs">
                        <div className="font-medium">
                          {item.original_currency}{' '}
                          {item.provider_amount != null ? item.provider_amount.toLocaleString() : '-'}
                        </div>
                        <div className="text-[10px] text-muted-foreground">
                          FX {item.exchange_rate || 1} → {item.converted_amount != null ? item.converted_amount.toFixed(2) : '-'} USD
                        </div>
                      </TableCell>
                      <TableCell className="text-right text-xs">
                        {item.db_amount != null ? `$${item.db_amount.toLocaleString()}` : '-'}
                      </TableCell>
                      <TableCell className="text-right text-xs">
                        {item.provider_amount != null ? `$${item.provider_amount.toLocaleString()}` : '-'}
                      </TableCell>
                      <TableCell className="text-right text-xs">
                        {item.difference ? (
                          <span className={item.difference > 0 ? 'text-green-600' : 'text-red-600'}>
                            {item.difference.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">0.00</span>
                        )}
                      </TableCell>
                      <TableCell className="text-xs max-w-xs">
                        {item.risk_flag && (
                          <span className="text-red-600 font-semibold mr-1">[RISK]</span>
                        )}
                        {item.notes || '-'}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground">
                      No mismatch items reported for this run.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Auto-Scheduler Settings</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between">
              <Label>Enable Auto-Fetch from PSP APIs</Label>
              <Switch
                checked={!!schedule?.auto_fetch_enabled}
                disabled={scheduleLoading}
                onCheckedChange={(checked) =>
                  setSchedule((prev) => ({ ...(prev || {}), auto_fetch_enabled: checked }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Frequency</Label>
              <Select
                value={schedule?.frequency || 'daily'}
                disabled={scheduleLoading}
                onValueChange={(val) => setSchedule((prev) => ({ ...(prev || {}), frequency: val }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hourly">Hourly</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Provider</Label>
              <Input value={schedule?.provider || provider} disabled className="bg-muted" />
            </div>
            <p className="text-[10px] text-muted-foreground">
              API credentials are managed in Vault and not editable from this UI.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsSettingsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveSchedule} disabled={scheduleLoading}>
              Save Configuration
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ReconciliationPanel;
