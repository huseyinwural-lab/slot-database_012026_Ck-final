import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Gift, Zap, DollarSign, RotateCcw, Clock } from 'lucide-react';
import NewMemberManualBonusCard from '../components/bonus/NewMemberManualBonusCard';


const BonusManagement = () => {
  const [bonuses, setBonuses] = useState([]);
  const [category, setCategory] = useState('Financial');
  const [bonusType, setBonusType] = useState('deposit_match');
  const [trigger, setTrigger] = useState('manual');
  
  // Dynamic Form State
  const [form, setForm] = useState({
    name: '',
    wager_req: 35,
    auto_apply: false,
    
    // Financial
    min_deposit: 20,
    reward_amount: 0,
    reward_percentage: 100,
    max_reward: 500,
    
    // RTP / Balance
    luck_boost_factor: 1.5,
    luck_boost_spins: 50,
    rtp_boost_percent: 2.0,
    guaranteed_win_spins: 1,
    
    // Free Spins
    fs_count: 10,
    fs_bet_value: 0.20,
    fs_game_ids: [],
    
    // Cashback
    cashback_percentage: 10,
    provider_ids: [],
    
    // Trigger
    trigger_value: 0 // e.g. min deposit amount or loss amount
  });

  const fetchBonuses = async () => {
    try {
        const res = await api.get('/v1/bonuses');
        // Handle paginated response or direct list
        const items = res.data.items || res.data || [];
        setBonuses(Array.isArray(items) ? items : []);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchBonuses(); }, []);

  const handleCreate = async () => {
    const rules = {
        min_deposit: form.min_deposit,
        reward_amount: form.reward_amount,
        reward_percentage: form.reward_percentage,
        max_reward: form.max_reward,
        luck_boost_factor: form.luck_boost_factor,
        luck_boost_spins: form.luck_boost_spins,
        rtp_boost_percent: form.rtp_boost_percent,
        guaranteed_win_spins: form.guaranteed_win_spins,
        fs_count: form.fs_count,
        fs_bet_value: form.fs_bet_value,
        cashback_percentage: form.cashback_percentage,
    };

    const payload = {
        name: form.name,
        type: bonusType,
        category: category,
        trigger: trigger,
        wager_req: form.wager_req,
        auto_apply: form.auto_apply,
        rules: rules
    };

    try {
        await api.post('/v1/bonuses', payload);
        toast.success("Bonus Created");
        fetchBonuses();
    } catch (err) {
        const status = err?.response?.status;
        const code = err?.response?.data?.error_code;
        if (status === 403 && code === 'TENANT_FEATURE_DISABLED') {
          toast.error('This module is disabled for your tenant.');
        } else {
          toast.error('Failed to create bonus');
        }
    }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Bonus Campaigns</h2>

        {/* Yeni Üye Manuel Bonus */}
        <NewMemberManualBonusCard />
        
        <div className="grid md:grid-cols-3 gap-6">
            {/* --- CONFIGURATION PANEL --- */}
            <Card className="md:col-span-1 h-fit">
                <CardHeader>
                    <CardTitle>Create Campaign</CardTitle>
                    <CardDescription>Select Category & Type</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Category</Label>
                        <Tabs value={category} onValueChange={setCategory}>
                            <TabsList className="grid grid-cols-5 h-auto">
                                <TabsTrigger value="Financial" title="Financial"><DollarSign className="w-4 h-4" /></TabsTrigger>
                                <TabsTrigger value="RTP" title="Balance/RTP"><Zap className="w-4 h-4" /></TabsTrigger>
                                <TabsTrigger value="Non-Deposit" title="Non-Deposit"><Gift className="w-4 h-4" /></TabsTrigger>
                                <TabsTrigger value="FreeSpin" title="Free Spins"><RotateCcw className="w-4 h-4" /></TabsTrigger>
                                <TabsTrigger value="Cashback" title="Cashback"><Clock className="w-4 h-4" /></TabsTrigger>
                            </TabsList>
                        </Tabs>
                    </div>

                    <div className="space-y-2">
                        <Label>Bonus Type</Label>
                        <Select value={bonusType} onValueChange={setBonusType}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                                {category === 'Financial' && (
                                    <>
                                        <SelectItem value="deposit_match">Deposit Match (Welcome/Reload)</SelectItem>
                                        <SelectItem value="threshold_deposit">Threshold Deposit (>Amount)</SelectItem>
                                        <SelectItem value="high_roller">High Roller</SelectItem>
                                        <SelectItem value="manual_comp">Manual Comp</SelectItem>
                                        <SelectItem value="moneyback">Moneyback</SelectItem>
                                        <SelectItem value="ladder">Ladder Bonus</SelectItem>
                                    </>
                                )}
                                {category === 'RTP' && (
                                    <>
                                        <SelectItem value="rtp_booster">RTP Booster</SelectItem>
                                        <SelectItem value="guaranteed_win">First Game Guaranteed Win</SelectItem>
                                        <SelectItem value="spins_powerup">Spins Power-Up</SelectItem>
                                        <SelectItem value="mystery_rtp">Mystery RTP</SelectItem>
                                        <SelectItem value="rakeback">Rakeback</SelectItem>
                                    </>
                                )}
                                {category === 'Non-Deposit' && (
                                    <>
                                        <SelectItem value="welcome_no_dep">Welcome No-Deposit</SelectItem>
                                        <SelectItem value="referral">Referral Bonus</SelectItem>
                                        <SelectItem value="kyc_completion">KYC Completion</SelectItem>
                                        <SelectItem value="reactivation">Reactivation</SelectItem>
                                        <SelectItem value="birthday">Birthday Bonus</SelectItem>
                                    </>
                                )}
                                {category === 'FreeSpin' && (
                                    <>
                                        <SelectItem value="fs_package">Free Spin Package</SelectItem>
                                        <SelectItem value="fs_bundle">Multi-Game Bundle</SelectItem>
                                        <SelectItem value="vip_fs_reload">VIP FS Reload</SelectItem>
                                    </>
                                )}
                                {category === 'Cashback' && (
                                    <>
                                        <SelectItem value="loss_cashback">Loss Cashback</SelectItem>
                                        <SelectItem value="periodic_cashback">Daily/Weekly Cashback</SelectItem>
                                        <SelectItem value="provider_cashback">Provider Specific</SelectItem>
                                    </>
                                )}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label>Campaign Name</Label>
                        <Input value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. Summer Special" />
                    </div>

                    {/* --- DYNAMIC FIELDS --- */}
                    {(category === 'Financial' || category === 'Non-Deposit') && (
                        <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-2">
                                <Label>Reward %</Label>
                                <Input type="number" value={form.reward_percentage || ''} onChange={e => setForm({...form, reward_percentage: e.target.value})} placeholder="100" />
                            </div>
                            <div className="space-y-2">
                                <Label>Or Amount ($)</Label>
                                <Input type="number" value={form.reward_amount || ''} onChange={e => setForm({...form, reward_amount: e.target.value})} placeholder="50" />
                            </div>
                            <div className="space-y-2">
                                <Label>Min Deposit</Label>
                                <Input type="number" value={form.min_deposit || ''} onChange={e => setForm({...form, min_deposit: e.target.value})} />
                            </div>
                            <div className="space-y-2">
                                <Label>Max Reward</Label>
                                <Input type="number" value={form.max_reward || ''} onChange={e => setForm({...form, max_reward: e.target.value})} />
                            </div>
                        </div>
                    )}

                    {category === 'RTP' && (
                        <div className="space-y-2 border p-2 rounded">
                            <div className="grid grid-cols-2 gap-2">
                                <div className="space-y-2">
                                    <Label>RTP Boost (%)</Label>
                                    <Input type="number" value={form.rtp_boost_percent} onChange={e => setForm({...form, rtp_boost_percent: e.target.value})} />
                                </div>
                                <div className="space-y-2">
                                    <Label>Duration (Spins)</Label>
                                    <Input type="number" value={form.luck_boost_spins} onChange={e => setForm({...form, luck_boost_spins: e.target.value})} />
                                </div>
                            </div>
                            {bonusType === 'guaranteed_win' && (
                                <div className="space-y-2 mt-2">
                                    <Label>Guaranteed Wins</Label>
                                    <Input type="number" value={form.guaranteed_win_spins} onChange={e => setForm({...form, guaranteed_win_spins: e.target.value})} />
                                </div>
                            )}
                        </div>
                    )}

                    {category === 'FreeSpin' && (
                        <div className="grid grid-cols-2 gap-2 border p-2 rounded">
                            <div className="space-y-2">
                                <Label>Count</Label>
                                <Input type="number" value={form.fs_count} onChange={e => setForm({...form, fs_count: e.target.value})} />
                            </div>
                            <div className="space-y-2">
                                <Label>Bet Value ($)</Label>
                                <Input type="number" value={form.fs_bet_value} onChange={e => setForm({...form, fs_bet_value: e.target.value})} />
                            </div>
                        </div>
                    )}

                    {category === 'Cashback' && (
                        <div className="space-y-2 border p-2 rounded">
                            <Label>Cashback Percentage (%)</Label>
                            <Input type="number" value={form.cashback_percentage} onChange={e => setForm({...form, cashback_percentage: e.target.value})} />
                        </div>
                    )}

                    <div className="space-y-2 pt-2 border-t">
                        <Label>Trigger Event</Label>
                        <Select value={trigger} onValueChange={setTrigger}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="manual">Manual Assignment</SelectItem>
                                <SelectItem value="registration">Registration</SelectItem>
                                <SelectItem value="first_deposit">First Deposit</SelectItem>
                                <SelectItem value="deposit_amount">Deposit > X</SelectItem>
                                <SelectItem value="loss_amount">Loss > X</SelectItem>
                                <SelectItem value="vip_level_up">VIP Level Up</SelectItem>
                                <SelectItem value="referral">Referral</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label>Wager Requirement (x)</Label>
                        <Input type="number" value={form.wager_req} onChange={e => setForm({...form, wager_req: e.target.value})} />
                    </div>

                    <div className="flex items-center gap-2 pt-2">
                        <Switch checked={form.auto_apply} onCheckedChange={c => setForm({...form, auto_apply: c})} />
                        <Label>Auto-apply when triggered</Label>
                    </div>

                    <Button onClick={handleCreate} className="w-full mt-4">Launch Campaign</Button>
                </CardContent>
            </Card>

            {/* --- LIST PANEL --- */}
            <div className="md:col-span-2 space-y-4">
                <h3 className="font-semibold text-lg">Active Campaigns</h3>
                {bonuses.length === 0 && <div className="text-muted-foreground">No active bonuses.</div>}
                {bonuses.map(bonus => (
                    <Card key={bonus.id} className="hover:bg-secondary/10 transition-colors">
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <div>
                                <CardTitle className="text-lg">{bonus.name}</CardTitle>
                                <div className="flex gap-2 mt-1">
                                    <Badge variant="outline" className="uppercase text-[10px]">{bonus.category}</Badge>
                                    <Badge variant="secondary" className="uppercase text-[10px]">{bonus.type.replace(/_/g, ' ')}</Badge>
                                    <Badge className="uppercase text-[10px] bg-blue-500/20 text-blue-500 hover:bg-blue-500/30">Trigger: {bonus.trigger}</Badge>
                                </div>
                            </div>
                            <Badge variant={bonus.auto_apply ? "default" : "secondary"}>
                                {bonus.auto_apply ? "Auto" : "Manual"}
                            </Badge>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-3 gap-4 text-xs text-muted-foreground">
                                {bonus.rules.reward_percentage && <div>Match: <span className="font-bold text-foreground">{bonus.rules.reward_percentage}%</span></div>}
                                {bonus.rules.reward_amount && <div>Reward: <span className="font-bold text-foreground">${bonus.rules.reward_amount}</span></div>}
                                {bonus.rules.rtp_boost_percent && <div>RTP Boost: <span className="font-bold text-green-500">+{bonus.rules.rtp_boost_percent}%</span></div>}
                                {bonus.rules.fs_count && <div>Free Spins: <span className="font-bold text-foreground">{bonus.rules.fs_count}</span></div>}
                                {bonus.rules.cashback_percentage && <div>Cashback: <span className="font-bold text-foreground">{bonus.rules.cashback_percentage}%</span></div>}
                                <div>Wager: <span className="font-bold text-foreground">x{bonus.wager_req}</span></div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    </div>
  );
};

export default BonusManagement;
