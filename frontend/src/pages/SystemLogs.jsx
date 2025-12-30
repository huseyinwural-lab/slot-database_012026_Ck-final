import React, { useCallback, useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
    Activity, Clock, Server, Package, Settings, AlertOctagon, Mail, Database, Zap, Archive, Link
} from 'lucide-react';

const NavButton = ({ tab, icon: Icon, label, activeTab, setActiveTab }) => (
    <Button 
        variant={activeTab===tab ? 'secondary' : 'ghost'} 
        className="w-full justify-start text-sm" 
        onClick={()=>setActiveTab(tab)}
    >
        <Icon className="w-4 h-4 mr-2" /> {label}
    </Button>
);
const SystemLogs = () => {
  const [activeTab, setActiveTab] = useState("events");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      let endpoint = '/v1/logs/events';
      if (activeTab === 'cron') endpoint = '/v1/logs/cron';
      if (activeTab === 'health') endpoint = '/v1/logs/health';
      if (activeTab === 'deployments') endpoint = '/v1/logs/deployments';
      if (activeTab === 'config') endpoint = '/v1/logs/config';
      if (activeTab === 'errors') endpoint = '/v1/logs/errors';
      if (activeTab === 'queues') endpoint = '/v1/logs/queues';
      if (activeTab === 'db') endpoint = '/v1/logs/db';
      if (activeTab === 'cache') endpoint = '/v1/logs/cache';
      if (activeTab === 'archive') endpoint = '/v1/logs/archive';

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

  const runCron = async () => {
    try { await api.post('/v1/logs/cron/run', { job_name: "manual_trigger" }); toast.success("Job Started"); fetchData(); } catch { toast.error("Failed"); }
  };

  return (
    <div className="flex h-[calc(100vh-100px)]">
        {/* SIDEBAR NAVIGATION */}
        <div className="w-64 border-r bg-card p-2 flex flex-col h-full">
            <h3 className="font-bold mb-2 px-4 flex items-center gap-2"><Server className="w-5 h-5 text-primary" /> System Logs</h3>
            <ScrollArea className="flex-1 pr-2">
                <div className="space-y-1">
                    <NavButton tab="events" icon={Activity} label="System Events" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="cron" icon={Clock} label="Cron Jobs" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="health" icon={Zap} label="Service Health" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="deployments" icon={Package} label="Deployments" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="config" icon={Settings} label="Config Changes" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="errors" icon={AlertOctagon} label="Error Logs" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="queues" icon={Mail} label="Queue / Workers" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="db" icon={Database} label="Database Logs" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="cache" icon={Zap} label="Cache Logs" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="archive" icon={Archive} label="Log Archive" activeTab={activeTab} setActiveTab={setActiveTab} />
                    <NavButton tab="trace" icon={Link} label="Trace View" activeTab={activeTab} setActiveTab={setActiveTab} />
                </div>
            </ScrollArea>
        </div>

        {/* CONTENT AREA */}
        <ScrollArea className="flex-1 p-6 bg-secondary/5">
            {loading ? <div className="text-center p-10">Loading...</div> : (
                <>
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-2xl font-bold capitalize">{activeTab.replace('_', ' ')}</h2>
                        {activeTab === 'cron' && <Button onClick={runCron}>Run Job</Button>}
                    </div>

                    {/* GENERIC TABLE RENDERER */}
                    {Array.isArray(data) && data.length > 0 ? (
                        <Card><CardContent className="pt-6">
                            <Table>
                                <TableHeader><TableRow>
                                    {Object.keys(data[0] || {}).map(k => <TableHead key={k} className="capitalize">{k.replace(/_/g, ' ')}</TableHead>)}
                                </TableRow></TableHeader>
                                <TableBody>
                                    {data.map((row, i) => (
                                        <TableRow key={i}>
                                            {Object.values(row).map((val, j) => (
                                                <TableCell key={j} className="max-w-xs truncate">
                                                    {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                                                </TableCell>
                                            ))}
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent></Card>
                    ) : (
                        <div className="text-center p-10 text-muted-foreground border border-dashed rounded-lg">
                            No logs found for this category.
                        </div>
                    )}

                    {activeTab === 'trace' && <Card><CardContent className="p-10 text-center">Distributed Tracing Visualization (Coming Soon)</CardContent></Card>}
                </>
            )}
        </ScrollArea>
    </div>
  );
};

export { SystemLogs };
