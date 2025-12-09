import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const BonusManagement = () => {
  const [bonuses, setBonuses] = useState([]);
  const [newBonus, setNewBonus] = useState({ name: '', amount: 100, wager_req: 35, type: 'deposit' });

  const fetchBonuses = async () => {
    try {
        const res = await api.get('/v1/bonuses');
        setBonuses(res.data);
    } catch (err) {
        console.error(err);
    }
  };

  useEffect(() => { fetchBonuses(); }, []);

  const handleCreate = async () => {
    try {
        await api.post('/v1/bonuses', newBonus);
        toast.success("Bonus Created");
        fetchBonuses();
    } catch (err) {
        toast.error("Failed to create bonus");
    }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight">Bonus Campaigns</h2>
        
        <div className="grid md:grid-cols-3 gap-6">
            <Card className="md:col-span-1">
                <CardHeader>
                    <CardTitle>Create New Bonus</CardTitle>
                    <CardDescription>Launch a new campaign</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Bonus Name</Label>
                        <Input value={newBonus.name} onChange={e => setNewBonus({...newBonus, name: e.target.value})} placeholder="e.g. Welcome Offer" />
                    </div>
                    <div className="space-y-2">
                        <Label>Amount / Value</Label>
                        <Input type="number" value={newBonus.amount} onChange={e => setNewBonus({...newBonus, amount: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                        <Label>Wager Req (x)</Label>
                        <Input type="number" value={newBonus.wager_req} onChange={e => setNewBonus({...newBonus, wager_req: e.target.value})} />
                    </div>
                    <Button onClick={handleCreate} className="w-full">Create Campaign</Button>
                </CardContent>
            </Card>

            <div className="md:col-span-2 space-y-4">
                {bonuses.map(bonus => (
                    <Card key={bonus.id}>
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-lg">{bonus.name}</CardTitle>
                            <Badge variant="outline">{bonus.type}</Badge>
                        </CardHeader>
                        <CardContent>
                            <div className="flex gap-6 text-sm">
                                <div>
                                    <span className="text-muted-foreground block">Value</span>
                                    <span className="font-bold text-lg">${bonus.amount}</span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground block">Wager</span>
                                    <span className="font-bold text-lg">x{bonus.wager_req}</span>
                                </div>
                                <div>
                                    <span className="text-muted-foreground block">Status</span>
                                    <span className="text-green-500 font-medium">{bonus.status}</span>
                                </div>
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
