import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import api from '../../services/api';

const GameSlotAdvancedTab = ({ game }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);


  const [form, setForm] = useState({
    spin_speed: 'normal',
    turbo_spin_allowed: false,
    autoplay_enabled: true,
    autoplay_default_spins: 50,
    autoplay_max_spins: 100,
    autoplay_stop_on_big_win: true,
    autoplay_stop_on_balance_drop_percent: '',
    big_win_animation_enabled: true,
    gamble_feature_allowed: false,
    summary: '',
  });

  useEffect(() => {
    if (!game) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get(`/v1/games/${game.id}/config/slot-advanced`);
        const cfg = res.data;
        setForm((prev) => ({
          ...prev,
          ...cfg,
          autoplay_stop_on_balance_drop_percent:
            cfg.autoplay_stop_on_balance_drop_percent ?? '',
          summary: '',
        }));
      } catch (err) {
        console.error(err);
        const apiError = err?.response?.data;
        if (apiError?.error_code === 'SLOT_ADVANCED_NOT_AVAILABLE_FOR_GAME') {
          setError(apiError.message || 'Slot advanced config not available for this game.');
        } else {
          toast.error('Slot advanced config yüklenemedi');
        }
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [game?.id]);

  const handleChange = (field, value) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleNumberChange = (field, value) => {
    const num = value === '' ? '' : Number(value);
    setForm((prev) => ({
      ...prev,
      [field]: num,
    }));
  };

  const handleSave = async () => {
    if (!game) return;
    setSaving(true);
    setError(null);
    try {
      const payload = {
        spin_speed: form.spin_speed,
        turbo_spin_allowed: !!form.turbo_spin_allowed,
        autoplay_enabled: !!form.autoplay_enabled,
        autoplay_default_spins: Number(form.autoplay_default_spins),
        autoplay_max_spins: Number(form.autoplay_max_spins),
        autoplay_stop_on_big_win: !!form.autoplay_stop_on_big_win,
        autoplay_stop_on_balance_drop_percent:
          form.autoplay_stop_on_balance_drop_percent === '' ||
          form.autoplay_stop_on_balance_drop_percent == null
            ? null
            : Number(form.autoplay_stop_on_balance_drop_percent),
        big_win_animation_enabled: !!form.big_win_animation_enabled,
        gamble_feature_allowed: !!form.gamble_feature_allowed,
        summary: form.summary || undefined,
      };

      const res = await api.post(`/v1/games/${game.id}/config/slot-advanced`, payload);
      const updated = res.data;
      toast.success('Slot advanced settings kaydedildi.');
      setForm((prev) => ({
        ...prev,
        ...updated,
        autoplay_stop_on_balance_drop_percent:
          updated.autoplay_stop_on_balance_drop_percent ?? '',
        summary: '',
      }));
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      if (apiError?.message) {
        toast.error(apiError.message);
      } else {
        toast.error('Slot advanced settings kaydedilemedi.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Spin &amp; Turbo</CardTitle>
          <CardDescription>Spin hızı ve turbo davranışı.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2 max-w-xs">
            <Label>Spin speed</Label>
            <Select
              value={form.spin_speed}
              onValueChange={(v) => handleChange('spin_speed', v)}
              disabled={loading}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="slow">Slow</SelectItem>
                <SelectItem value="normal">Normal</SelectItem>
                <SelectItem value="fast">Fast</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              checked={!!form.turbo_spin_allowed}
              onCheckedChange={(v) => handleChange('turbo_spin_allowed', v)}
              disabled={loading}
            />
            <span className="text-xs text-muted-foreground">Turbo spin allowed</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Autoplay</CardTitle>
          <CardDescription>Varsayılan autoplay davranışları.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Switch
              checked={!!form.autoplay_enabled}
              onCheckedChange={(v) => handleChange('autoplay_enabled', v)}
              disabled={loading}
            />
            <span className="text-xs text-muted-foreground">Autoplay enabled</span>
          </div>

          <div className="grid grid-cols-3 gap-4 max-w-xl">
            <div className="space-y-2">
              <Label>Default spins</Label>
              <Input
                type="number"
                value={form.autoplay_default_spins}
                onChange={(e) => handleNumberChange('autoplay_default_spins', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Max spins</Label>
              <Input
                type="number"
                value={form.autoplay_max_spins}
                onChange={(e) => handleNumberChange('autoplay_max_spins', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Stop on big win</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.autoplay_stop_on_big_win}
                  onCheckedChange={(v) => handleChange('autoplay_stop_on_big_win', v)}
                  disabled={loading}
                />
              </div>
            </div>
          </div>

          <div className="space-y-2 max-w-xs">
            <Label>Stop on balance drop (%)</Label>
            <Input
              type="number"
              value={form.autoplay_stop_on_balance_drop_percent}
              onChange={(e) =>
                handleNumberChange('autoplay_stop_on_balance_drop_percent', e.target.value)
              }
              disabled={loading}
              placeholder="örn. 50"
            />
            <p className="text-[10px] text-muted-foreground">
              Boş bırakılırsa bu kritere göre durdurma yapılmaz.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">UX &amp; Gamble</CardTitle>
          <CardDescription>VIP ve regülasyon uyumlu görsel davranışlar.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Switch
              checked={!!form.big_win_animation_enabled}
              onCheckedChange={(v) => handleChange('big_win_animation_enabled', v)}
              disabled={loading}
            />
            <span className="text-xs text-muted-foreground">Big win animation enabled</span>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              checked={!!form.gamble_feature_allowed}
              onCheckedChange={(v) => handleChange('gamble_feature_allowed', v)}
              disabled={loading}
            />
            <span className="text-xs text-muted-foreground">Gamble feature allowed</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Change summary</CardTitle>
          <CardDescription>Bu değişiklik için kısa bir açıklama.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Label>Summary (optional)</Label>
          <Input
            value={form.summary}
            onChange={(e) => handleChange('summary', e.target.value)}
            disabled={loading}
            placeholder="VIP slot advanced ayarı."
          />
          <Button onClick={handleSave} disabled={saving || loading} className="mt-2">
            {saving ? 'Saving...' : 'Save Advanced Settings'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default GameSlotAdvancedTab;
