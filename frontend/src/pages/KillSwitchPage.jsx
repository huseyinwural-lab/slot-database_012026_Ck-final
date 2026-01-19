import React, { useEffect, useState } from 'react';
import api from '../services/api';
import RequireFeature from '../components/RequireFeature';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';

const KillSwitchPage = () => {
  const [tenants, setTenants] = useState([]);
  const [tenantId, setTenantId] = useState('');
  const [moduleKey, setModuleKey] = useState('crm');
  const [disabled, setDisabled] = useState(true);

  const loadTenants = async () => {
    try {
      const res = await api.get('/v1/tenants/');
      const tenantsData = Array.isArray(res.data?.items) ? res.data.items : [];
      setTenants(tenantsData);

      // Auto-select Demo tenant if present and nothing selected yet
      // Do not auto-select: P0 requires Apply disabled until tenant is explicitly chosen.
    } catch (e) {
      console.error('Failed to load tenants:', e);
      toast.error('Failed to load tenants');
      setTenants([]); // Ensure we have an empty array on error
    }
  };

  useEffect(() => {
    const t = setTimeout(() => {
      loadTenants();
    }, 0);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const apply = async () => {
    if (!tenantId) return;
    try {
      await api.post('/v1/kill-switch/tenant', { tenant_id: tenantId, module_key: moduleKey, disabled });
      toast.success('Kill switch updated');
    } catch (e) {
      toast.error(e?.standardized?.message || 'Failed to update');
    }
  };

  return (
    <RequireFeature feature="can_use_kill_switch">
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Kill Switch</h1>

        <Card>
          <CardHeader>
            <CardTitle>Tenant Module Kill Switch</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <div className="text-xs text-muted-foreground mb-1">Tenant</div>
                <Select value={tenantId} onValueChange={setTenantId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select tenant" />
                  </SelectTrigger>
                  <SelectContent>
                    {tenants.map((t) => (
                      <SelectItem key={t.id} value={t.id}>{t.name} ({t.id})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <div className="text-xs text-muted-foreground mb-1">Module</div>
                <Select value={moduleKey} onValueChange={setModuleKey}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select module" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="crm">CRM</SelectItem>
                    <SelectItem value="affiliates">Affiliates</SelectItem>
                    <SelectItem value="experiments">Experiments</SelectItem>
                    <SelectItem value="kill_switch">Kill Switch</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <div className="text-xs text-muted-foreground mb-1">State</div>
                <Select value={disabled ? 'disabled' : 'enabled'} onValueChange={(v) => setDisabled(v === 'disabled')}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select state" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="enabled">Enabled</SelectItem>
                    <SelectItem value="disabled">Disabled (503)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button onClick={apply} disabled={!tenantId}>Apply</Button>
              {!tenantId && <div className="text-xs text-muted-foreground">Tenant required</div>}
            </div>
          </CardContent>
        </Card>
      </div>
    </RequireFeature>
  );
};

export default KillSwitchPage;
