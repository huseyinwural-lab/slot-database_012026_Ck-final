import React, { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { ShieldAlert, CheckCircle, Save, AlertTriangle } from 'lucide-react';
import api from '../../services/api';
import { toast } from 'sonner';

const GameEngineTab = ({ game, onUpdated }) => {
  const [loading, setLoading] = useState(false);
  const [profiles, setProfiles] = useState([]);
  const [engineState, setEngineState] = useState({
    mode: 'STANDARD',
    profile_code: '',
    custom_params: {},
    params: {} // Effective params from backend
  });
  const [reason, setReason] = useState('');
  const [customJson, setCustomJson] = useState('{}');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [stdRes, confRes] = await Promise.all([
        api.get('/v1/engine/standards'),
        api.get(`/v1/engine/game/${game.id}/config`)
      ]);
      setProfiles(stdRes.data);
      
      const conf = confRes.data;
      setEngineState({
        mode: conf.mode || 'STANDARD',
        profile_code: conf.profile_code || stdRes.data[0]?.code,
        custom_params: conf.params || {},
        params: conf.params || {}
      });
      setCustomJson(JSON.stringify(conf.params || {}, null, 2));
    } catch (e) {
      toast.error('Failed to load engine data');
  }, [game?.id]);

  useEffect(() => {
    if (!game?.id) return;
    loadData();
  }, [loadData, game?.id]);


    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!reason) {
      toast.error('Reason is required');
      return;
    }
    
    let paramsToSend = {};
    if (engineState.mode === 'CUSTOM') {
      try {
        paramsToSend = JSON.parse(customJson);
      } catch (e) {
        toast.error('Invalid JSON in Custom Params');
        return;
      }
    }

    setLoading(true);
    try {
      const res = await api.post(`/v1/engine/game/${game.id}/config`, {
        mode: engineState.mode,
        profile_code: engineState.profile_code,
        custom_params: paramsToSend,
        reason: reason
      });
      
      if (res.data.review_required) {
        toast.warning('Update saved but marked as DANGEROUS. Review required.');
      } else {
        toast.success('Engine config updated');
      }
      onUpdated?.();
      loadData();
    } catch (e) {
      toast.error('Update failed');
    } finally {
      setLoading(false);
    }
  };

  const selectedProfile = profiles.find(p => p.code === engineState.profile_code);

  return (
    <div className="space-y-6 pt-4">
      <div className="grid grid-cols-2 gap-6">
        {/* Left: Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Engine Configuration</CardTitle>
            <CardDescription>Select Standard Profile or Override</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Mode</Label>
              <Select 
                value={engineState.mode} 
                onValueChange={(v) => setEngineState({...engineState, mode: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="STANDARD">Standard (Safe)</SelectItem>
                  <SelectItem value="CUSTOM">Custom (Advanced)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Base Profile</Label>
              <Select 
                value={engineState.profile_code} 
                onValueChange={(v) => setEngineState({...engineState, profile_code: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {profiles.map(p => (
                    <SelectItem key={p.code} value={p.code}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedProfile && (
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedProfile.description}
                </p>
              )}
            </div>

            {engineState.mode === 'CUSTOM' && (
              <div className="space-y-2">
                <Label>Override Parameters (JSON)</Label>
                <Textarea 
                  value={customJson}
                  onChange={(e) => setCustomJson(e.target.value)}
                  className="font-mono text-xs h-40"
                />
                <p className="text-[10px] text-yellow-500 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> 
                  Custom overrides may trigger safety review.
                </p>
              </div>
            )}

            <div className="space-y-2 pt-4 border-t">
              <Label>Change Reason (Mandatory)</Label>
              <Input 
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. Requested by Tenant A for campaign..."
              />
            </div>

            <Button onClick={handleSave} disabled={loading} className="w-full">
              <Save className="w-4 h-4 mr-2" /> 
              Apply Configuration
            </Button>
          </CardContent>
        </Card>

        {/* Right: Effective Config Preview */}
        <Card>
          <CardHeader>
            <CardTitle>Effective Configuration</CardTitle>
            <div className="flex gap-2">
               {engineState.mode === 'STANDARD' ? (
                 <Badge variant="outline" className="bg-green-500/10 text-green-500">Standard</Badge>
               ) : (
                 <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500">Custom</Badge>
               )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="bg-slate-950 p-4 rounded-md overflow-auto h-[350px]">
              <pre className="text-xs font-mono text-green-400">
                {JSON.stringify(engineState.params, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default GameEngineTab;
