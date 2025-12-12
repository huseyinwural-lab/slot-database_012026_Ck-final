import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import api from '../../services/api';

const NewMemberManualBonusCard = () => {
  const [config, setConfig] = useState({
    enabled: false,
    allowed_game_ids: [],
    spin_count: 0,
    fixed_bet_amount: 0,
    total_budget_cap: 0,
    validity_days: 7,
  });

  const summary = React.useMemo(() => {
    const gameCount = (config.allowed_game_ids || []).length;
    const parts = [];
    parts.push(`${gameCount} game${gameCount === 1 ? '' : 's'}`);
    if (config.spin_count) parts.push(`${config.spin_count} spins`);
    if (config.fixed_bet_amount) parts.push(`${config.fixed_bet_amount} EUR/spin`);
    if (config.total_budget_cap) parts.push(`limit ${config.total_budget_cap} EUR`);
    return parts.join(' • ');
  }, [config]);

  const [games, setGames] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [cfgRes, gamesRes] = await Promise.all([
          api.get('/v1/bonus/config/new-member-manual'),
          api.get('/v1/games', { params: { limit: 200 } }),
        ]);
        setConfig(cfgRes.data);
        setGames(gamesRes.data || []);
      } catch (err) {
        console.error(err);
        toast.error('Failed to load new member bonus configuration');
      }
    };
    load();
  }, []);

  const handleSave = async () => {
    try {
      const payload = { ...config };
      await api.put('/v1/bonus/config/new-member-manual', payload);
      toast.success('New member bonus configuration updated');
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      toast.error(apiError?.detail || apiError?.message || 'Save failed');
    }
  };

  const toggleGame = (gameId) => {
    const exists = (config.allowed_game_ids || []).includes(gameId);
    setConfig({
      ...config,
      allowed_game_ids: exists
        ? config.allowed_game_ids.filter((id) => id !== gameId)
        : [...(config.allowed_game_ids || []), gameId],
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-lg">
          New Member Manual Bonus
          <div className="flex items-center gap-2 text-xs">
            <Switch
              checked={config.enabled}
              onCheckedChange={(v) => setConfig({ ...config, enabled: v })}
            />
            <span>New member bonus active</span>
          </div>
        </CardTitle>
        <CardDescription className="text-xs">
          This bonus is automatically activated only for newly registered players.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid md:grid-cols-4 gap-3">
          <div className="space-y-1">
            <Label>Number of spins</Label>
            <Input
              type="number"
              value={config.spin_count}
              onChange={(e) => setConfig({ ...config, spin_count: Number(e.target.value) || 0 })}
            />
          </div>
          <div className="space-y-1">
            <Label>Amount per spin (EUR)</Label>
            <Input
              type="number"
              value={config.fixed_bet_amount}
              onChange={(e) =>
                setConfig({ ...config, fixed_bet_amount: Number(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-1">
            <Label>Total budget cap (EUR)</Label>
            <Input
              type="number"
              value={config.total_budget_cap}
              onChange={(e) =>
                setConfig({ ...config, total_budget_cap: Number(e.target.value) || 0 })
              }
            />
          </div>
          <div className="space-y-1">
            <Label>Geçerlilik (gün)</Label>
            <Input
              type="number"
              value={config.validity_days}
              onChange={(e) =>
                setConfig({ ...config, validity_days: Number(e.target.value) || 0 })
              }
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Oyun Ara / Seç</Label>
          <div className="max-h-48 overflow-auto border rounded-md p-2 text-xs space-y-1">
            {games.map((g) => {
              const selected = (config.allowed_game_ids || []).includes(g.id);
              return (
                <button
                  key={g.id}
                  type="button"
                  onClick={() => toggleGame(g.id)}
                  className={`w-full flex items-center justify-between px-2 py-1 rounded text-left hover:bg-secondary/60 ${
                    selected ? 'bg-secondary' : ''
                  }`}
                >
                  <span className="truncate mr-2">{g.name}</span>
                  {selected && <span className="text-[10px] text-green-400">SEÇİLİ</span>}
                </button>
              );
            })}
            {(!games || games.length === 0) && (
              <div className="text-[11px] text-muted-foreground">Henüz oyun bulunamadı.</div>
            )}
          </div>
        </div>

        {summary && (
          <div className="text-[11px] text-muted-foreground">
            Özet: <span className="font-medium text-foreground">{summary}</span>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <Button size="sm" onClick={handleSave}>
            Konfigürasyonu Kaydet
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default NewMemberManualBonusCard;
