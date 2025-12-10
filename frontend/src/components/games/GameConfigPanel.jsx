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

  useEffect(() => {
    if (!game) return;

    const loadAll = async () => {
      try {
        // General
        const generalRes = await api.get(`/v1/games/${game.id}/config/general`);
        setGeneral(generalRes.data);

        // RTP
        const rtpRes = await api.get(`/v1/games/${game.id}/config/rtp`);
        setRtpConfig(rtpRes.data);

        // Bets
        const betRes = await api.get(`/v1/games/${game.id}/config/bets`);
        if (betRes.data?.config) setBets(betRes.data.config);

        // Features
        const featRes = await api.get(`/v1/games/${game.id}/config/features`);
        setFeatures(featRes.data.features || {});

        // Paytable
        const payRes = await api.get(`/v1/games/${game.id}/config/paytable`);
        setPaytable(payRes.data);

        // Logs
        const logsRes = await api.get(`/v1/games/${game.id}/config/logs?limit=50`);
        setLogs(logsRes.data.items || []);
      } catch (err) {
        console.error(err);
        toast.error('Failed to load game config');
      }
    };

    loadAll();
  }, [game]);

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
      toast.error(err.response?.data?.detail || 'Failed to save bets');
    } finally {
      setLoading(false);
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
        <TabsList className="grid w-full grid-cols-12">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="rtp">Math &amp; RTP</TabsTrigger>
          <TabsTrigger value="bets">Bets &amp; Limits</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
          <TabsTrigger value="reels">Reel Strips</TabsTrigger>
          <TabsTrigger value="paytable">Paytable</TabsTrigger>
          <TabsTrigger value="poker_rules">Poker Rules &amp; Rake</TabsTrigger>
          <TabsTrigger value="crash_math">Crash Math</TabsTrigger>
          <TabsTrigger value="dice_math">Dice Math</TabsTrigger>
          <TabsTrigger value="assets">Assets</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        {/* GENERAL TAB */}
        <TabsContent value="general" className="space-y-4 pt-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input value={general.name} onChange={(e) => setGeneral({ ...general, name: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Provider</Label>
              <Input value={general.provider} onChange={(e) => setGeneral({ ...general, provider: e.target.value })} />
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
                onChange={(e) => setGeneral({ ...general, lobby_sort_order: Number(e.target.value) })}
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
            <Select value={general.status} onValueChange={(val) => setGeneral({ ...general, status: val })}>
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

        {/* RTP TAB */}
        <TabsContent value="rtp" className="space-y-4 pt-4">
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
                    onChange={(e) => setNewRtp({ ...newRtp, rtp_value: Number(e.target.value) })}
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
                      <TableCell colSpan={4} className="text-center text-xs text-muted-foreground">
                        No RTP profiles yet.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* BETS TAB */}
        <TabsContent value="bets" className="space-y-4 pt-4">
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
                  presets: parseTags(e.target.value).map((v) => Number(v)).filter((v) => !Number.isNaN(v)),
                })
              }
            />
          </div>
          <Button onClick={handleSaveBets} disabled={loading} className="mt-2">
            Save Bets &amp; Limits
          </Button>
        </TabsContent>

        {/* FEATURES TAB */}
        <TabsContent value="features" className="space-y-4 pt-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border rounded-md">
              <div>
                <p className="font-medium text-sm">Bonus Buy</p>
                <p className="text-xs text-muted-foreground">Allow players to purchase bonus rounds directly.</p>
              </div>
              <Switch
                checked={!!features.bonus_buy}
                onCheckedChange={(v) => setFeatures({ ...features, bonus_buy: v })}
              />
            </div>
            <div className="flex items-center justify-between p-3 border rounded-md">
              <div>
                <p className="font-medium text-sm">Turbo Spin</p>
                <p className="text-xs text-muted-foreground">Faster spin animations for high-velocity players.</p>
              </div>
              <Switch
                checked={!!features.turbo_spin}
                onCheckedChange={(v) => setFeatures({ ...features, turbo_spin: v })}
              />
            </div>
            <div className="flex items-center justify-between p-3 border rounded-md">
              <div>
                <p className="font-medium text-sm">Autoplay</p>
                <p className="text-xs text-muted-foreground">Automatically play multiple spins in sequence.</p>
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


        {/* POKER RULES TAB - only for TABLE_POKER games (guard FE seviyesinde yapılır) */}
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

        {/* REEL STRIPS TAB */}
        <TabsContent value="reels" className="space-y-4 pt-4">
          <GameReelStripsTab game={game} />
        </TabsContent>

        {/* PAYTABLE TAB */}
        <TabsContent value="paytable" className="space-y-4 pt-4">
          <GamePaytableTab
            game={game}
            paytable={paytable}
            onReload={reloadPaytable}
          />
        </TabsContent>

        {/* ASSETS TAB */}
        <TabsContent value="assets" className="space-y-4 pt-4">
          <GameAssetsTab game={game} />
        </TabsContent>

        {/* LOGS TAB */}
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
                      <TableCell colSpan={4} className="text-center text-xs text-muted-foreground">
                        No config changes logged yet.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GameConfigPanel;
