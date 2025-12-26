import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, Database, HardDrive, ShieldCheck, RefreshCcw } from 'lucide-react';
import { toast } from 'sonner';

const OpsStatus = () => {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const res = await api.get('/v1/ops/health');
      setHealth(res.data);
    } catch (e) {
      toast.error('Failed to fetch Ops Health');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const getStatusColor = (status) => {
    if (status === 'ok' || status === 'green') return 'bg-green-500';
    if (status === 'warning') return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (!health) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">System Operations Status</h2>
        <Button onClick={fetchHealth} disabled={loading}>
          <RefreshCcw className="w-4 h-4 mr-2" /> Refresh
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold uppercase flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(health.status)}`} />
              {health.status}
            </div>
            <p className="text-xs text-muted-foreground">
              Last check: {new Date(health.timestamp).toLocaleTimeString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Database</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{health.components.database.status}</div>
            <p className="text-xs text-muted-foreground">
              Migration: {health.components.migrations.version || 'Unknown'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Audit Chain</CardTitle>
            <ShieldCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{health.components.audit_chain.status}</div>
            <p className="text-xs text-muted-foreground truncate">
              Head: {health.components.audit_chain.head_hash || 'N/A'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Storage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{health.components.storage.status}</div>
            <p className="text-xs text-muted-foreground">
              Backend: {health.components.storage.backend}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Raw Health Data</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="text-xs font-mono bg-slate-950 p-4 rounded text-green-400 overflow-auto">
            {JSON.stringify(health, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
};

export default OpsStatus;
