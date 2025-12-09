import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { FlaskConical } from 'lucide-react';

const FeatureFlags = () => {
  const [flags, setFlags] = useState([]);

  const fetchFlags = async () => {
    try {
        const res = await api.get('/v1/features');
        setFlags(res.data);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchFlags(); }, []);

  const toggleFlag = async (id) => {
    try {
        await api.post(`/v1/features/${id}/toggle`);
        setFlags(flags.map(f => f.id === id ? { ...f, is_enabled: !f.is_enabled } : f));
        toast.success("Feature flag updated");
    } catch (err) {
        toast.error("Failed to update flag");
    }
  };

  return (
    <div className="space-y-6">
        <div>
            <h2 className="text-3xl font-bold tracking-tight">Feature Flags & A/B Tests</h2>
            <p className="text-muted-foreground">Manage rollout of new features and experiments without code deployment.</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {flags.map(flag => (
                <Card key={flag.id} className={flag.is_enabled ? "border-primary/50 bg-primary/5" : "opacity-70"}>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <FlaskConical className={`w-6 h-6 ${flag.is_enabled ? 'text-primary' : 'text-muted-foreground'}`} />
                        <Switch checked={flag.is_enabled} onCheckedChange={() => toggleFlag(flag.id)} />
                    </CardHeader>
                    <CardContent>
                        <div className="font-bold text-lg mb-1">{flag.key}</div>
                        <p className="text-sm text-muted-foreground mb-4">{flag.description}</p>
                        <div className="text-xs font-mono bg-background p-2 rounded border">
                            Rollout: {flag.rollout_percentage}%
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    </div>
  );
};

export default FeatureFlags;
