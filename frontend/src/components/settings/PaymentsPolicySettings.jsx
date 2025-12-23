import React, { useEffect, useState } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

const numberOrEmpty = (v) => (v === null || v === undefined ? '' : String(v));

const PaymentsPolicySettings = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [policy, setPolicy] = useState({
    min_deposit: '',
    max_deposit: '',
    min_withdraw: '',
    max_withdraw: '',
    daily_deposit_limit: '',
    daily_withdraw_limit: '',
    payout_retry_limit: '',
    payout_cooldown_seconds: '',
  });

  const fetchPolicy = async () => {
    setLoading(true);
    try {
      const res = await api.get('/v1/tenants/payments/policy');
      const data = res.data;
      setPolicy({
        min_deposit: numberOrEmpty(data.min_deposit),
        max_deposit: numberOrEmpty(data.max_deposit),
        min_withdraw: numberOrEmpty(data.min_withdraw),
        max_withdraw: numberOrEmpty(data.max_withdraw),
        daily_deposit_limit: numberOrEmpty(data.daily_deposit_limit),
        daily_withdraw_limit: numberOrEmpty(data.daily_withdraw_limit),
        payout_retry_limit: numberOrEmpty(data.payout_retry_limit),
        payout_cooldown_seconds: numberOrEmpty(data.payout_cooldown_seconds),
      });
    } catch (err) {
      console.error(err);
      toast.error('Payments policy yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicy();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleChange = (field) => (e) => {
    setPolicy((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {};
      Object.entries(policy).forEach(([k, v]) => {
        if (v === '') {
          payload[k] = null;
        } else if (k.includes('limit') || k.includes('deposit') || k.includes('withdraw')) {
          payload[k] = parseFloat(v);
        } else {
          payload[k] = parseInt(v, 10);
        }
      });

      await api.put('/v1/tenants/payments/policy', payload);
      toast.success('Payments policy kaydedildi');
      fetchPolicy();
    } catch (err) {
      console.error(err);
      toast.error('Payments policy kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tenant Payments Policy</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <p className="text-muted-foreground text-sm">Yükleniyor...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Min Deposit</Label>
              <Input
                type="number"
                step="0.01"
                value={policy.min_deposit}
                onChange={handleChange('min_deposit')}
              />
            </div>
            <div className="space-y-2">
              <Label>Max Deposit</Label>
              <Input
                type="number"
                step="0.01"
                value={policy.max_deposit}
                onChange={handleChange('max_deposit')}
              />
            </div>
            <div className="space-y-2">
              <Label>Min Withdraw</Label>
              <Input
                type="number"
                step="0.01"
                value={policy.min_withdraw}
                onChange={handleChange('min_withdraw')}
              />
            </div>
            <div className="space-y-2">
              <Label>Max Withdraw</Label>
              <Input
                type="number"
                step="0.01"
                value={policy.max_withdraw}
                onChange={handleChange('max_withdraw')}
              />
            </div>
            <div className="space-y-2">
              <Label>Daily Deposit Limit</Label>
              <Input
                type="number"
                step="0.01"
                value={policy.daily_deposit_limit}
                onChange={handleChange('daily_deposit_limit')}
              />
            </div>
            <div className="space-y-2">
              <Label>Daily Withdraw Limit</Label>
              <Input
                type="number"
                step="0.01"
                value={policy.daily_withdraw_limit}
                onChange={handleChange('daily_withdraw_limit')}
              />
            </div>
            <div className="space-y-2">
              <Label>Payout Retry Limit</Label>
              <Input
                type="number"
                value={policy.payout_retry_limit}
                onChange={handleChange('payout_retry_limit')}
              />
            </div>
            <div className="space-y-2">
              <Label>Payout Cooldown (seconds)</Label>
              <Input
                type="number"
                value={policy.payout_cooldown_seconds}
                onChange={handleChange('payout_cooldown_seconds')}
              />
            </div>
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <Button onClick={handleSave} disabled={saving}>
            {saving ? 'Kaydediliyor...' : 'Kaydet'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default PaymentsPolicySettings;
