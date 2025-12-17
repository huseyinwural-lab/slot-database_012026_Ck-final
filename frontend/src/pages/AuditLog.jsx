import React, { useEffect, useMemo, useState } from 'react';
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
import { toast } from 'sonner';
import { FileText, Eye, RefreshCcw } from 'lucide-react';

const AuditLog = () => {
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [meta, setMeta] = useState({});

  const [filters, setFilters] = useState({
    action: '',
    resource_type: '',
    result: '',
    actor_user_id: '',
    request_id: '',
    since_hours: 24,
  });

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.action) params.action = filters.action;
      if (filters.resource_type) params.resource_type = filters.resource_type;
      if (filters.result) params.result = filters.result;
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
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const resultBadge = (result) => {
    if (result === 'success') return <Badge variant="secondary">success</Badge>;
    if (result === 'blocked') return <Badge variant="destructive">blocked</Badge>;
    if (result === 'failure') return <Badge variant="destructive">failure</Badge>;
    return <Badge variant="outline">{result || 'unknown'}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <FileText className="w-7 h-7 text-blue-600" /> Audit Log
          </h2>
          <p className="text-sm text-muted-foreground">Admin actions (retention: 90 days)</p>
        </div>
        <Button onClick={fetchEvents} disabled={loading}>
          <RefreshCcw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter by action, resource type, actor, result, or request id.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Action</Label>
              <Input value={filters.action} onChange={(e) => setFilters({ ...filters, action: e.target.value })} placeholder="tenant.created" />
            </div>
            <div>
              <Label>Resource Type</Label>
              <Input value={filters.resource_type} onChange={(e) => setFilters({ ...filters, resource_type: e.target.value })} placeholder="tenant / admin_user" />
            </div>
            <div>
              <Label>Result</Label>
              <Select value={filters.result || 'all'} onValueChange={(v) => setFilters({ ...filters, result: v === 'all' ? '' : v })}>
                <SelectTrigger><SelectValue placeholder="All" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="success">success</SelectItem>
                  <SelectItem value="failure">failure</SelectItem>
                  <SelectItem value="blocked">blocked</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Actor User ID</Label>
              <Input value={filters.actor_user_id} onChange={(e) => setFilters({ ...filters, actor_user_id: e.target.value })} placeholder="admin uuid" />
            </div>
            <div>
              <Label>Request ID</Label>
              <Input value={filters.request_id} onChange={(e) => setFilters({ ...filters, request_id: e.target.value })} placeholder="X-Request-ID" />
            </div>
            <div>
              <Label>Since (hours)</Label>
              <Select value={String(filters.since_hours)} onValueChange={(v) => setFilters({ ...filters, since_hours: Number(v) })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1</SelectItem>
                  <SelectItem value="6">6</SelectItem>
                  <SelectItem value="24">24</SelectItem>
                  <SelectItem value="168">168 (7d)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={fetchEvents} disabled={loading}>Apply</Button>
            <Button
              variant="outline"
              onClick={() => setFilters({ action: '', resource_type: '', result: '', actor_user_id: '', request_id: '', since_hours: 24 })}
            >
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Events</CardTitle>
          <CardDescription>Showing up to 200 events. {meta?.since_hours ? `Since: last ${meta.since_hours}h` : ''}</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-10 text-muted-foreground">Loading...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Tenant</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Result</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {events.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="text-xs whitespace-nowrap">{new Date(e.timestamp).toLocaleString()}</TableCell>
                    <TableCell className="font-medium">{e.action}</TableCell>
                    <TableCell className="text-xs">
                      <div className="flex flex-col">
                        <span>{e.resource_type}</span>
                        <span className="text-muted-foreground">{e.resource_id || '-'}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs">{e.tenant_id}</TableCell>
                    <TableCell className="text-xs">{e.actor_user_id}</TableCell>
                    <TableCell>{resultBadge(e.result)}</TableCell>
                    <TableCell className="text-right">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="ghost" size="sm"><Eye className="w-4 h-4" /></Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-3xl">
                          <DialogHeader><DialogTitle>Audit Event</DialogTitle></DialogHeader>
                          <ScrollArea className="max-h-[60vh] pr-4">
                            <div className="space-y-3 text-sm">
                              <div><span className="font-medium">Request ID:</span> {e.request_id}</div>
                              <div><span className="font-medium">Actor:</span> {e.actor_user_id}</div>
                              <div><span className="font-medium">Tenant:</span> {e.tenant_id}</div>
                              <div><span className="font-medium">Action:</span> {e.action}</div>
                              <div><span className="font-medium">Resource:</span> {e.resource_type} / {e.resource_id || '-'}</div>
                              <div><span className="font-medium">Result:</span> {e.result}</div>
                              <div><span className="font-medium">IP:</span> {e.ip_address || '-'}</div>
                              <div>
                                <span className="font-medium">Details (masked):</span>
                                <pre className="mt-2 bg-secondary/50 p-3 rounded text-xs overflow-auto">{JSON.stringify(e.details || {}, null, 2)}</pre>
                              </div>
                            </div>
                          </ScrollArea>
                        </DialogContent>
                      </Dialog>
                    </TableCell>
                  </TableRow>
                ))}
                {events.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground py-10">No events</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AuditLog;
