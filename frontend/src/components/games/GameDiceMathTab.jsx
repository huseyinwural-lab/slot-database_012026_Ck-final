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

const GameDiceMathTab = ({ game }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState('');

  const [form, setForm] = useState({
    range_min: 0.0,
    range_max: 99.99,
    step: 0.01,
    house_edge_percent: 1.0,
    min_payout_multiplier: 1.01,
    max_payout_multiplier: 990.0,
    allow_over: true,
    allow_under: true,
    min_target: 1.0,
    max_target: 98.0,
    round_duration_seconds: 5,
    bet_phase_seconds: 3,
    // Advanced limits (global)
    max_win_per_bet: '',
    max_loss_per_bet: '',
    max_session_loss: '',
    max_session_bets: '',
    enforcement_mode: 'log_only',
    country_overrides: {},
    provably_fair_enabled: true,
    rng_algorithm: 'sha256_chain',
    seed_rotation_interval_rounds: 20000,
    summary: '',
  });

  useEffect(() => {
    if (!game) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [cfgRes, presetRes] = await Promise.all([
          api.get(`/v1/games/${game.id}/config/dice-math`),
          api.get('/v1/game-config/presets', {
            params: { game_type: game.core_type, config_type: 'dice_math' },
          }),
        ]);

        const data = cfgRes.data;
        setForm((prev) => ({
          ...prev,
          ...data,
          max_win_per_bet: data.max_win_per_bet ?? '',
          max_loss_per_bet: data.max_loss_per_bet ?? '',
          max_session_loss: data.max_session_loss ?? '',
          max_session_bets: data.max_session_bets ?? '',
          enforcement_mode: data.enforcement_mode || 'log_only',
          country_overrides: data.country_overrides || {},
          summary: '',
        }));

        setPresets(presetRes.data?.presets || []);
      } catch (err) {
        console.error(err);
        const apiError = err?.response?.data;
        if (apiError?.error_code) {
          setError(apiError.message || 'Dice math config yüklenemedi.');
        } else {
          toast.error('Dice math config yüklenemedi.');
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
          summary: preset.values.summary || prev.summary,
        }));
      }
      await api.post(`/v1/game-config/presets/${selectedPreset}/apply`, {
        game_id: game.id,
        game_type: game.core_type,
        config_type: 'dice_math',
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
        range_min: Number(form.range_min),
        range_max: Number(form.range_max),
        step: Number(form.step),
        house_edge_percent: Number(form.house_edge_percent),
        min_payout_multiplier: Number(form.min_payout_multiplier),
        max_payout_multiplier: Number(form.max_payout_multiplier),
        allow_over: !!form.allow_over,
        allow_under: !!form.allow_under,
        min_target: Number(form.min_target),
        max_target: Number(form.max_target),
        round_duration_seconds: Number(form.round_duration_seconds),
        bet_phase_seconds: Number(form.bet_phase_seconds),
        max_win_per_bet:
          form.max_win_per_bet === '' || form.max_win_per_bet == null
            ? null
            : Number(form.max_win_per_bet),
        max_loss_per_bet:
          form.max_loss_per_bet === '' || form.max_loss_per_bet == null
            ? null
            : Number(form.max_loss_per_bet),
        max_session_loss:
          form.max_session_loss === '' || form.max_session_loss == null
            ? null
            : Number(form.max_session_loss),
        max_session_bets:
          form.max_session_bets === '' || form.max_session_bets == null
            ? null
            : Number(form.max_session_bets),
        enforcement_mode: form.enforcement_mode || 'log_only',
        country_overrides: form.country_overrides || {},
        provably_fair_enabled: !!form.provably_fair_enabled,
        rng_algorithm: form.rng_algorithm,
        seed_rotation_interval_rounds:
          form.seed_rotation_interval_rounds === '' ||
          form.seed_rotation_interval_rounds == null
            ? null
            : Number(form.seed_rotation_interval_rounds),
        summary: form.summary || undefined,
      };

      const res = await api.post(`/v1/games/${game.id}/config/dice-math`, payload);
      toast.success('Dice math config kaydedildi.');
      const updated = res.data;
      setForm((prev) => ({
        ...prev,
        ...updated,
        max_win_per_bet: updated.max_win_per_bet ?? '',
        max_loss_per_bet: updated.max_loss_per_bet ?? '',
        max_session_loss: updated.max_session_loss ?? '',
        max_session_bets: updated.max_session_bets ?? '',
        enforcement_mode: updated.enforcement_mode || 'log_only',
        country_overrides: updated.country_overrides || {},
        summary: '',
      }));
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      if (apiError?.message) {
        toast.error(apiError.message);
        setError(apiError.message);
      } else {
        toast.error('Dice math config kaydedilemedi.');
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
            Dice math için hazır profilleri uygula, ardından gerekirse manuel olarak düzenle.
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
          <CardTitle className="text-sm">Range &amp; Step</CardTitle>
          <CardDescription>Dice oyununun sayı aralığı ve step çözünürlüğü.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Range Min</Label>
              <Input
                type="number"
                value={form.range_min}
                onChange={(e) => handleNumberChange('range_min', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Range Max</Label>
              <Input
                type="number"
                value={form.range_max}
                onChange={(e) => handleNumberChange('range_max', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Step</Label>
              <Input
                type="number"
                value={form.step}
                onChange={(e) => handleNumberChange('step', e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">House Edge &amp; Payouts</CardTitle>
          <CardDescription>
            House edge yüzdesi ve minimum/maksimum payout multiplier sınırlarını ayarla.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>House Edge (%)</Label>
              <Input
                type="number"
                value={form.house_edge_percent}
                onChange={(e) => handleNumberChange('house_edge_percent', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Min Payout Multiplier</Label>
              <Input
                type="number"
                value={form.min_payout_multiplier}
                onChange={(e) => handleNumberChange('min_payout_multiplier', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Max Payout Multiplier</Label>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Advanced Limits (global)</CardTitle>
          <CardDescription>
            Tek bet ve session bazlı advanced limitler. Boş bırakırsan sınırsız kabul edilir.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Max Win per Bet</Label>
              <Input
                type="number"
                value={form.max_win_per_bet}
                onChange={(e) => handleNumberChange('max_win_per_bet', e.target.value)}
                disabled={loading}
                placeholder="(optional)"
              />
              <p className="text-[10px] text-muted-foreground mt-1">
                Tek elde kazanılabilecek maksimum tutar. Özellikle VIP masalarda risk departmanıyla uyumlu seç.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Max Loss per Bet</Label>
              <Input
                type="number"
                value={form.max_loss_per_bet}
                onChange={(e) => handleNumberChange('max_loss_per_bet', e.target.value)}
                disabled={loading}
                placeholder="(optional)"
              />
              <p className="text-[10px] text-muted-foreground mt-1">
                Tek elde kaybedilebilecek maksimum tutar. Responsible gaming limitleriyle uyumlu olmalı.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Max Session Loss</Label>
              <Input
                type="number"
                value={form.max_session_loss}
                onChange={(e) => handleNumberChange('max_session_loss', e.target.value)}
                disabled={loading}
                placeholder="(optional)"
              />
              <p className="text-[10px] text-muted-foreground mt-1">
                Bir oyuncunun tek session&#39;da kaybedebileceği toplam maksimum tutar.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Max Session Bets</Label>
              <Input
                type="number"
                value={form.max_session_bets}
                onChange={(e) => handleNumberChange('max_session_bets', e.target.value)}
                disabled={loading}
                placeholder="(optional)"
              />
              <p className="text-[10px] text-muted-foreground mt-1">
                Bir session&#39;da atılabilecek maksimum bet sayısı. Yüksek velocity&#39;yi sınırlamak için kullanılabilir.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Advanced Limits Enforcement</CardTitle>
          <CardDescription>
            Limit aşımlarında sistemin nasıl davranacağını seç.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2 max-w-xs">
            <Label>Enforcement Mode</Label>
            <Select
              value={form.enforcement_mode}
              onValueChange={(v) => handleChange('enforcement_mode', v)}
              disabled={loading}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="log_only">Log only</SelectItem>
                <SelectItem value="hard_block">Hard block</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <ul className="list-disc list-inside text-[10px] text-muted-foreground space-y-1">
            <li><strong>log_only</strong>: Limit aşımlarını sadece loglar, bet akışını kesmez.</li>
            <li><strong>hard_block</strong>: Limit aşıldığında bet/round engellenir ve loglanır.</li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Country Overrides</CardTitle>
          <CardDescription>
            Ülke bazlı daha sıkı / gevşek Dice limitleri tanımla (ISO 3166-1 alpha-2 kodlarıyla).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Alert variant="default">
            <AlertDescription className="text-[10px]">
              Örnek: {`{"TR": { "max_session_loss": 1000, "max_win_per_bet": 200 }}`}
            </AlertDescription>
          </Alert>
          <div className="space-y-2">
            <Label>Country Overrides (JSON)</Label>
            <textarea
              className="w-full border rounded-md p-2 text-xs font-mono min-h-[120px] bg-background"
              disabled={loading}
              value={JSON.stringify(form.country_overrides || {}, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = e.target.value.trim() ? JSON.parse(e.target.value) : {};
                  setForm((prev) => ({ ...prev, country_overrides: parsed }));
                  setError(null);
                } catch (parseErr) {
                  setError('Country overrides JSON formatı geçersiz.');
                }
              }}
            />
          </div>
        </CardContent>
      </Card>

              <Input
                type="number"
                value={form.max_payout_multiplier}
                onChange={(e) => handleNumberChange('max_payout_multiplier', e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
          <p className="text-[10px] text-muted-foreground mt-2">
            Gerçek payout hesaplaması engine tarafından yapılacak; burada sadece sınırlar belirlenir.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Target Rules</CardTitle>
          <CardDescription>Over/Under modları ve izin verilen hedef aralığı.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch
                checked={!!form.allow_over}
                onCheckedChange={(v) => handleChange('allow_over', v)}
                disabled={loading}
              />
              <span className="text-xs text-muted-foreground">Allow Over</span>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={!!form.allow_under}
                onCheckedChange={(v) => handleChange('allow_under', v)}
                disabled={loading}
              />
              <span className="text-xs text-muted-foreground">Allow Under</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Min Target</Label>
              <Input
                type="number"
                value={form.min_target}
                onChange={(e) => handleNumberChange('min_target', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Max Target</Label>
              <Input
                type="number"
                value={form.max_target}
                onChange={(e) => handleNumberChange('max_target', e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Timing &amp; Fairness</CardTitle>
          <CardDescription>Round süresi, bet phase ve provably fair parametreleri.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
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
          </div>
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
          placeholder="Standard 1% house edge dice config."
          disabled={loading}
          className="mt-1"
        />
      </div>

      <Button onClick={handleSave} disabled={saving || loading}>
        {saving ? 'Saving...' : 'Save Dice Math'}
      </Button>
    </div>
  );
};

export default GameDiceMathTab;
