import React, { useEffect, useState } from 'react';
import api from '@/services/api';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  Beaker, TrendingUp, Users, Shield, Heart,
  Dna, Brain, Archive, RefreshCw, Eye, Target, Gift, Folder
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Play, Download } from 'lucide-react';

// Sub-components
import GameMathSimulator from '../components/simulation/GameMathSimulator';
import BonusSimulator from '../components/simulation/BonusSimulator';
import SimulationOverview from '../components/simulation/SimulationOverview';
import SimulationArchive from '../components/simulation/SimulationArchive';

const SimulationLab = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [runs, setRuns] = useState([]);
  
  const fetchRuns = async () => {
    try {
      const res = await api.get('/v1/simulation-lab/runs');
      setRuns(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    // initial fetch
    fetchRuns();

  }, []);

  const getStatusBadge = (status) => {
    const variants = {
      completed: 'default',
      running: 'secondary',
      failed: 'destructive',
      draft: 'outline'
    };
    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  const getTypeBadge = (type) => {
    const labels = {
      game_math: '🎰 Game Math',
      portfolio: '📈 Portfolio',
      bonus: '🎁 Bonus',
      cohort_ltv: '👥 Cohort/LTV',
      risk: '🛡️ Risk',
      rg: '❤️ RG',
      ab_variant: '🧬 A/B',
      mixed: '🧠 Mixed'
    };
    return <Badge variant="outline">{labels[type] || type}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Beaker className="w-8 h-8 text-purple-600" /> 🧪 Simulation Lab
        </h2>
        <Button onClick={fetchRuns}>
          <RefreshCw className="w-4 h-4 mr-2" /> Yenile
        </Button>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <ScrollArea className="w-full whitespace-nowrap rounded-md border">
          <TabsList className="w-full flex justify-start">
            <TabsTrigger value="overview"><Eye className="w-4 h-4 mr-2" /> Overview</TabsTrigger>
            <TabsTrigger value="game-math"><Target className="w-4 h-4 mr-2" /> 🎰 Game Math</TabsTrigger>
            <TabsTrigger value="portfolio"><TrendingUp className="w-4 h-4 mr-2" /> 📈 Portfolio</TabsTrigger>
            <TabsTrigger value="bonus"><Gift className="w-4 h-4 mr-2" /> 🎁 Bonus</TabsTrigger>
            <TabsTrigger value="cohort"><Users className="w-4 h-4 mr-2" /> 👥 Cohort/LTV</TabsTrigger>
            <TabsTrigger value="risk"><Shield className="w-4 h-4 mr-2" /> 🛡️ Risk</TabsTrigger>
            <TabsTrigger value="rg"><Heart className="w-4 h-4 mr-2" /> ❤️ RG</TabsTrigger>
            <TabsTrigger value="ab-sandbox"><Dna className="w-4 h-4 mr-2" /> 🧬 A/B Sandbox</TabsTrigger>
            <TabsTrigger value="scenario"><Brain className="w-4 h-4 mr-2" /> 🧠 Scenario Builder</TabsTrigger>
            <TabsTrigger value="archive"><Archive className="w-4 h-4 mr-2" /> 📁 Archive</TabsTrigger>
          </TabsList>
        </ScrollArea>

        {/* 1️⃣ OVERVIEW */}
        <TabsContent value="overview" className="mt-4">
          <SimulationOverview 
            runs={runs} 
            getTypeBadge={getTypeBadge} 
            getStatusBadge={getStatusBadge} 
          />
        </TabsContent>

        {/* 2️⃣ GAME MATH SIMULATOR */}
        <TabsContent value="game-math" className="mt-4">
          <GameMathSimulator onRunComplete={fetchRuns} />
        </TabsContent>

        {/* 3️⃣ PORTFOLIO SIMULATOR */}
        <TabsContent value="portfolio" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">📈 Portfolio RTP & Revenue Simulator</CardTitle>
              <CardDescription>Portföy RTP ve trafik değişikliklerinin GGR/NGR etkisi</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Button variant="outline" disabled title="Not implemented yet">
                    <Download className="w-4 h-4 mr-2" /> Import from Live Data
                  </Button>
                  <Button variant="outline" disabled title="Not implemented yet">
                    <Folder className="w-4 h-4 mr-2" /> Load Saved Scenario
                  </Button>
                  <Button disabled title="Not implemented yet">
                    <Play className="w-4 h-4 mr-2" /> Run Portfolio Simulation
                  </Button>
                </div>
                <p className="text-muted-foreground">Portfolio simülasyon arayüzü yakında eklenecek</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 4️⃣ BONUS SIMULATOR */}
        <TabsContent value="bonus" className="mt-4">
          <BonusSimulator />
        </TabsContent>

        {/* 5️⃣ COHORT/LTV */}
        <TabsContent value="cohort" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">👥 Player Cohort / LTV Simulator</CardTitle>
              <CardDescription>Segment LTV ve davranış simülasyonu</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Cohort/LTV simülasyon arayüzü yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 6️⃣ RISK */}
        <TabsContent value="risk" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🛡️ Risk & Fraud Scenario Simulator</CardTitle>
              <CardDescription>Risk kuralı değişikliklerinin etkisi</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Risk simülasyon arayüzü yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 7️⃣ RG */}
        <TabsContent value="rg" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">❤️ RG & Limits Impact Simulator</CardTitle>
              <CardDescription>RG limit politikalarının gelir etkisi</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">RG simülasyon arayüzü yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 8️⃣ A/B SANDBOX */}
        <TabsContent value="ab-sandbox" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🧬 A/B Variant Sandbox</CardTitle>
              <CardDescription>A/B test simülasyonu</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">A/B sandbox yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 9️⃣ SCENARIO BUILDER */}
        <TabsContent value="scenario" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">🧠 Scenario Builder (Multi-Module)</CardTitle>
              <CardDescription>Çok modüllü karmaşık senaryolar</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Scenario builder yakında eklenecek</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 🔟 ARCHIVE */}
        <TabsContent value="archive" className="mt-4">
          <SimulationArchive 
            runs={runs} 
            getTypeBadge={getTypeBadge} 
            getStatusBadge={getStatusBadge} 
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SimulationLab;
