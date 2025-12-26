import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Bot, RefreshCw } from 'lucide-react';
import api from '../../services/api';

const GameRobotTab = ({ game }) => {
  const [currentBinding, setCurrentBinding] = useState(null);
  const [robots, setRobots] = useState([]);
  const [selectedRobotId, setSelectedRobotId] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchBinding = async () => {
    try {
      const res = await api.get(`/v1/games/${game.id}/robot`);
      if (res.data && res.data.robot_id) {
        setCurrentBinding(res.data);
        setSelectedRobotId(res.data.robot_id);
      } else {
        setCurrentBinding(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchRobots = async () => {
    try {
      const res = await api.get('/v1/robots', { params: { is_active: true } });
      setRobots(res.data.items || []);
    } catch (e) {
      toast.error('Failed to load robots');
    }
  };

  useEffect(() => {
    if (game) {
      fetchBinding();
      fetchRobots();
    }
  }, [game]);

  const handleBind = async () => {
    if (!selectedRobotId) return;
    setLoading(true);
    try {
      await api.post(`/v1/games/${game.id}/robot`, { robot_id: selectedRobotId });
      toast.success('Robot bound successfully');
      fetchBinding();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Binding failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5" /> Math Engine Binding
          </CardTitle>
          <CardDescription>
            Bind a deterministic Math Model (Robot) to this game.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {currentBinding ? (
            <div className="p-4 border rounded-lg bg-slate-50 dark:bg-slate-900">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-muted-foreground">Current Robot</span>
                <Badge variant={currentBinding.is_active ? 'default' : 'destructive'}>
                  {currentBinding.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              <div className="text-lg font-bold">{currentBinding.robot_name}</div>
              <div className="text-xs font-mono text-muted-foreground mt-1">
                Hash: {currentBinding.config_hash}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Effective: {new Date(currentBinding.effective_from).toLocaleString()}
              </div>
            </div>
          ) : (
            <div className="p-4 border border-dashed rounded-lg text-center text-muted-foreground">
              No robot currently bound. Game will use default/mock or fail.
            </div>
          )}

          <div className="space-y-2">
            <Label>Select Robot Engine</Label>
            <div className="flex gap-2">
              <Select value={selectedRobotId} onValueChange={setSelectedRobotId}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Select a robot..." />
                </SelectTrigger>
                <SelectContent>
                  {robots.map(r => (
                    <SelectItem key={r.id} value={r.id}>
                      {r.name} ({r.config_hash.substring(0,6)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button onClick={handleBind} disabled={loading || !selectedRobotId}>
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                {currentBinding ? 'Switch Robot' : 'Bind Robot'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GameRobotTab;