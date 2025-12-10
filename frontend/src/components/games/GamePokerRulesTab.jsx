import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import api from '../../services/api';

const VARIANTS = [
  { value: 'texas_holdem', label: "Texas Hold'em" },
  { value: 'omaha', label: 'Omaha' },
  { value: 'omaha_hi_lo', label: 'Omaha Hi-Lo' },
  { value: '3card_poker', label: '3-Card Poker' },
  { value: 'caribbean_stud', label: 'Caribbean Stud' },
];

const LIMIT_TYPES = [
  { value: 'no_limit', label: 'No Limit' },
  { value: 'pot_limit', label: 'Pot Limit' },
  { value: 'fixed_limit', label: 'Fixed Limit' },
];

const RAKE_TYPES = [
  { value: 'none', label: 'None' },
  { value: 'percentage', label: 'Percentage' },
  { value: 'time', label: 'Time (yakında)' },
];

const GamePokerRulesTab = ({ game }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    variant: 'texas_holdem',
    limit_type: 'no_limit',
    min_players: 2,
    max_players: 6,
    min_buyin_bb: 40,
    max_buyin_bb: 100,
    rake_type: 'percentage',
    rake_percent: 5.0,
    rake_cap_currency: 10.0,
    rake_applies_from_pot: 1.0,
    use_antes: false,
    ante_bb: null,
    small_blind_bb: 0.5,
    big_blind_bb: 1.0,
    allow_straddle: true,
    run_it_twice_allowed: false,
    min_players_to_start: 2,
    summary: '',
  });

  useEffect(() => {
    if (!game) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get(`/v1/games/${game.id}/config/poker-rules`);
        const rules = res.data?.rules;
        if (rules) {
          setForm((prev) => ({
            ...prev,
            ...rules,
            summary: '',
          }));
        }
      } catch (err) {
        console.error(err);
        const apiError = err?.response?.data;
        if (apiError?.error_code === 'POKER_RULES_NOT_AVAILABLE_FOR_GAME') {
          setError(apiError.message || 'Poker rules not available for this game.');
        } else {
          toast.error('Poker rules yüklenemedi');
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
        variant: form.variant,
        limit_type: form.limit_type,
        min_players: Number(form.min_players),
        max_players: Number(form.max_players),
        min_buyin_bb: Number(form.min_buyin_bb),
        max_buyin_bb: Number(form.max_buyin_bb),
        rake_type: form.rake_type,
        rake_percent:
          form.rake_type === 'percentage' && form.rake_percent !== ''
            ? Number(form.rake_percent)
            : null,
        rake_cap_currency:
          form.rake_type === 'percentage' && form.rake_cap_currency !== ''
            ? Number(form.rake_cap_currency)
            : null,
        rake_applies_from_pot:
          form.rake_type === 'percentage' && form.rake_applies_from_pot !== ''
            ? Number(form.rake_applies_from_pot)
            : null,
        use_antes: !!form.use_antes,
        ante_bb:
          form.use_antes && form.ante_bb !== '' && form.ante_bb != null ? Number(form.ante_bb) : null,
        small_blind_bb: Number(form.small_blind_bb),
        big_blind_bb: Number(form.big_blind_bb),
        allow_straddle: !!form.allow_straddle,
        run_it_twice_allowed: !!form.run_it_twice_allowed,
        min_players_to_start: Number(form.min_players_to_start),
        summary: form.summary || undefined,
      };

      const res = await api.post(`/v1/games/${game.id}/config/poker-rules`, payload);
      toast.success('Poker kuralları kaydedildi.');
      const updated = res.data;
      setForm((prev) => ({
        ...prev,
        ...updated,
        summary: '',
      }));
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      if (apiError?.message) {
        toast.error(apiError.message);
      } else {
        toast.error('Poker kuralları kaydedilemedi.');
      }
    } finally {
      setSaving(false);
    }
  };

  const rakeTypeDisabled = form.rake_type === 'time';

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Game Basics</CardTitle>
          <CardDescription>Poker varyantı, limit tipi ve masa kapasitesi.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Variant</Label>
              <Select
                value={form.variant}
                onValueChange={(v) => handleChange('variant', v)}
                disabled={loading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VARIANTS.map((v) => (
                    <SelectItem key={v.value} value={v.value}>
                      {v.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Limit Type</Label>
              <Select
                value={form.limit_type}
                onValueChange={(v) => handleChange('limit_type', v)}
                disabled={loading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LIMIT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Players (min / max)</Label>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  value={form.min_players}
                  onChange={(e) => handleNumberChange('min_players', e.target.value)}
                  disabled={loading}
                />
                <span className="text-xs text-muted-foreground">to</span>
                <Input
                  type="number"
                  value={form.max_players}
                  onChange={(e) => handleNumberChange('max_players', e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Buy-in &amp; Blinds</CardTitle>
          <CardDescription>
            BB değerleri, masanın seçilmiş ana bet para birimine göre hesaplanır.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Min Buy-in (BB)</Label>
              <Input
                type="number"
                value={form.min_buyin_bb}
                onChange={(e) => handleNumberChange('min_buyin_bb', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Max Buy-in (BB)</Label>
              <Input
                type="number"
                value={form.max_buyin_bb}
                onChange={(e) => handleNumberChange('max_buyin_bb', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Small Blind (BB)</Label>
              <Input
                type="number"
                value={form.small_blind_bb}
                onChange={(e) => handleNumberChange('small_blind_bb', e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Big Blind (BB)</Label>
              <Input
                type="number"
                value={form.big_blind_bb}
                onChange={(e) => handleNumberChange('big_blind_bb', e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Rake</CardTitle>
          <CardDescription>Rake tipi ve yüzde/cap tanımı.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="space-y-2">
              <Label>Rake Type</Label>
              <Select
                value={form.rake_type}
                onValueChange={(v) => handleChange('rake_type', v)}
                disabled={loading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {RAKE_TYPES.map((r) => (
                    <SelectItem key={r.value} value={r.value} disabled={r.value === 'time'}>
                      {r.label}
                      {r.value === 'time' && (
                        <Badge variant="outline" className="ml-2 text-[10px]">
                          Yakında
                        </Badge>
                      )}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Rake %</Label>
              <Input
                type="number"
                value={form.rake_percent ?? ''}
                onChange={(e) => handleNumberChange('rake_percent', e.target.value)}
                disabled={loading || rakeTypeDisabled || form.rake_type !== 'percentage'}
              />
            </div>
            <div className="space-y-2">
              <Label>Rake Cap (Currency)</Label>
              <Input
                type="number"
                value={form.rake_cap_currency ?? ''}
                onChange={(e) => handleNumberChange('rake_cap_currency', e.target.value)}
                disabled={loading || rakeTypeDisabled || form.rake_type !== 'percentage'}
              />
            </div>
            <div className="space-y-2">
              <Label>Rake From Pot (BB)</Label>
              <Input
                type="number"
                value={form.rake_applies_from_pot ?? ''}
                onChange={(e) => handleNumberChange('rake_applies_from_pot', e.target.value)}
                disabled={loading || rakeTypeDisabled || form.rake_type !== 'percentage'}
              />
            </div>
          </div>
          {form.rake_type === 'time' && (
            <p className="text-[10px] text-muted-foreground">
              Time-based rake konfigürasyonu bir sonraki iterasyonda eklenecektir.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Other Rules</CardTitle>
          <CardDescription>Ante, straddle ve run-it-twice kuralları.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Use antes?</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.use_antes}
                  onCheckedChange={(v) => handleChange('use_antes', v)}
                  disabled={loading}
                />
                <span className="text-xs text-muted-foreground">Enable antes for this table</span>
              </div>
              <Input
                type="number"
                value={form.ante_bb ?? ''}
                onChange={(e) => handleNumberChange('ante_bb', e.target.value)}
                disabled={loading || !form.use_antes}
                placeholder="Ante BB"
                className="mt-2"
              />
            </div>
            <div className="space-y-2">
              <Label>Allow straddle?</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.allow_straddle}
                  onCheckedChange={(v) => handleChange('allow_straddle', v)}
                  disabled={loading}
                />
                <span className="text-xs text-muted-foreground">Straddle opsiyonuna izin ver</span>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Run it twice allowed?</Label>
              <div className="flex items-center gap-2">
                <Switch
                  checked={!!form.run_it_twice_allowed}
                  onCheckedChange={(v) => handleChange('run_it_twice_allowed', v)}
                  disabled={loading}
                />
                <span className="text-xs text-muted-foreground">Run-it-twice masada kullanılabilir</span>
              </div>
            </div>
          </div>

          <div className="space-y-2 max-w-xs">
            <Label>Min players to start</Label>
            <Input
              type="number"
              value={form.min_players_to_start}
              onChange={(e) => handleNumberChange('min_players_to_start', e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label>Change summary (optional)</Label>
            <Input
              value={form.summary}
              onChange={(e) => handleChange('summary', e.target.value)}
              placeholder="6-max NLH rake 5% cap 8 EUR."
              disabled={loading}
            />
          </div>

          <Button onClick={handleSave} disabled={saving || loading}>
            {saving ? 'Saving...' : 'Save Poker Rules'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default GamePokerRulesTab;
