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

const GameCrashMathTab = ({ game }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState('');

  const [form, setForm] = useState({
    base_rtp: 96.0,
    volatility_profile: 'medium',
    min_multiplier: 1.0,
    max_multiplier: 500.0,
    max_auto_cashout: 100.0,
    round_duration_seconds: 12,
    bet_phase_seconds: 6,
    grace_period_seconds: 2,
    min_bet_per_round: '',
    max_bet_per_round: '',
    provably_fair_enabled: true,
    rng_algorithm: 'sha256_chain',
    seed_rotation_interval_rounds: 10000,
    summary: '',
  });

  useEffect(() => {
    if (!game) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [cfgRes, presetRes] = await Promise.all([
          api.get(`/v1/games/${game.id}/config/crash-math`),
          api.get('/v1/game-config/presets', {
            params: { game_type: game.core_type, config_type: 'crash_math' },
          }),
        ]);

        const data = cfgRes.data;
        setForm((prev) => ({
          ...prev,
          ...data,
          min_bet_per_round: data.min_bet_per_round ?? '',
          max_bet_per_round: data.max_bet_per_round ?? '',
          summary: '',
        }));

        setPresets(presetRes.data?.presets || []);
      } catch (err) {
        console.error(err);
        const apiError = err?.response?.data;
        if (apiError?.error_code) {
          setError(apiError.message || 'Crash math config yüklenemedi.');
        } else {
          toast.error('Crash math config yüklenemedi.');
        }
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [game?.id, game?.core_type]);

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleNumberChange = (field, value) => {
    const num = value === '' ? '' : Number(value);
    setForm((prev) => ({ ...prev, [field]: num }));
  };

  const handleApplyPreset = async () => {
    if (!selectedPreset || !game) return;
    try {
      const res = await api.get(`/v1/game-config/presets/${selectedPreset}`);
      const preset = res.data;
      if (preset?.values) {
        setForm((prev) => ({
          ...prev,
          ...preset.values,
          min_bet_per_round: preset.values.min_bet_per_round ?? '',
          max_bet_per_round: preset.values.max_bet_per_round ?? '',
          summary: preset.values.summary || prev.summary,
        }));
      }
      // apply log
      await api.post(`/v1/game-config/presets/${selectedPreset}/apply`, {
        game_id: game.id,
        game_type: game.core_type,
        config_type: 'crash_math',
      });
      toast.success('Preset uygulandı. Değerler forma yansıtıldı.');
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      toast.error(apiError?.message || 'Preset uygulanamadı.');
    }
  };

  const handleSave = async () => {
    if (!game) return;
    setSaving(true);
    setError(null);
    try {
      const payload = {
        base_rtp: Number(form.base_rtp),
        volatility_profile: form.volatility_profile,
        min_multiplier: Number(form.min_multiplier),
        max_multiplier: Number(form.max_multiplier),
        max_auto_cashout: Number(form.max_auto_cashout),
        round_duration_seconds: Number(form.round_duration_seconds),
        bet_phase_seconds: Number(form.bet_phase_seconds),
        grace_period_seconds: Number(form.grace_period_seconds),
        min_bet_per_round:
          form.min_bet_per_round === '' || form.min_bet_per_round == null
            ? null
            : Number(form.min_bet_per_round),
        max_bet_per_round:
          form.max_bet_per_round === '' || form.max_bet_per_round == null
            ? null
            : Number(form.max_bet_per_round),
        provably_fair_enabled: !!form.provably_fair_enabled,
        rng_algorithm: form.rng_algorithm,
        seed_rotation_interval_rounds:
          form.seed_rotation_interval_rounds === '' ||
          form.seed_rotation_interval_rounds == null
            ? null
            : Number(form.seed_rotation_interval_rounds),
        summary: form.summary || undefined,
      };

      const res = await api.post(`/v1/games/${game.id}/config/crash-math`, payload);
      toast.success('Crash math config kaydedildi.');
      const updated = res.data;
      setForm((prev) => ({
        ...prev,
        ...updated,
        min_bet_per_round: updated.min_bet_per_round ?? '',
        max_bet_per_round: updated.max_bet_per_round ?? '',
        summary: '',
      }));
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      if (apiError?.message) {
        toast.error(apiError.message);
        setError(apiError.message);
      } else {
        toast.error('Crash math config kaydedilemedi.');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Preset bar */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Preset</CardTitle>
          <CardDescription>
            Crash math için hazır profilleri uygula, ardından gerekirse manuel olarak düzenle.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col sm:flex-row gap-2 items-start sm:items-end">
          <div className="flex-1 space-y-1">
            <Label>Preset seç</Label>
            <Select
              value={selectedPreset}
              onValueChange={setSelectedPreset}
              disabled={loading || presets.length === 0}
            >
              <SelectTrigger>
                <SelectValue placeholder={presets.length ? 'Seçiniz' : 'Preset bulunamadı'} />
              </SelectTrigger>
              <SelectContent>
                {presets.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button
            type="button"
            onClick={handleApplyPreset}
            disabled={loading || !selectedPreset}
            className="whitespace-nowrap"
          >
            Apply Preset
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">RTP &amp; Volatility</CardTitle>
          <CardDescription>Crash oyununun temel RTP ve volatilite profilini yapılandır.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Base RTP (%)</Label>
              <Input
                type="number"
                value={form.base_rtp}
                onChange={(e) => handleNumberChange('base_rtp', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Volatility Profile</Label>
              <Select
                value={form.volatility_profile}
                onValueChange={(v) => handleChange('volatility_profile', v)}
                disabled={loading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Multipliers</CardTitle>
          <CardDescription>
            Min/max multiplier ve oyuncuların seçebileceği max auto-cashout sınırını belirle.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Min Multiplier</Label>
              <Input
                type="number"
                value={form.min_multiplier}
                onChange={(e) => handleNumberChange('min_multiplier', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Max Multiplier</Label>
              <Input
                type="number"
                value={form.max_multiplier}
                onChange={(e) => handleNumberChange('max_multiplier', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Max Auto-Cashout</Label>
              <Input
                type="number"
                value={form.max_auto_cashout}
                onChange={(e) => handleNumberChange('max_auto_cashout', e.target.value)}
                disabled={loading}
              />
              <p className="text-[10px] text-muted-foreground mt-1">
                Gerçek crash motoru max multiplier&apos;ı garantilemeyebilir, bu sadece UI sınırını belirler.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Round Timing</CardTitle>
          <CardDescription>Round süresi, bet phase ve grace period ayarları.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Round Duration (sec)</Label>
              <Input
                type="number"
                value={form.round_duration_seconds}
                onChange={(e) => handleNumberChange('round_duration_seconds', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Bet Phase (sec)</Label>
              <Input
                type="number"
                value={form.bet_phase_seconds}
                onChange={(e) => handleNumberChange('bet_phase_seconds', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Grace Period (sec)</Label>
              <Input
                type="number"
                value={form.grace_period_seconds}
                onChange={(e) => handleNumberChange('grace_period_seconds', e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Bet Limits (optional)</CardTitle>
          <CardDescription>Bu alanlar doluysa bet_config üzerini override eder.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Min Bet per Round</Label>
              <Input
                type="number"
                value={form.min_bet_per_round}
                onChange={(e) => handleNumberChange('min_bet_per_round', e.target.value)}
                disabled={loading}
                placeholder="(optional)"
              />
            </div>
            <div className="space-y-2">
              <Label>Max Bet per Round</Label>
              <Input
                type="number"
                value={form.max_bet_per_round}
                onChange={(e) => handleNumberChange('max_bet_per_round', e.target.value)}
                disabled={loading}
                placeholder="(optional)"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">RNG / Provably Fair</CardTitle>
          <CardDescription>Provably fair açılsın mı ve hangi RNG algoritması kullanılacak?</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Switch
              checked={!!form.provably_fair_enabled}
              onCheckedChange={(v) => handleChange('provably_fair_enabled', v)}
              disabled={loading}
            />
            <span className="text-xs text-muted-foreground">Provably fair enabled</span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>RNG Algorithm</Label>
              <Input
                value={form.rng_algorithm}
                onChange={(e) => handleChange('rng_algorithm', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Seed Rotation Interval (rounds)</Label>
              <Input
                type="number"
                value={form.seed_rotation_interval_rounds}
                onChange={(e) => handleNumberChange('seed_rotation_interval_rounds', e.target.value)}
                disabled={loading}
                placeholder="(optional)"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <div>
        <Label>Change Summary (optional)</Label>
        <Input
          value={form.summary}
          onChange={(e) => handleChange('summary', e.target.value)}
          placeholder="Max multi 500x, RTP 96, medium volatility."
          disabled={loading}
          className="mt-1"
        />
      </div>

      <Button onClick={handleSave} disabled={saving || loading}>
        {saving ? 'Saving...' : 'Save Crash Math'}
      </Button>
    </div>
  );
};

export default GameCrashMathTab;
