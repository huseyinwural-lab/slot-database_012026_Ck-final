import React, { useCallback, useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { 
    BarChart3, TrendingUp, DollarSign, Users, Gamepad2, FileText, Download, Calendar, Activity, 
    Gift, Handshake, ShieldAlert, Scale, CheckCircle, Megaphone, Layout, Server, Settings2, Zap
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

const Reports = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      let endpoint = '/v1/reports/overview';
      if (activeTab === 'financial') endpoint = '/v1/reports/financial';
      if (activeTab === 'players') endpoint = '/v1/reports/players/ltv';
      if (activeTab === 'games') endpoint = '/v1/reports/games';
      if (activeTab === 'providers') endpoint = '/v1/reports/providers';
      if (activeTab === 'bonuses') endpoint = '/v1/reports/bonuses';
      if (activeTab === 'affiliates') endpoint = '/v1/reports/affiliates';
      if (activeTab === 'risk') endpoint = '/v1/reports/risk';
      if (activeTab === 'rg') endpoint = '/v1/reports/rg';
      if (activeTab === 'kyc') endpoint = '/v1/reports/kyc';
      if (activeTab === 'crm') endpoint = '/v1/reports/crm';
      if (activeTab === 'cms') endpoint = '/v1/reports/cms';
      if (activeTab === 'operational') endpoint = '/v1/reports/operational';
      if (activeTab === 'scheduled') endpoint = '/v1/reports/schedules';
      if (activeTab === 'exports') endpoint = '/v1/reports/exports';

      const res = await api.get(endpoint);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExport = async (type) => {
    try {
        await api.post('/v1/reports/exports', { type, requested_by: "admin" });
        toast.success("Export started");
    } catch { toast.error("Failed"); }
  };

  const NavButton = ({ tab, icon: Icon, label }) => (
    <Button 
        variant={activeTab===tab ? 'secondary' : 'ghost'} 
        className="w-full justify-start text-sm" 
        onClick={()=>setActiveTab(tab)}
    >
        <Icon className="w-4 h-4 mr-2" /> {label}
    </Button>
  );

  return (
    <div className="flex h-[calc(100vh-100px)]">
        {/* SIDEBAR NAVIGATION */}
        <div className="w-64 border-r bg-card p-2 flex flex-col h-full">
            <h3 className="font-bold mb-2 px-4 flex items-center gap-2"><BarChart3 className="w-5 h-5 text-primary" /> Reports</h3>
            <ScrollArea className="flex-1 pr-2">
                <div className="space-y-1">
                    <NavButton tab="overview" icon={Activity} label="Overview" />
                    <NavButton tab="live" icon={Zap} label="Real-Time" />
                    <div className="px-2 pt-2 text-[10px] font-bold text-muted-foreground uppercase">Core</div>
                    <NavButton tab="financial" icon={DollarSign} label="Financial" />
                    <NavButton tab="players" icon={Users} label="Players" />
                    <NavButton tab="games" icon={Gamepad2} label="Games" />
                    <NavButton tab="providers" icon={Server} label="Providers" />
                    <div className="px-2 pt-2 text-[10px] font-bold text-muted-foreground uppercase">Marketing</div>
                    <NavButton tab="bonuses" icon={Gift} label="Bonuses" />
                    <NavButton tab="affiliates" icon={Handshake} label="Affiliates" />
                    <NavButton tab="crm" icon={Megaphone} label="CRM" />
                    <NavButton tab="cms" icon={Layout} label="CMS" />
                    <div className="px-2 pt-2 text-[10px] font-bold text-muted-foreground uppercase">Risk & Compliance</div>
                    <NavButton tab="risk" icon={ShieldAlert} label="Risk & Fraud" />
                    <NavButton tab="rg" icon={Scale} label="Responsible Gaming" />
                    <NavButton tab="kyc" icon={CheckCircle} label="KYC" />
                    <div className="px-2 pt-2 text-[10px] font-bold text-muted-foreground uppercase">System</div>
                    <NavButton tab="operational" icon={Settings2} label="Operational" />
                    <NavButton tab="custom" icon={FileText} label="Custom Builder" />
                    <NavButton tab="scheduled" icon={Calendar} label="Scheduled" />
                    <NavButton tab="exports" icon={Download} label="Export Center" />
                </div>
            </ScrollArea>
        </div>

        {/* CONTENT AREA */}
        <ScrollArea className="flex-1 p-6 bg-secondary/5">
            {loading ? <div className="text-center p-10">Loading...</div> : (
                <>
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-2xl font-bold capitalize">{activeTab.replace('_', ' ')} Reports</h2>
                        <Button onClick={() => handleExport(activeTab + "_report")}>
                            <Download className="w-4 h-4 mr-2" /> Export
                        </Button>
                    </div>

                    {/* OVERVIEW */}
                    {activeTab === 'overview' && data && (
                        <div className="grid grid-cols-4 gap-4">
                            <Card><CardHeader className="pb-2"><CardTitle className="text-sm">GGR</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">${data.ggr.toLocaleString()}</div></CardContent></Card>
                            <Card><CardHeader className="pb-2"><CardTitle className="text-sm">NGR</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">${data.ngr.toLocaleString()}</div></CardContent></Card>
                            <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Players</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{data.active_players}</div></CardContent></Card>
                            <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Bonus Cost</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">${data.bonus_cost.toLocaleString()}</div></CardContent></Card>
                        </div>
                    )}

                    {/* GENERIC TABLE RENDERER FOR MOST REPORTS */}
                    {['financial', 'players', 'games', 'providers', 'bonuses', 'affiliates', 'crm', 'cms', 'scheduled', 'exports'].includes(activeTab) && Array.isArray(data) && (
                        <Card><CardContent className="pt-6">
                            <Table>
                                <TableHeader><TableRow>
                                    {Object.keys(data[0] || {}).map(k => <TableHead key={k} className="capitalize">{k.replace(/_/g, ' ')}</TableHead>)}
                                </TableRow></TableHeader>
                                <TableBody>
                                    {data.map((row, i) => (
                                        <TableRow key={i}>
                                            {Object.values(row).map((val, j) => (
                                                <TableCell key={j}>{typeof val === 'object' ? JSON.stringify(val) : val}</TableCell>
                                            ))}
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent></Card>
                    )}

                    {/* SPECIAL FORMATS */}
                    {activeTab === 'risk' && Array.isArray(data) && (
                        <div className="grid md:grid-cols-3 gap-4">
                            {data.map((d, i) => (
                                <Card key={i} className="border-l-4 border-red-500">
                                    <CardHeader className="pb-2"><CardTitle className="text-sm">{d.metric}</CardTitle></CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">{d.count}</div>
                                        <div className="text-xs text-muted-foreground">Saved: ${d.prevented_loss}</div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {activeTab === 'rg' && Array.isArray(data) && (
                        <div className="grid md:grid-cols-3 gap-4">
                            {data.map((d, i) => (
                                <Card key={i} className="border-l-4 border-green-500">
                                    <CardHeader className="pb-2"><CardTitle className="text-sm">{d.metric}</CardTitle></CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">{d.count}</div>
                                        <div className="text-xs text-muted-foreground">Trend: {d.trend}</div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {activeTab === 'kyc' && Array.isArray(data) && (
                        <div className="grid md:grid-cols-3 gap-4">
                            {data.map((d, i) => (
                                <Card key={i} className="border-l-4 border-blue-500">
                                    <CardHeader className="pb-2"><CardTitle className="text-sm">{d.status}</CardTitle></CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">{d.count}</div>
                                        <div className="text-xs text-muted-foreground">Avg Time: {d.avg_time}</div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {activeTab === 'operational' && Array.isArray(data) && (
                        <div className="grid md:grid-cols-4 gap-4">
                            {data.map((d, i) => (
                                <Card key={i}>
                                    <CardHeader className="pb-2"><CardTitle className="text-xs uppercase text-muted-foreground">{d.metric}</CardTitle></CardHeader>
                                    <CardContent><div className="text-xl font-bold">{d.value}</div></CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {/* PLACEHOLDERS */}
                    {activeTab === 'live' && <Card><CardContent className="p-10 text-center">Real-Time Dashboard (WebSocket Mock)</CardContent></Card>}
                    {activeTab === 'custom' && <Card><CardContent className="p-10 text-center">Drag & Drop Report Builder</CardContent></Card>}
                </>
            )}
        </ScrollArea>
    </div>
  );
};

export { Reports };
