import React, { useEffect, useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Activity } from 'lucide-react';
import api from '../../services/api';
import GamePaytableTab from './GamePaytableTab';
import { Alert, AlertDescription } from '@/components/ui/alert';

import GameReelStripsTab from './GameReelStripsTab';
import GameAssetsTab from './GameAssetsTab';
import GamePokerRulesTab from './GamePokerRulesTab';
import GameCrashMathTab from './GameCrashMathTab';
import GameDiceMathTab from './GameDiceMathTab';

const defaultVisibility = {
  countries: [],
  segments: [],
  vip_min_level: 1,
};

// core_type bazlı görünür tab şeması
// Burada ana türler için SLOT / TABLE_POKER / CRASH / DICE / TABLE_BLACKJACK kullanıyoruz.
// REEL_LINES / WAYS / MEGAWAYS vb. engine tipleri SLOT ile aynı şemayı kullanacak.
const TAB_SCHEMA = {
  SLOT: ['general', 'rtp', 'bets', 'features', 'paytable', 'reels', 'assets', 'logs'],
  REEL_LINES: ['general', 'rtp', 'bets', 'features', 'paytable', 'reels', 'assets', 'logs'],
  WAYS: ['general', 'rtp', 'bets', 'features', 'paytable', 'reels', 'assets', 'logs'],
  MEGAWAYS: ['general', 'rtp', 'bets', 'features', 'paytable', 'reels', 'assets', 'logs'],
  TABLE_POKER: ['general', 'poker_rules', 'assets', 'logs'],
  CRASH: ['general', 'crash_math', 'bets', 'assets', 'logs'],
  DICE: ['general', 'dice_math', 'bets', 'assets', 'logs'],
  TABLE_BLACKJACK: ['general', 'blackjack_rules', 'assets', 'logs'],
};

const GameConfigPanel = ({ game, onClose, onSaved }) => {
  const [activeTab, setActiveTab] = useState('general');
  const [loading, setLoading] = useState(false);

  const [general, setGeneral] = useState({
    name: game?.name || '',
    provider: game?.provider || '',
    category: game?.category || 'slot',
    default_language: 'en',
    visibility_rules: defaultVisibility,
    lobby_sort_order: game?.sort_order || 0,
    tags: game?.tags || [],
    status: 'active',
  });

  const [rtpConfig, setRtpConfig] = useState({ profiles: [], default_profile_id: null });
  const [newRtp, setNewRtp] = useState({ code: '', rtp_value: 96.0, is_default: false });

  const [bets, setBets] = useState({
    min_bet: 0.1,
    max_bet: 100,
    step: 0.1,
    presets: [0.2, 0.5, 1, 2, 5, 10],
    country_overrides: [],
  });

  const [features, setFeatures] = useState({ bonus_buy: false, turbo_spin: false, autoplay: true });
  const [logs, setLogs] = useState([]);
  const [paytable, setPaytable] = useState({ current: null, history: [] });

  // core_type bazı eski oyunlarda boş olabiliyor; category'den türeterek normalize ediyoruz.
  const resolvedCoreType = React.useMemo(() => {
    if (!game) return undefined;
    if (game.core_type) return game.core_type;

    const cat = (game.category || '').toLowerCase();
    if (cat === 'slot' || cat === 'slots') return 'SLOT';
    if (cat === 'crash') return 'CRASH';
    if (cat === 'dice') return 'DICE';
    if (cat.includes('poker')) return 'TABLE_POKER';
    if (cat.includes('blackjack')) return 'TABLE_BLACKJACK';
    return undefined;
  }, [game]);

  const visibleTabs = TAB_SCHEMA[resolvedCoreType] || [];

  const [rtpPresets, setRtpPresets] = useState([]);
  const [selectedRtpPreset, setSelectedRtpPreset] = useState('');

  const [betsPresets, setBetsPresets] = useState([]);
  const [selectedBetsPreset, setSelectedBetsPreset] = useState('');

  useEffect(() => {
    if (!game) return;

    const loadAll = async () => {
      try {
        // General
        const generalRes = await api.get(`/v1/games/${game.id}/config/general`);
        setGeneral(generalRes.data);

        // RTP + RTP presets (slot türü için)
        if (visibleTabs.includes('rtp')) {
          const [rtpRes, presetRes] = await Promise.all([
            api.get(`/v1/games/${game.id}/config/rtp`),
            api.get('/v1/game-config/presets', {
              params: { game_type: resolvedCoreType || 'SLOT', config_type: 'rtp' },
            }),
          ]);
          setRtpConfig(rtpRes.data);
          setRtpPresets(presetRes.data?.presets || []);
        }

        // Bets + Bets presets (slot/crash/dice türleri için)
        if (visibleTabs.includes('bets')) {
          const [betRes, betPresetRes] = await Promise.all([
            api.get(`/v1/games/${game.id}/config/bets`),
            api.get('/v1/game-config/presets', {
              params: { game_type: resolvedCoreType || 'SLOT', config_type: 'bets' },
            }),
          ]);
          if (betRes.data?.config) setBets(betRes.data.config);
          setBetsPresets(betPresetRes.data?.presets || []);
        }

        // Features
        if (visibleTabs.includes('features')) {
          const featRes = await api.get(`/v1/games/${game.id}/config/features`);
          setFeatures(featRes.data.features || {});
        }

        // Paytable
        if (visibleTabs.includes('paytable')) {
          const payRes = await api.get(`/v1/games/${game.id}/config/paytable`);
          setPaytable(payRes.data);
        }

        // Logs
        if (visibleTabs.includes('logs')) {
          const logsRes = await api.get(`/v1/games/${game.id}/config/logs?limit=50`);
          setLogs(logsRes.data.items || []);
        }
      } catch (err) {
        console.error(err);
        toast.error('Failed to load game config');
      }
    };

    loadAll();
  }, [game, visibleTabs, resolvedCoreType]);

  const reloadPaytable = async () => {
    if (!game) return;
    try {
      const payRes = await api.get(`/v1/games/${game.id}/config/paytable`);
      setPaytable(payRes.data);
    } catch (err) {
      console.error(err);
      toast.error('Failed to reload paytable');
    }
  };

  const handleSaveGeneral = async () => {
    if (!game) return;
    setLoading(true);
    try {
      await api.post(`/v1/games/${game.id}/config/general`, general);
      toast.success('General settings saved');
      onSaved?.();
    } catch (err) {
      console.error(err);
      toast.error('Failed to save general');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRtpProfile = async () => {
    if (!game || !newRtp.code) return;
    setLoading(true);
    try {
      const res = await api.post(`/v1/games/${game.id}/config/rtp`, newRtp);
      setRtpConfig((prev) => ({
        ...prev,
        profiles: [res.data, ...(prev.profiles || [])],
        default_profile_id: res.data.is_default ? res.data.id : prev.default_profile_id,
      }));
      setNewRtp({ code: '', rtp_value: 96.0, is_default: false });
      toast.success('RTP profile created (approval required)');
    } catch (err) {
      console.error(err);
      toast.error('Failed to create RTP profile');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyRtpPreset = async () => {
    if (!selectedRtpPreset || !game) return;
    try {
      const res = await api.get(`/v1/game-config/presets/${selectedRtpPreset}`);
      const preset = res.data;
      if (preset?.values) {
        setNewRtp((prev) => ({
          ...prev,
          ...preset.values,
        }));
      }
      await api.post(`/v1/game-config/presets/${selectedRtpPreset}/apply`, {
        game_id: game.id,
        game_type: resolvedCoreType || 'SLOT',
        config_type: 'rtp',
      });
      toast.success('RTP preset uygulandı. Değerler forma yansıtıldı.');
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      toast.error(apiError?.message || 'RTP preset uygulanamadı.');
    }
  };

  const handleSaveBets = async () => {
    if (!game) return;
    setLoading(true);
    try {
      const payload = { ...bets, game_id: game.id };
      const res = await api.post(`/v1/games/${game.id}/config/bets`, payload);
      setBets(res.data);
      toast.success('Bet config saved');
    } catch (err) {
      console.error(err);
      const detail = err?.response?.data?.detail;
      if (Array.isArray(detail)) {
        const msg = detail.map((d) => d?.msg || JSON.stringify(d)).join(' | ');
        toast.error(msg);
      } else if (typeof detail === 'string') {
        toast.error(detail);
      } else {
        toast.error('Failed to save bets');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleApplyBetsPreset = async () => {
    if (!selectedBetsPreset || !game) return;
    try {
      const res = await api.get(`/v1/game-config/presets/${selectedBetsPreset}`);
      const preset = res.data;
      if (preset?.values) {
        setBets((prev) => ({
          ...prev,
          ...preset.values,
        }));
      }
      await api.post(`/v1/game-config/presets/${selectedBetsPreset}/apply`, {
        game_id: game.id,
        game_type: resolvedCoreType || game.core_type,
        config_type: 'bets',
      });
      toast.success('Bets preset uygulandı. Değerler forma yansıtıldı.');
    } catch (err) {
      console.error(err);
      const apiError = err?.response?.data;
      toast.error(apiError?.message || 'Bets preset uygulanamadı.');
    }
  };

  const handleSaveFeatures = async () => {
    if (!game) return;
    setLoading(true);
    try {
      const res = await api.post(`/v1/games/${game.id}/config/features`, { game_id: game.id, features });
      setFeatures(res.data.features);
      toast.success('Feature flags saved');
    } catch (err) {
      console.error(err);
      toast.error('Failed to save features');
    } finally {
      setLoading(false);
    }
  };

  const parseTags = (value) =>
    value
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

  return (
    <div className="space-y-4">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList
          className="flex flex-wrap gap-2 whitespace-nowrap overflow-x-auto scrollbar-thin items-center"
        >
          {visibleTabs.includes('general') && (
            <TabsTrigger value="general">General</TabsTrigger>
          )}
          {visibleTabs.includes('rtp') && (
            <TabsTrigger value="rtp">Math &amp; RTP</TabsTrigger>
          )}
          {visibleTabs.includes('bets') && (
            <TabsTrigger value="bets">Bets &amp; Limits</TabsTrigger>
          )}
          {visibleTabs.includes('features') && (
            <TabsTrigger value="features">Features</TabsTrigger>
          )}
          {visibleTabs.includes('paytable') && (
            <TabsTrigger value="paytable">Paytable</TabsTrigger>
          )}
          {visibleTabs.includes('reels') && (
            <TabsTrigger value="reels">Reel Strips</TabsTrigger>
          )}
          {visibleTabs.includes('poker_rules') && (
            <TabsTrigger value="poker_rules">Poker Rules &amp; Rake</TabsTrigger>
          )}
          {visibleTabs.includes('crash_math') && (
            <TabsTrigger value="crash_math">Crash Math</TabsTrigger>
          )}
          {visibleTabs.includes('blackjack_rules') && (
            <TabsTrigger value="blackjack_rules">Blackjack Rules &amp; Side Bets</TabsTrigger>
          )}

          {visibleTabs.includes('dice_math') && (
            <TabsTrigger value="dice_math">Dice Math</TabsTrigger>
          )}
          {visibleTabs.includes('assets') && (
            <TabsTrigger value="assets">Assets</TabsTrigger>
          )}
          {visibleTabs.includes('logs') && (
            <TabsTrigger value="logs">Logs</TabsTrigger>
          )}
        </TabsList>

        {/* GENERAL TAB */}
        {visibleTabs.includes('general') && (
          <TabsContent value="general" className="space-y-4 pt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input
                  value={general.name}
                  onChange={(e) => setGeneral({ ...general, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Provider</Label>
                <Input
                  value={general.provider}
                  onChange={(e) => setGeneral({ ...general, provider: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Category</Label>
                <Select
                  value={general.category}
                  onValueChange={(val) => setGeneral({ ...general, category: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="slot">Slot</SelectItem>
                    <SelectItem value="live">Live</SelectItem>
                    <SelectItem value="crash">Crash</SelectItem>
                    <SelectItem value="table">Table</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Default Language</Label>
                <Input
                  value={general.default_language}
                  onChange={(e) => setGeneral({ ...general, default_language: e.target.value })}
                />
              </div>
              <div className="space-y-2 col-span-2">
                <Label>Lobby Sort Order</Label>
                <Input
                  type="number"
                  value={general.lobby_sort_order}
                  onChange={(e) =>
                    setGeneral({ ...general, lobby_sort_order: Number(e.target.value) })
                  }
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Tags (comma separated)</Label>
              <Input
                value={general.tags.join(', ')}
                onChange={(e) => setGeneral({ ...general, tags: parseTags(e.target.value) })}
                placeholder="new, popular, feature_buy"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Visibility Countries (comma separated)</Label>
                <Input
                  value={general.visibility_rules.countries.join(', ')}
                  onChange={(e) =>
                    setGeneral({
                      ...general,
                      visibility_rules: {
                        ...general.visibility_rules,
                        countries: parseTags(e.target.value),
                      },
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Segments (comma separated)</Label>
                <Input
                  value={general.visibility_rules.segments.join(', ')}
                  onChange={(e) =>
                    setGeneral({
                      ...general,
                      visibility_rules: {
                        ...general.visibility_rules,
                        segments: parseTags(e.target.value),
                      },
                    })
                  }
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>VIP Min Level</Label>
              <Input
                type="number"
                value={general.visibility_rules.vip_min_level}
                onChange={(e) =>
                  setGeneral({
                    ...general,
                    visibility_rules: {
                      ...general.visibility_rules,
                      vip_min_level: Number(e.target.value) || 1,
                    },
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={general.status}
                onValueChange={(val) => setGeneral({ ...general, status: val })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                  <SelectItem value="maintenance">Maintenance</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleSaveGeneral} disabled={loading} className="mt-2">
              Save General
            </Button>
          </TabsContent>
        )}

        {/* RTP TAB */}
        {visibleTabs.includes('rtp') && (
          <TabsContent value="rtp" className="space-y-4 pt-4">
            {/* Preset bar */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Preset</CardTitle>
                <CardDescription>
                  RTP profili için hazır preset&apos;leri uygula, ardından manuel olarak düzenleyebilirsin.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col sm:flex-row gap-2 items-start sm:items-end">
                <div className="flex-1 space-y-1">
                  <Label>Preset seç</Label>
                  <Select
                    value={selectedRtpPreset}
                    onValueChange={setSelectedRtpPreset}
                    disabled={loading || rtpPresets.length === 0}
                  >
                    <SelectTrigger>
                      <SelectValue
                        placeholder={rtpPresets.length ? 'Seçiniz' : 'Preset bulunamadı'}
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {rtpPresets.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  type="button"
                  onClick={handleApplyRtpPreset}
                  disabled={loading || !selectedRtpPreset}
                  className="whitespace-nowrap"
                >
                  Apply Preset
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>RTP Profiles</CardTitle>
                <CardDescription>
                  Any RTP change will be logged and can require dual approval in production.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Code</Label>
                    <Input
                      placeholder="RTP_96"
                      value={newRtp.code}
                      onChange={(e) => setNewRtp({ ...newRtp, code: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>RTP Value</Label>
                    <Input
                      type="number"
                      value={newRtp.rtp_value}
                      onChange={(e) =>
                        setNewRtp({ ...newRtp, rtp_value: Number(e.target.value) })
                      }
                    />
                  </div>
                  <div className="flex items-end gap-2">
                    <Switch
                      checked={newRtp.is_default}
                      onCheckedChange={(v) => setNewRtp({ ...newRtp, is_default: v })}
                    />
                    <span className="text-xs text-muted-foreground">Set as default</span>
                  </div>
                </div>
                <Button onClick={handleAddRtpProfile} disabled={loading || !newRtp.code}>
                  Create RTP Profile
                </Button>

                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>RTP</TableHead>
                      <TableHead>Default</TableHead>
                      <TableHead>Created At</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(rtpConfig.profiles || []).map((p) => (
                      <TableRow key={p.id}>
                        <TableCell>{p.code}</TableCell>
                        <TableCell>{p.rtp_value}%</TableCell>
                        <TableCell>
                          {rtpConfig.default_profile_id === p.id ? (
                            <Badge variant="default">Default</Badge>
                          ) : p.is_default ? (
                            <Badge variant="outline">Default</Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {new Date(p.created_at).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!rtpConfig.profiles || rtpConfig.profiles.length === 0) && (
                      <TableRow>
                        <TableCell
                          colSpan={4}
                          className="text-center text-xs text-muted-foreground"
                        >
                          No RTP profiles yet.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* BETS TAB */}
        {visibleTabs.includes('bets') && (
          <TabsContent value="bets" className="space-y-4 pt-4">
            {/* Preset bar */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Preset</CardTitle>
                <CardDescription>
                  Bet &amp; limits için hazır preset&apos;leri uygula, ardından manuel olarak düzenleyebilirsin.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col sm:flex-row gap-2 items-start sm:items-end">
                <div className="flex-1 space-y-1">
                  <Label>Preset seç</Label>
                  <Select
                    value={selectedBetsPreset}
                    onValueChange={setSelectedBetsPreset}
                    disabled={loading || betsPresets.length === 0}
                  >
                    <SelectTrigger>
                      <SelectValue
                        placeholder={betsPresets.length ? 'Seçiniz' : 'Preset bulunamadı'}
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {betsPresets.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  type="button"
                  onClick={handleApplyBetsPreset}
                  disabled={loading || !selectedBetsPreset}
                  className="whitespace-nowrap"
                >
                  Apply Preset
                </Button>
              </CardContent>
            </Card>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Min Bet</Label>
                <Input
                  type="number"
                  value={bets.min_bet}
                  onChange={(e) => setBets({ ...bets, min_bet: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-2">
                <Label>Max Bet</Label>
                <Input
                  type="number"
                  value={bets.max_bet}
                  onChange={(e) => setBets({ ...bets, max_bet: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-2">
                <Label>Step</Label>
                <Input
                  type="number"
                  value={bets.step}
                  onChange={(e) => setBets({ ...bets, step: Number(e.target.value) })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Presets (comma separated)</Label>
              <Input
                value={(bets.presets || []).join(', ')}
                onChange={(e) =>
                  setBets({
                    ...bets,
                    presets: parseTags(e.target.value)
                      .map((v) => Number(v))
                      .filter((v) => !Number.isNaN(v)),
                  })
                }
              />
            </div>
            <Button onClick={handleSaveBets} disabled={loading} className="mt-2">
              Save Bets &amp; Limits
            </Button>
          </TabsContent>
        )}

        {/* FEATURES TAB */}
        {visibleTabs.includes('features') && (
          <TabsContent value="features" className="space-y-4 pt-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 border rounded-md">
                <div>
                  <p className="font-medium text-sm">Bonus Buy</p>
                  <p className="text-xs text-muted-foreground">
                    Allow players to purchase bonus rounds directly.
                  </p>
                </div>
                <Switch
                  checked={!!features.bonus_buy}
                  onCheckedChange={(v) => setFeatures({ ...features, bonus_buy: v })}
                />
              </div>
              <div className="flex items-center justify-between p-3 border rounded-md">
                <div>
                  <p className="font-medium text-sm">Turbo Spin</p>
                  <p className="text-xs text-muted-foreground">
                    Faster spin animations for high-velocity players.
                  </p>
                </div>
                <Switch
                  checked={!!features.turbo_spin}
                  onCheckedChange={(v) => setFeatures({ ...features, turbo_spin: v })}
                />
              </div>
              <div className="flex items-center justify-between p-3 border rounded-md">
                <div>
                  <p className="font-medium text-sm">Autoplay</p>
                  <p className="text-xs text-muted-foreground">
                    Automatically play multiple spins in sequence.
                  </p>
                </div>
                <Switch
                  checked={!!features.autoplay}
                  onCheckedChange={(v) => setFeatures({ ...features, autoplay: v })}
                />
              </div>
            </div>
            <Button onClick={handleSaveFeatures} disabled={loading} className="mt-2">
              Save Features
            </Button>
          </TabsContent>
        )}

        {/* POKER RULES TAB */}
        {visibleTabs.includes('poker_rules') && (
          <TabsContent value="poker_rules" className="space-y-4 pt-4">
            {game?.core_type === 'TABLE_POKER' ? (
              <GamePokerRulesTab game={game} />
            ) : (
              <Card>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    Poker Rules &amp; Rake sadece TABLE_POKER oyunları için geçerlidir.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        )}

        {/* CRASH MATH TAB */}
        {visibleTabs.includes('crash_math') && (
          <TabsContent value="crash_math" className="space-y-4 pt-4">
            {resolvedCoreType === 'CRASH' ? (
              <GameCrashMathTab game={game} />
            ) : (
              <Card>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    Crash Math sadece CRASH oyunları için geçerlidir.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        )}

        {/* DICE MATH TAB */}
        {visibleTabs.includes('dice_math') && (
          <TabsContent value="dice_math" className="space-y-4 pt-4">
            {resolvedCoreType === 'DICE' ? (
              <GameDiceMathTab game={game} />
            ) : (
              <Card>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    Dice Math sadece DICE oyunları için geçerlidir.
                  </p>
                </CardContent>
        {/* BLACKJACK RULES TAB */}
        {visibleTabs.includes('blackjack_rules') && (
          <TabsContent value="blackjack_rules" className="space-y-4 pt-4">
            {resolvedCoreType === 'TABLE_BLACKJACK' ? (
              <div className="text-xs text-muted-foreground">
                {/* TODO: GameBlackjackRulesTab bileşeni burada render edilecek */}
                Blackjack Rules &amp; Side Bets sekmesi henüz UI tarafında tamamlanmadı.
              </div>
            ) : (
              <Card>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    Blackjack Rules &amp; Side Bets sadece TABLE_BLACKJACK oyunları için geçerlidir.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        )}

              </Card>
            )}
          </TabsContent>
        )}

        {/* REEL STRIPS TAB */}
        {visibleTabs.includes('reels') && (
          <TabsContent value="reels" className="space-y-4 pt-4">
            <GameReelStripsTab game={game} />
          </TabsContent>
        )}

        {/* PAYTABLE TAB */}
        {visibleTabs.includes('paytable') && (
          <TabsContent value="paytable" className="space-y-4 pt-4">
            <GamePaytableTab game={game} paytable={paytable} onReload={reloadPaytable} />
          </TabsContent>
        )}

        {/* ASSETS TAB */}
        {visibleTabs.includes('assets') && (
          <TabsContent value="assets" className="space-y-4 pt-4">
            <GameAssetsTab game={game} />
          </TabsContent>
        )}

        {/* LOGS TAB */}
        {visibleTabs.includes('logs') && (
          <TabsContent value="logs" className="space-y-4 pt-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Activity className="w-4 h-4" /> Config Change Logs
                </CardTitle>
              </CardHeader>
              <CardContent className="max-h-64 overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>When</TableHead>
                      <TableHead>Admin</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="text-xs text-muted-foreground">
                          {new Date(log.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-xs">{log.admin_id}</TableCell>
                        <TableCell className="text-xs">{log.action}</TableCell>
                        <TableCell className="text-xs font-mono truncate max-w-xs">
                          {JSON.stringify(log.details)}
                        </TableCell>
                      </TableRow>
                    ))}
                    {logs.length === 0 && (
                      <TableRow>
                        <TableCell
                          colSpan={4}
                          className="text-center text-xs text-muted-foreground"
                        >
                          No config changes logged yet.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
};

export default GameConfigPanel;
