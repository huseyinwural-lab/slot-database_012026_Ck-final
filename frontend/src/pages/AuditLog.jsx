import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { FileText, Eye, RefreshCcw, Download } from 'lucide-react';

const AuditLog = () => {
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [meta, setMeta] = useState({});

  const [filters, setFilters] = useState({
    action: '',
    resource_type: '',
    status: '',
    actor_user_id: '',
    request_id: '',
    since_hours: 24,
  });

  const fetchEvents = React.useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.action) params.action = filters.action;
      if (filters.resource_type) params.resource_type = filters.resource_type;
      if (filters.status && filters.status !== 'all') params.status = filters.status;
      if (filters.actor_user_id) params.actor_user_id = filters.actor_user_id;
      if (filters.request_id) params.request_id = filters.request_id;
      params.since_hours = filters.since_hours;
      params.limit = 200;

      const res = await api.get('/v1/audit/events', { params });
      setEvents(res.data.items || []);
      setMeta(res.data.meta || {});
    } catch (e) {
      console.error(e);
      toast.error('Failed to load audit events');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handleExport = async () => {
    try {
      const res = await api.get('/v1/audit/export', {
        params: { since_hours: filters.since_hours },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_export_${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (e) {
      toast.error('Export failed');
    }
  };

  const statusBadge = (status, result) => {
    // Fallback to result if status is missing (legacy events)
    const finalStatus = status || (result === 'success' ? 'SUCCESS' : result === 'failure' ? 'FAILED' : 'UNKNOWN');
    
    switch (finalStatus) {
      case 'SUCCESS': return <Badge variant="secondary" className="bg-green-100 text-green-800 hover:bg-green-100">SUCCESS</Badge>;
      case 'FAILED': return <Badge variant="destructive">FAILED</Badge>;
      case 'DENIED': return <Badge variant="destructive" className="bg-red-800">DENIED</Badge>;
      default: return <Badge variant="outline">{finalStatus}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <FileText className="w-7 h-7 text-blue-600" /> Audit Log
          </h2>
          <p className="text-sm text-muted-foreground">Immutable record of all administrative actions.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
          <Button onClick={fetchEvents} disabled={loading}>
            <RefreshCcw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Search audit trail by actor, action, resource or status.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1">
              <Label>Action</Label>
              <Input value={filters.action} onChange={(e) => setFilters({ ...filters, action: e.target.value })} placeholder="e.g. ROBOT_TOGGLE" />
            </div>
            <div className="space-y-1">
              <Label>Resource Type</Label>
              <Input value={filters.resource_type} onChange={(e) => setFilters({ ...filters, resource_type: e.target.value })} placeholder="e.g. robot" />
            </div>
            <div className="space-y-1">
              <Label>Status</Label>
              <Select value={filters.status || 'all'} onValueChange={(v) => setFilters({ ...filters, status: v })}>
                <SelectTrigger><SelectValue placeholder="All" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="SUCCESS">Success</SelectItem>
                  <SelectItem value="FAILED">Failed</SelectItem>
                  <SelectItem value="DENIED">Denied</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Actor ID</Label>
              <Input value={filters.actor_user_id} onChange={(e) => setFilters({ ...filters, actor_user_id: e.target.value })} placeholder="UUID" />
            </div>
            <div className="space-y-1">
              <Label>Request ID</Label>
              <Input value={filters.request_id} onChange={(e) => setFilters({ ...filters, request_id: e.target.value })} placeholder="Trace ID" />
            </div>
            <div className="space-y-1">
              <Label>Time Range</Label>
              <Select value={String(filters.since_hours)} onValueChange={(v) => setFilters({ ...filters, since_hours: Number(v) })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Last Hour</SelectItem>
                  <SelectItem value="6">Last 6 Hours</SelectItem>
                  <SelectItem value="24">Last 24 Hours</SelectItem>
                  <SelectItem value="168">Last 7 Days</SelectItem>
                  <SelectItem value="720">Last 30 Days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              variant="ghost"
              onClick={() => setFilters({ action: '', resource_type: '', status: '', actor_user_id: '', request_id: '', since_hours: 24 })}
            >
              Reset
            </Button>
            <Button onClick={fetchEvents} disabled={loading}>Apply Filters</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px]">Timestamp</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Resource</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead className="text-right">Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-10 text-muted-foreground">
                    No audit events found for the selected criteria.
                  </TableCell>
                </TableRow>
              ) : (
                events.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="text-xs whitespace-nowrap font-mono text-muted-foreground">
                      {new Date(e.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell className="font-medium">{e.action}</TableCell>
                    <TableCell>{statusBadge(e.status, e.result)}</TableCell>
                    <TableCell className="max-w-[200px] truncate text-xs" title={e.reason}>
                      {e.reason || '-'}
                    </TableCell>
                    <TableCell className="text-xs">
                      <div className="flex flex-col">
                        <span className="font-medium">{e.resource_type}</span>
                        <span className="text-muted-foreground text-[10px] truncate max-w-[100px]" title={e.resource_id}>
                          {e.resource_id}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs max-w-[150px] truncate" title={e.actor_user_id}>
                      {e.actor_user_id}
                    </TableCell>
                    <TableCell className="text-right">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-4xl max-h-[85vh] flex flex-col">
                          <DialogHeader>
                            <DialogTitle>Audit Event Details</DialogTitle>
                            <CardDescription className="font-mono text-xs text-muted-foreground">
                              ID: {e.id} • Request: {e.request_id}
                            </CardDescription>
                          </DialogHeader>
                          
                          <Tabs defaultValue="diff" className="flex-1 overflow-hidden flex flex-col">
                            <TabsList className="grid w-full grid-cols-4">
                              <TabsTrigger value="diff">Changes (Diff)</TabsTrigger>
                              <TabsTrigger value="states">Before/After</TabsTrigger>
                              <TabsTrigger value="meta">Metadata & Context</TabsTrigger>
                              <TabsTrigger value="raw">Raw JSON</TabsTrigger>
                            </TabsList>
                            
                            <ScrollArea className="flex-1 mt-4 border rounded-md bg-slate-950 p-4">
                              <TabsContent value="diff" className="mt-0">
                                {e.diff_json ? (
                                  <pre className="text-xs font-mono text-blue-400">
                                    {JSON.stringify(e.diff_json, null, 2)}
                                  </pre>
                                ) : (
                                  <div className="text-sm text-muted-foreground text-center italic py-8">
                                    No computed diff available for this event.
                                  </div>
                                )}
                              </TabsContent>
                              
                              <TabsContent value="states" className="mt-0">
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <h4 className="text-xs font-semibold text-red-400 mb-2 uppercase">Before</h4>
                                    <pre className="text-xs font-mono text-slate-300">
                                      {JSON.stringify(e.before_json || {}, null, 2)}
                                    </pre>
                                  </div>
                                  <div className="border-l pl-4 border-slate-800">
                                    <h4 className="text-xs font-semibold text-green-400 mb-2 uppercase">After</h4>
                                    <pre className="text-xs font-mono text-slate-300">
                                      {JSON.stringify(e.after_json || {}, null, 2)}
                                    </pre>
                                  </div>
                                </div>
                              </TabsContent>
                              
                              <TabsContent value="meta" className="mt-0 space-y-4">
                                <div>
                                  <h4 className="text-xs font-semibold text-purple-400 mb-1">Reason</h4>
                                  <p className="text-sm text-slate-200">{e.reason || 'No reason provided'}</p>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <h4 className="text-xs font-semibold text-purple-400 mb-1">Actor</h4>
                                    <p className="text-xs font-mono text-slate-300">User: {e.actor_user_id}</p>
                                    <p className="text-xs font-mono text-slate-300">Role: {e.actor_role || '-'}</p>
                                    <p className="text-xs font-mono text-slate-300">Tenant: {e.tenant_id}</p>
                                  </div>
                                  <div>
                                    <h4 className="text-xs font-semibold text-purple-400 mb-1">Network</h4>
                                    <p className="text-xs font-mono text-slate-300">IP: {e.ip_address}</p>
                                    <p className="text-xs font-mono text-slate-300">UA: {e.user_agent || '-'}</p>
                                  </div>
                                </div>
                                {e.metadata_json && (
                                  <div>
                                    <h4 className="text-xs font-semibold text-purple-400 mb-1">Additional Metadata</h4>
                                    <pre className="text-xs font-mono text-slate-300">
                                      {JSON.stringify(e.metadata_json, null, 2)}
                                    </pre>
                                  </div>
                                )}
                              </TabsContent>
                              
                              <TabsContent value="raw" className="mt-0">
                                <pre className="text-xs font-mono text-green-400">
                                  {JSON.stringify(e, null, 2)}
                                </pre>
                              </TabsContent>
                            </ScrollArea>
                          </Tabs>
                        </DialogContent>
                      </Dialog>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default AuditLog;
