import React, { useEffect, useState } from 'react';
import { useCallback } from 'react';
import api from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';

import { MENU_ITEMS } from '../config/menu';

const featureKeys = [
  'can_use_game_robot',
  'can_edit_configs',
  'can_manage_bonus',
  'can_view_reports',
];

const TenantsPage = () => {
  const [tenants, setTenants] = useState([]);
  const [tenantsMeta, setTenantsMeta] = useState({ page: 1, page_size: 50, total: null });
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    name: '',
    type: 'renter',
    features: {
      can_use_game_robot: true,
      can_edit_configs: false,
      can_manage_bonus: true,
      can_view_reports: true,
    },
  });
  const [submitting, setSubmitting] = useState(false);
  const [editingTenant, setEditingTenant] = useState(null);
  const [editFeatures, setEditFeatures] = useState({});

  const loadTenants = useCallback(async (page = 1) => {
    try {
      setLoading(true);
      const res = await api.get('/v1/tenants/', { params: { page, page_size: tenantsMeta.page_size || 50 } });
      const data = res.data || {};
      setTenants(data.items || []);
      setTenantsMeta(data.meta || { page, page_size: tenantsMeta.page_size || 50, total: null });
    } catch (e) {
      console.error(e);
      toast.error('Tenants yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, [tenantsMeta.page_size]);

  useEffect(() => {
    loadTenants(1);
  }, [loadTenants]);

  const handleToggleFeature = (key) => {
    setForm((prev) => ({
      ...prev,
      features: {
        ...prev.features,
        [key]: !prev.features[key],
      },
    }));
  };

  const handleEditClick = (tenant) => {
    setEditingTenant(tenant);
    setEditFeatures(tenant.features || {});
  };

  const handleCancelEdit = () => {
    setEditingTenant(null);
    setEditFeatures({});
  };

  const handleSaveFeatures = async () => {
    if (!editingTenant) return;
    setSubmitting(true);
    try {
      await api.patch(`/v1/tenants/${editingTenant.id}`, { features: editFeatures });
      toast.success('Tenant features updated');
      setEditingTenant(null);
      setEditFeatures({});
      loadTenants();
    } catch (e) {
      console.error(e);
      toast.error('Failed to update tenant');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleEditFeature = (key) => {
    setEditFeatures((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleToggleMenuFlag = (key) => {
    setEditFeatures((prev) => {
        const currentFlags = prev.menu_flags || {};
        // If undefined, it means Enabled (default). So toggling means setting to false.
        // If false, toggling means setting to true (or undefined).
        // Let's be explicit: true/false.
        // But Layout logic is: if (flags[key] === false) hide.
        // So we default to true.
        
        const currentVal = currentFlags[key] !== false; // Default true
        return {
            ...prev,
            menu_flags: {
                ...currentFlags,
                [key]: !currentVal
            }
        };
    });
  };

  const groupedMenu = React.useMemo(() => {
    const groups = {};
    MENU_ITEMS.forEach(item => {
        if (!groups[item.section]) groups[item.section] = [];
        groups[item.section].push(item);
    });
    return groups;
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      toast.error('Tenant name zorunludur');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        name: form.name.trim(),
        type: form.type,
        features: form.features,
      };
      await api.post('/v1/tenants/', payload);
      toast.success('Tenant created');
      setTenantsMeta({ page: 1, page_size: tenantsMeta.page_size || 50, total: null });
      setForm({
        name: '',
        type: 'renter',
        features: {
          can_use_game_robot: true,
          can_edit_configs: false,
          can_manage_bonus: true,
          can_view_reports: true,
        },
      });
      loadTenants();
    } catch (e) {
      console.error(e);
      const msg = e?.response?.data?.detail || 'Tenant oluşturulamadı';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Tenants</h1>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Tenant List */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Existing Tenants</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-sm text-muted-foreground">Loading tenants...</div>
            ) : tenants.length === 0 ? (
              <div className="text-sm text-muted-foreground">No tenants found.</div>
            ) : (
              <div className="space-y-2 text-sm">
                {tenants.map((t) => (
                  <div
                    key={t.id}
                    className="border rounded-md px-3 py-2 flex items-center justify-between gap-4"
                  >
                    <div className="flex-1">
                      <div className="font-medium">
                        {t.name}{' '}
                        <span className="text-xs uppercase text-muted-foreground">({t.type})</span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1 flex flex-wrap gap-2">
                        <span>
                          Robot: {t.features?.can_use_game_robot ? 'On' : 'Off'}
                        </span>
                        <span>
                          Config: {t.features?.can_edit_configs ? 'On' : 'Off'}
                        </span>
                        <span>
                          Bonus: {t.features?.can_manage_bonus ? 'On' : 'Off'}
                        </span>
                        <span>
                          Reports: {t.features?.can_view_reports ? 'On' : 'Off'}
                        </span>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditClick(t)}
                    >
                      Edit Features
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
          <div className="flex items-center justify-between px-4 py-3 border-t text-xs text-muted-foreground">
            <div>
              Page {tenantsMeta.page}
              {tenantsMeta.total != null && tenantsMeta.page_size && (
                <span>
                  {' '}of {Math.max(1, Math.ceil(tenantsMeta.total / tenantsMeta.page_size))}
                </span>
              )}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={loading || tenantsMeta.page <= 1}
                onClick={() => {
                  const prevPage = (tenantsMeta.page || 1) - 1;
                  if (prevPage < 1) return;
                  loadTenants(prevPage).then(() => {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  });
                }}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={loading || tenants.length < (tenantsMeta.page_size || 50)}
                onClick={() => {
                  const nextPage = (tenantsMeta.page || 1) + 1;
                  loadTenants(nextPage).then(() => {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  });
                }}
              >
                Next
              </Button>
            </div>
          </div>
        </Card>

        {/* New Tenant Form */}
        <Card>
          <CardHeader>
            <CardTitle>Yeni Tenant / Kiracı Oluştur</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleCreate}>
              <div className="space-y-1">
                <Label>Name</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="Demo Renter X"
                />
              </div>

              <div className="space-y-1">
                <Label>Type</Label>
                <div className="flex gap-3 text-xs">
                  <button
                    type="button"
                    className={`px-2 py-1 rounded border ${
                      form.type === 'owner'
                        ? 'border-blue-500 text-blue-500'
                        : 'border-slate-700 text-slate-300'
                    }`}
                    onClick={() => setForm((prev) => ({ ...prev, type: 'owner' }))}
                  >
                    Owner
                  </button>
                  <button
                    type="button"
                    className={`px-2 py-1 rounded border ${
                      form.type === 'renter'
                        ? 'border-blue-500 text-blue-500'
                        : 'border-slate-700 text-slate-300'
                    }`}
                    onClick={() => setForm((prev) => ({ ...prev, type: 'renter' }))}
                  >
                    Renter
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Features</Label>
                <div className="space-y-2 text-xs">
                  {featureKeys.map((key) => (
                    <div key={key} className="flex items-center justify-between">
                      <span>{key}</span>
                      <Switch
                        checked={!!form.features[key]}
                        onCheckedChange={() => handleToggleFeature(key)}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? 'Creating...' : 'Create Tenant'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Edit Features Modal */}
      {editingTenant && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Edit Features - {editingTenant.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {featureKeys.map((key) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-slate-300">{key}</span>
                    <Switch
                      checked={!!editFeatures[key]}
                      onCheckedChange={() => handleToggleEditFeature(key)}
                    />
                  </div>
                ))}
              </div>
              <div className="flex gap-2 mt-6">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={handleCancelEdit}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleSaveFeatures}
                  disabled={submitting}
                >
                  {submitting ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default TenantsPage;
