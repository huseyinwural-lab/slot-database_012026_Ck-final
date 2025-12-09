import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Play } from 'lucide-react';

const BonusSimulator = () => {
  const [bonusConfig, setBonusConfig] = useState({
    bonus_type: 'welcome',
    current_percentage: 100,
    new_percentage: 150,
    current_wagering: 35,
    new_wagering: 40,
    expected_participants: 1000
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">🎁 Bonus & Campaign Simulator</CardTitle>
        <CardDescription>Bonus parametrelerinin ekonomik etkisi</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Bonus Type</Label>
              <Select value={bonusConfig.bonus_type} onValueChange={v => setBonusConfig({...bonusConfig, bonus_type: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="welcome">Welcome Bonus</SelectItem>
                  <SelectItem value="reload">Reload Bonus</SelectItem>
                  <SelectItem value="cashback">Cashback</SelectItem>
                  <SelectItem value="free_spins">Free Spins</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Current Bonus %</Label>
              <Input type="number" value={bonusConfig.current_percentage} onChange={e => setBonusConfig({...bonusConfig, current_percentage: parseInt(e.target.value)})} />
            </div>
            <div className="space-y-2">
              <Label>New Bonus %</Label>
              <Input type="number" value={bonusConfig.new_percentage} onChange={e => setBonusConfig({...bonusConfig, new_percentage: parseInt(e.target.value)})} />
            </div>
            <div className="space-y-2">
              <Label>Current Wagering</Label>
              <Input type="number" value={bonusConfig.current_wagering} onChange={e => setBonusConfig({...bonusConfig, current_wagering: parseInt(e.target.value)})} />
            </div>
            <div className="space-y-2">
              <Label>New Wagering</Label>
              <Input type="number" value={bonusConfig.new_wagering} onChange={e => setBonusConfig({...bonusConfig, new_wagering: parseInt(e.target.value)})} />
            </div>
            <div className="space-y-2">
              <Label>Expected Participants</Label>
              <Input type="number" value={bonusConfig.expected_participants} onChange={e => setBonusConfig({...bonusConfig, expected_participants: parseInt(e.target.value)})} />
            </div>
          </div>
          <Button><Play className="w-4 h-4 mr-2" /> Run Bonus Simulation</Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default BonusSimulator;
