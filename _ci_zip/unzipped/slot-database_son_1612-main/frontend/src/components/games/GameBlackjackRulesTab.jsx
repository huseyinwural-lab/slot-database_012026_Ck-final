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
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

const GameBlackjackRulesTab = ({ game }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState('');

  const [form, setForm] = useState({
    // Core rules defaults (eşleşen default template ile uyumlu)
    deck_count: 6,
    dealer_hits_soft_17: false,
    blackjack_payout: 1.5,
    double_allowed: true,
    double_after_split_allowed: true,
    split_max_hands: 4,
    resplit_aces_allowed: false,
    surrender_allowed: true,
    insurance_allowed: true,
    min_bet: 5.0,
    max_bet: 500.0,
    side_bets_enabled: false,
    side_bets: [],
    // Branding
    table_label: '',
    theme: '',
    avatar_url: '',
    banner_url: '',
    // Behavior / safety
    auto_seat_enabled: false,
    sitout_time_limit_seconds: 120,
    disconnect_wait_seconds: 30,
    max_same_country_seats: '',
    block_vpn_flagged_players: false,
    session_max_duration_minutes: '',
    max_daily_buyin_limit: '',
    // Local only
    summary: '',
  });

  const [sideBetsUi, setSideBetsUi] = useState([]); // { code, min_bet, max_bet, payout_table_json }

  useEffect(() => {
    if (!game) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [rulesRes, presetRes] = await Promise.all([
          api.get(`/v1/games/${game.id}/config/blackjack-rules`),
          api.get('/v1/game-config/presets', {
            params: { game_type: game.core_type || 'TABLE_BLACKJACK', config_type: 'blackjack_rules' },
          }),
        ]);

        const rules = rulesRes.data?.rules;
        if (rules) {
          setForm((prev) => ({
            ...prev,
            ...rules,
            max_same_country_seats: rules.max_same_country_seats ?? '',
            session_max_duration_minutes: rules.session_max_duration_minutes ?? '',
            max_daily_buyin_limit: rules.max_daily_buyin_limit ?? '',
            summary: '',
          }));

          const sb = rules.side_bets || [];
          setSideBetsUi(
            sb.map((item) => ({
              code: item.code || '',
              min_bet: item.min_bet ?? '',
              max_bet: item.max_bet ?? '',
              payout_table_json:
                item.payout_table && typeof item.payout_table === 'object'
                  ? JSON.stringify(item.payout_table)
                  : '',
            })),
          );
        }

        setPresets(presetRes.data?.presets || []);
      } catch (err) {
        console.error(err);
        const apiError = err?.response?.data;
        if (apiError?.error_code === 'BLACKJACK_RULES_NOT_AVAILABLE_FOR_GAME') {
          setError(apiError.message || 'Blackjack rules not available for this game.');
        } else {
          toast.error('Blackjack rules yüklenemedi');
        }
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [game?.id, game?.core_type, game]);

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

  const handleSideBetChange = (index, field, value) => {
    setSideBetsUi((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const addSideBetRow = () => {
    setSideBetsUi((prev) => [...prev, { code: '', min_bet: '', max_bet: '', payout_table_json: '' }]);
  };

  const removeSideBetRow = (index) => {
    setSideBetsUi((prev) => prev.filter((_, i) => i !== index));
  };

  const handleApplyPreset = async () => {
    if (!selectedPreset || !game) return;
    try {
      const res = await api.get(`/v1/game-config/presets/${selectedPreset}`);
      const preset = res.data;
      if (preset?.values) {
        const v = preset.values;
        setForm((prev) => ({
          ...prev,
          deck_count: v.deck_count ?? prev.deck_count,
          dealer_hits_soft_17: v.dealer_hits_soft_17 ?? prev.dealer_hits_soft_17,
          blackjack_payout: v.blackjack_payout ?? prev.blackjack_payout,
          double_allowed: v.double_allowed ?? prev.double_allowed,
          double_after_split_allowed:
            v.double_after_split_allowed ?? prev.double_after_split_allowed,
          split_max_hands: v.split_max_hands ?? prev.split_max_hands,
          resplit_aces_allowed: v.resplit_aces_allowed ?? prev.resplit_aces_allowed,
          surrender_allowed: v.surrender_allowed ?? prev.surrender_allowed,
          insurance_allowed: v.insurance_allowed ?? prev.insurance_allowed,
          min_bet: v.min_bet ?? prev.min_bet,
          max_bet: v.max_bet ?? prev.max_bet,
          side_bets_enabled: v.side_bets_enabled ?? prev.side_bets_enabled,
          table_label: v.table_label ?? prev.table_label,
          theme: v.theme ?? prev.theme,
          avatar_url: v.avatar_url ?? prev.avatar_url,
          banner_url: v.banner_url ?? prev.banner_url,
          auto_seat_enabled: v.auto_seat_enabled ?? prev.auto_seat_enabled,
          sitout_time_limit_seconds:
            v.sitout_time_limit_seconds ?? prev.sitout_time_limit_seconds,
          disconnect_wait_seconds:
            v.disconnect_wait_seconds ?? prev.disconnect_wait_seconds,
          max_same_country_seats: v.max_same_country_seats ?? prev.max_same_country_seats,
          block_vpn_flagged_players:
            v.block_vpn_flagged_players ?? prev.block_vpn_flagged_players,
          session_max_duration_minutes:
            v.session_max_duration_minutes ?? prev.session_max_duration_minutes,
          max_daily_buyin_limit: v.max_daily_buyin_limit ?? prev.max_daily_buyin_limit,
          summary: v.summary || prev.summary,
        }));

        const sb = v.side_bets || [];
        if (Array.isArray(sb)) {
          setSideBetsUi(
            sb.map((item) => ({
              code: item.code || '',
              min_bet: item.min_bet ?? '',
              max_bet: item.max_bet ?? '',
              payout_table_json:
                item.payout_table && typeof item.payout_table === 'object'
                  ? JSON.stringify(item.payout_table)
                  : '',
            })),
          );
        }
      }

      await api.post(`/v1/game-config/presets/${selectedPreset}/apply`, {
        game_id: game.id,
        game_type: game.core_type || 'TABLE_BLACKJACK',
        config_type: 'blackjack_rules',
      });
      toast.success('Preset uygulandı. Değerler forma yansıtıldı.');
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      toast.error(apiError?.message || 'Preset uygulanamadı.');
    }
  };

  const buildSideBetsPayload = () => {
    if (!form.side_bets_enabled) return [];
    const arr = [];
    for (const row of sideBetsUi) {
      if (!row.code) continue;
      const minStr = row.min_bet;
      const maxStr = row.max_bet;
      if (minStr === '' || maxStr === '') {
        toast.error('Side bet min/max bet boş olamaz.');
        return null;
      }
      const minVal = Number(minStr);
      const maxVal = Number(maxStr);
      if (Number.isNaN(minVal) || Number.isNaN(maxVal)) {
        toast.error('Side bet min/max bet sayı olmalıdır.');
        return null;
      }
      let payoutTable = undefined;
      if (row.payout_table_json && row.payout_table_json.trim().length > 0) {
        try {
          payoutTable = JSON.parse(row.payout_table_json);
        } catch (e) {
          console.error(e);
          toast.error('Side bet payout_table JSON geçersiz.');
          return null;
        }
      }
      arr.push({
        code: row.code,
        min_bet: minVal,
        max_bet: maxVal,
        ...(payoutTable ? { payout_table: payoutTable } : {}),
      });
    }
    return arr;
  };

  const handleSave = async () => {
    if (!game) return;

    const sideBetsPayload = buildSideBetsPayload();
    if (sideBetsPayload === null) return;

    setSaving(true);
    setError(null);
    try {
      const payload = {
        deck_count: Number(form.deck_count),
        dealer_hits_soft_17: !!form.dealer_hits_soft_17,
        blackjack_payout: Number(form.blackjack_payout),
        double_allowed: !!form.double_allowed,
        double_after_split_allowed: !!form.double_after_split_allowed,
        split_max_hands: Number(form.split_max_hands),
        resplit_aces_allowed: !!form.resplit_aces_allowed,
        surrender_allowed: !!form.surrender_allowed,
        insurance_allowed: !!form.insurance_allowed,
        min_bet: Number(form.min_bet),
        max_bet: Number(form.max_bet),
        side_bets_enabled: !!form.side_bets_enabled,
        side_bets: sideBetsPayload,
        table_label: form.table_label || null,
        theme: form.theme || null,
        avatar_url: form.avatar_url || null,
        banner_url: form.banner_url || null,
        auto_seat_enabled: !!form.auto_seat_enabled,
        sitout_time_limit_seconds:
          form.sitout_time_limit_seconds === '' || form.sitout_time_limit_seconds == null
            ? null
            : Number(form.sitout_time_limit_seconds),
        disconnect_wait_seconds:
          form.disconnect_wait_seconds === '' || form.disconnect_wait_seconds == null
            ? null
            : Number(form.disconnect_wait_seconds),
        max_same_country_seats:
          form.max_same_country_seats === '' || form.max_same_country_seats == null
            ? null
            : Number(form.max_same_country_seats),
        block_vpn_flagged_players: !!form.block_vpn_flagged_players,
        session_max_duration_minutes:
          form.session_max_duration_minutes === '' || form.session_max_duration_minutes == null
            ? null
            : Number(form.session_max_duration_minutes),
        max_daily_buyin_limit:
          form.max_daily_buyin_limit === '' || form.max_daily_buyin_limit == null
            ? null
            : Number(form.max_daily_buyin_limit),
        summary: form.summary || undefined,
      };

      const res = await api.post(`/v1/games/${game.id}/config/blackjack-rules`, payload);
      toast.success('Blackjack kuralları kaydedildi.');
      const updated = res.data;
      setForm((prev) => ({
        ...prev,
        ...updated,
        max_same_country_seats: updated.max_same_country_seats ?? '',
        session_max_duration_minutes: updated.session_max_duration_minutes ?? '',
        max_daily_buyin_limit: updated.max_daily_buyin_limit ?? '',
        summary: '',
      }));

      const sbUpdated = updated.side_bets || [];
      setSideBetsUi(
        sbUpdated.map((item) => ({
          code: item.code || '',
          min_bet: item.min_bet ?? '',
          max_bet: item.max_bet ?? '',
          payout_table_json:
            item.payout_table && typeof item.payout_table === 'object'
              ? JSON.stringify(item.payout_table)
              : '',
        })),
      );
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      if (apiError?.message) {
        toast.error(apiError.message);
      } else {
        toast.error('Blackjack kuralları kaydedilemedi.');
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
            Blackjack kuralları ve side bet yapısı için hazır preset&apos;leri uygula, ardından manuel
            olarak düzenleyebilirsin.
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
                <SelectValue
                  placeholder={presets.length ? 'Seçiniz' : 'Preset bulunamadı'}
                />
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

      {/* Core Rules */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Core Rules</CardTitle>
          <CardDescription>Desteler, payout ve temel masa kuralları.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Deck count</Label>
              <Input
                type="number"
                value={form.deck_count}
                onChange={(e) => handleNumberChange('deck_count', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Blackjack payout (ör. 1.5 = 3:2)</Label>
              <Input
                type="number"
                step="0.1"
                value={form.blackjack_payout}
                onChange={(e) => handleNumberChange('blackjack_payout', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Dealer hits soft 17? (H17)</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.dealer_hits_soft_17}
                  onCheckedChange={(v) => handleChange('dealer_hits_soft_17', v)}
                  disabled={loading}
                />
                <span className="text-xs text-muted-foreground">
                  Kapalı ise S17 (dealer stands on soft 17)
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Double allowed</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.double_allowed}
                  onCheckedChange={(v) => handleChange('double_allowed', v)}
                  disabled={loading}
                />
                <span className="text-xs text-muted-foreground">Double on any 2 cards</span>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Double after split allowed</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.double_after_split_allowed}
                  onCheckedChange={(v) => handleChange('double_after_split_allowed', v)}
                  disabled={loading}
                />
                <span className="text-xs text-muted-foreground">DAS</span>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Split max hands</Label>
              <Input
                type="number"
                value={form.split_max_hands}
                onChange={(e) => handleNumberChange('split_max_hands', e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Resplit aces allowed</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.resplit_aces_allowed}
                  onCheckedChange={(v) => handleChange('resplit_aces_allowed', v)}
                  disabled={loading}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Surrender allowed</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.surrender_allowed}
                  onCheckedChange={(v) => handleChange('surrender_allowed', v)}
                  disabled={loading}
                />
                <span className="text-xs text-muted-foreground">Late surrender</span>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Insurance allowed</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.insurance_allowed}
                  onCheckedChange={(v) => handleChange('insurance_allowed', v)}
                  disabled={loading}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Limits */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Limits</CardTitle>
          <CardDescription>Masa minimum / maksimum bet limitleri.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Min bet</Label>
              <Input
                type="number"
                value={form.min_bet}
                onChange={(e) => handleNumberChange('min_bet', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Max bet</Label>
              <Input
                type="number"
                value={form.max_bet}
                onChange={(e) => handleNumberChange('max_bet', e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Side Bets */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Side Bets</CardTitle>
          <CardDescription>Popüler side bet&apos;leri tanımla veya preset&apos;lerden başla.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Switch
              checked={!!form.side_bets_enabled}
              onCheckedChange={(v) => handleChange('side_bets_enabled', v)}
              disabled={loading}
            />
            <span className="text-xs text-muted-foreground">Side bets enabled</span>
          </div>

          {form.side_bets_enabled && (
            <div className="space-y-3">
              {sideBetsUi.map((sb, index) => (
                <div
                  key={index}
                  className="border rounded-md p-3 flex flex-col gap-2 bg-muted/40"
                >
                  <div className="flex gap-2">
                    <div className="flex-1 space-y-1">
                      <Label>Code</Label>
                      <Input
                        value={sb.code}
                        onChange={(e) => handleSideBetChange(index, 'code', e.target.value)}
                        disabled={loading}
                        placeholder="perfect_pairs"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Min bet</Label>
                      <Input
                        type="number"
                        value={sb.min_bet}
                        onChange={(e) => handleSideBetChange(index, 'min_bet', e.target.value)}
                        disabled={loading}
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Max bet</Label>
                      <Input
                        type="number"
                        value={sb.max_bet}
                        onChange={(e) => handleSideBetChange(index, 'max_bet', e.target.value)}
                        disabled={loading}
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <Label>Payout table (JSON, opsiyonel)</Label>
                    <Input
                      value={sb.payout_table_json}
                      onChange={(e) =>
                        handleSideBetChange(index, 'payout_table_json', e.target.value)
                      }
                      placeholder='{"mixed": 5, "colored": 10, "perfect": 25}'
                      disabled={loading}
                    />
                  </div>
                  <div className="flex justify-end">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => removeSideBetRow(index)}
                      disabled={loading}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              ))}

              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addSideBetRow}
                disabled={loading}
              >
                Add side bet
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Advanced Settings */}
      <Collapsible>
        <CollapsibleTrigger asChild>
          <Button variant="outline" className="w-full justify-between text-sm">
            <span>Advanced Table Settings</span>
            <span className="text-xs text-muted-foreground">Branding, davranış ve anti-collusion</span>
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-4 space-y-4">
          {/* Branding */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Branding</CardTitle>
              <CardDescription>VIP ve marka uyumlu blackjack masaları için.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Table Label</Label>
                <Input
                  value={form.table_label || ''}
                  onChange={(e) => handleChange('table_label', e.target.value)}
                  disabled={loading}
                  placeholder="VIP Emerald BJ Table"
                />
              </div>
              <div className="space-y-2">
                <Label>Theme</Label>
                <Input
                  value={form.theme || ''}
                  onChange={(e) => handleChange('theme', e.target.value)}
                  disabled={loading}
                  placeholder="bj_dark_luxe"
                />
              </div>
              <div className="space-y-2">
                <Label>Avatar URL</Label>
                <Input
                  value={form.avatar_url || ''}
                  onChange={(e) => handleChange('avatar_url', e.target.value)}
                  disabled={loading}
                />
              </div>
              <div className="space-y-2">
                <Label>Banner URL</Label>
                <Input
                  value={form.banner_url || ''}
                  onChange={(e) => handleChange('banner_url', e.target.value)}
                  disabled={loading}
                />
              </div>
            </CardContent>
          </Card>

          {/* Behavior */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Behavior</CardTitle>
              <CardDescription>Masa oturum ve disconnect davranışları.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={!!form.auto_seat_enabled}
                    onCheckedChange={(v) => handleChange('auto_seat_enabled', v)}
                    disabled={loading}
                  />
                  <span className="text-xs text-muted-foreground">Auto seat enabled</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Sit-out Timeout (sec)</Label>
                  <Input
                    type="number"
                    value={form.sitout_time_limit_seconds ?? ''}
                    onChange={(e) =>
                      handleNumberChange('sitout_time_limit_seconds', e.target.value)
                    }
                    disabled={loading}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Disconnect Wait (sec)</Label>
                  <Input
                    type="number"
                    value={form.disconnect_wait_seconds ?? ''}
                    onChange={(e) =>
                      handleNumberChange('disconnect_wait_seconds', e.target.value)
                    }
                    disabled={loading}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Anti-Collusion & Safety */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Anti-Collusion &amp; Safety</CardTitle>
              <CardDescription>Regülasyon ve güvenlik için limitler.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={!!form.block_vpn_flagged_players}
                    onCheckedChange={(v) => handleChange('block_vpn_flagged_players', v)}
                    disabled={loading}
                  />
                  <span className="text-xs text-muted-foreground">Block VPN-flagged players</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Max same-country seats</Label>
                  <Input
                    type="number"
                    value={form.max_same_country_seats}
                    onChange={(e) =>
                      handleNumberChange('max_same_country_seats', e.target.value)
                    }
                    disabled={loading}
                    placeholder="örn. 2"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Session max duration (minutes)</Label>
                  <Input
                    type="number"
                    value={form.session_max_duration_minutes}
                    onChange={(e) =>
                      handleNumberChange('session_max_duration_minutes', e.target.value)
                    }
                    disabled={loading}
                    placeholder="örn. 240"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Max daily buy-in limit (currency)</Label>
                  <Input
                    type="number"
                    value={form.max_daily_buyin_limit}
                    onChange={(e) =>
                      handleNumberChange('max_daily_buyin_limit', e.target.value)
                    }
                    disabled={loading}
                    placeholder="örn. 5000"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>

      {/* Change summary + Save */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Change summary</CardTitle>
          <CardDescription>Bu değişiklik için kısa bir açıklama yazabilirsin.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <Label>Summary (optional)</Label>
          <Input
            value={form.summary}
            onChange={(e) => handleChange('summary', e.target.value)}
            disabled={loading}
            placeholder="VIP Vegas blackjack masası ayarı."
          />
          <Button onClick={handleSave} disabled={saving || loading} className="mt-2">
            {saving ? 'Saving...' : 'Save Blackjack Rules'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default GameBlackjackRulesTab;
