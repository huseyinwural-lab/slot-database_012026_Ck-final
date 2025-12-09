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

const BonusManagement = () => {
  const [bonuses, setBonuses] = useState([]);
  const [bonusType, setBonusType] = useState('welcome');
  
  // Dynamic Form State
  const [form, setForm] = useState({
    name: '',
    wager_req: 35,
    auto_apply: false,
    min_deposit: 20,
    reward_amount: 0,
    reward_percentage: 100,
    luck_boost_factor: 1.5,
    luck_boost_spins: 50,
    cashback_percentage: 10
  });

  const fetchBonuses = async () => {
    try {
        const res = await api.get('/v1/bonuses');
        setBonuses(res.data);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchBonuses(); }, []);

  const handleCreate = async () => {
    const rules = {};
    if (bonusType === 'deposit' || bonusType === 'welcome') {
        rules.min_deposit = form.min_deposit;
        rules.reward_percentage = form.reward_percentage;
    }
    if (bonusType === 'referral') {
        rules.reward_amount = form.reward_amount;
    }
    if (bonusType === 'luck_boost') {
        rules.luck_boost_factor = form.luck_boost_factor;
        rules.luck_boost_spins = form.luck_boost_spins;
    }
    if (bonusType === 'cashback') {
        rules.cashback_percentage = form.cashback_percentage;
    }

    const payload = {
        name: form.name,
        type: bonusType,
        wager_req: form.wager_req,
        auto_apply: form.auto_apply,
        rules: rules
    };

    try {
        await api.post('/v1/bonuses', payload);
        toast.success("Bonus Created");
        fetchBonuses();
    } catch (err) { toast.error("Failed to create bonus"); }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Bonus Campaigns</h2>
        
        <div className="grid md:grid-cols-3 gap-6">
            <Card className="md:col-span-1 h-fit">
                <CardHeader>
                    <CardTitle>Create Campaign</CardTitle>
                    <CardDescription>Select type and configure rules</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Bonus Type</Label>
                        <Select value={bonusType} onValueChange={setBonusType}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="welcome">1. Welcome Bonus (Registration)</SelectItem>
                                <SelectItem value="deposit">2. Deposit Bonus</SelectItem>
                                <SelectItem value="referral">3. Referral Bonus</SelectItem>
                                <SelectItem value="luck_boost">4. New Player Luck Boost</SelectItem>
                                <SelectItem value="cashback">5. Cashback (Loss Return)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label>Campaign Name</Label>
                        <Input value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. Summer Special" />
                    </div>

                    {/* Dynamic Fields based on Type */}
                    {(bonusType === 'welcome' || bonusType === 'deposit') && (
                        <>
                            <div className="space-y-2">
                                <Label>Match Percentage (%)</Label>
                                <Input type="number" value={form.reward_percentage} onChange={e => setForm({...form, reward_percentage: e.target.value})} />
                            </div>
                            <div className="space-y-2">
                                <Label>Min Deposit ($)</Label>
                                <Input type="number" value={form.min_deposit} onChange={e => setForm({...form, min_deposit: e.target.value})} />
                            </div>
                        </>
                    )}

                    {bonusType === 'referral' && (
                        <div className="space-y-2">
                            <Label>Reward Amount per Friend ($)</Label>
                            <Input type="number" value={form.reward_amount} onChange={e => setForm({...form, reward_amount: e.target.value})} />
                        </div>
                    )}

                    {bonusType === 'luck_boost' && (
                        <>
                            <div className="space-y-2">
                                <Label>Luck Multiplier (e.g. 1.5x)</Label>
                                <Input type="number" step="0.1" value={form.luck_boost_factor} onChange={e => setForm({...form, luck_boost_factor: e.target.value})} />
                            </div>
                            <div className="space-y-2">
                                <Label>Duration (Spins)</Label>
                                <Input type="number" value={form.luck_boost_spins} onChange={e => setForm({...form, luck_boost_spins: e.target.value})} />
                            </div>
                        </>
                    )}

                    {bonusType === 'cashback' && (
                        <div className="space-y-2">
                            <Label>Cashback Percentage (%)</Label>
                            <Input type="number" value={form.cashback_percentage} onChange={e => setForm({...form, cashback_percentage: e.target.value})} />
                        </div>
                    )}

                    <div className="space-y-2">
                        <Label>Wager Requirement (x)</Label>
                        <Input type="number" value={form.wager_req} onChange={e => setForm({...form, wager_req: e.target.value})} />
                    </div>

                    <div className="flex items-center gap-2 pt-2">
                        <Switch checked={form.auto_apply} onCheckedChange={c => setForm({...form, auto_apply: c})} />
                        <Label>Auto-apply to new users</Label>
                    </div>

                    <Button onClick={handleCreate} className="w-full mt-4">Launch Campaign</Button>
                </CardContent>
            </Card>

            <div className="md:col-span-2 space-y-4">
                <h3 className="font-semibold text-lg">Active Campaigns</h3>
                {bonuses.length === 0 && <div className="text-muted-foreground">No active bonuses.</div>}
                {bonuses.map(bonus => (
                    <Card key={bonus.id}>
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <div>
                                <CardTitle className="text-lg">{bonus.name}</CardTitle>
                                <CardDescription className="uppercase text-xs font-bold mt-1 text-primary">{bonus.type.replace('_', ' ')}</CardDescription>
                            </div>
                            <Badge variant={bonus.auto_apply ? "default" : "secondary"}>
                                {bonus.auto_apply ? "Auto-Apply" : "Manual"}
                            </Badge>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                {bonus.rules.reward_percentage && <div>Match: <span className="font-bold">{bonus.rules.reward_percentage}%</span></div>}
                                {bonus.rules.cashback_percentage && <div>Cashback: <span className="font-bold">{bonus.rules.cashback_percentage}%</span></div>}
                                {bonus.rules.luck_boost_factor && <div>Boost: <span className="font-bold text-green-500">{bonus.rules.luck_boost_factor}x</span></div>}
                                <div>Wager: <span className="font-bold">x{bonus.wager_req}</span></div>
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
