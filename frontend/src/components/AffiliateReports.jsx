import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { toast } from 'sonner';

const Metric = ({ label, value }) => {
  return (
    <div className="p-4 rounded-lg border bg-background">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
};

const AffiliateReports = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      try {
        const res = await api.get('/v1/affiliates/reports/summary');
        setData(res.data);
      } catch (e) {
        toast.error(e?.standardized?.message || e?.standardized?.code || 'Failed to load report');
      } finally {
        setLoading(false);
      }
    };

    run();
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Summary</CardTitle>
        <CardDescription>P0 metrics: clicks, registrations, first deposits, payouts.</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-sm text-muted-foreground">Loading...</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Metric label="Clicks" value={data?.clicks ?? 0} />
            <Metric label="Registrations" value={data?.signups ?? 0} />
            <Metric label="First Deposits" value={data?.first_deposits ?? 0} />
            <Metric label="Payouts" value={data?.payouts ?? 0} />
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AffiliateReports;
