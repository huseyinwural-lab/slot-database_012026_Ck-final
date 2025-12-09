import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Layout, File, Image, Menu, Globe, AlertTriangle, Plus, Eye } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

const CMSManagement = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [pages, setPages] = useState([]);
  const [banners, setBanners] = useState([]);
  const [menus, setMenus] = useState([]);
  
  // Create States
  const [isPageOpen, setIsPageOpen] = useState(false);
  const [newPage, setNewPage] = useState({ title: '', slug: '', template: 'static' });

  const fetchData = async () => {
    try {
        if (activeTab === 'dashboard') setDashboard((await api.get('/v1/cms/dashboard')).data);
        if (activeTab === 'pages') setPages((await api.get('/v1/cms/pages')).data);
        if (activeTab === 'banners') setBanners((await api.get('/v1/cms/banners')).data);
        if (activeTab === 'menus') setMenus((await api.get('/v1/cms/menus')).data);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  const handleCreatePage = async () => {
    try { await api.post('/v1/cms/pages', newPage); setIsPageOpen(false); fetchData(); toast.success("Page Created"); } catch { toast.error("Failed"); }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2"><Layout className="w-8 h-8 text-purple-600" /> CMS & Content</h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <ScrollArea className="w-full whitespace-nowrap rounded-md border">
                <TabsList className="w-full flex justify-start">
                    <TabsTrigger value="dashboard"><Activity className="w-4 h-4 mr-2" /> Overview</TabsTrigger>
                    <TabsTrigger value="pages"><File className="w-4 h-4 mr-2" /> Pages</TabsTrigger>
                    <TabsTrigger value="banners"><Image className="w-4 h-4 mr-2" /> Banners</TabsTrigger>
                    <TabsTrigger value="menus"><Menu className="w-4 h-4 mr-2" /> Navigation</TabsTrigger>
                    <TabsTrigger value="seo"><Globe className="w-4 h-4 mr-2" /> SEO</TabsTrigger>
                    <TabsTrigger value="maintenance"><AlertTriangle className="w-4 h-4 mr-2" /> System</TabsTrigger>
                </TabsList>
            </ScrollArea>

            {/* DASHBOARD */}
            <TabsContent value="dashboard" className="mt-4">
                {dashboard ? (
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Published Pages</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{dashboard.published_pages}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Banners</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{dashboard.active_banners}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Drafts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-500">{dashboard.draft_count}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Scheduled</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-500">{dashboard.scheduled_count}</div></CardContent></Card>
                    </div>
                ) : <div>Loading...</div>}
            </TabsContent>

            {/* PAGES */}
            <TabsContent value="pages" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isPageOpen} onOpenChange={setIsPageOpen}>
                        <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> New Page</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Create New Page</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Title</Label><Input value={newPage.title} onChange={e=>setNewPage({...newPage, title: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Slug (URL)</Label><Input value={newPage.slug} onChange={e=>setNewPage({...newPage, slug: e.target.value})} placeholder="/promos/..." /></div>
                                <div className="space-y-2"><Label>Template</Label>
                                    <Select value={newPage.template} onValueChange={v=>setNewPage({...newPage, template: v})}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="static">Static Content</SelectItem><SelectItem value="promo">Promotion</SelectItem><SelectItem value="landing">Landing Page</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleCreatePage} className="w-full">Create Draft</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Title</TableHead><TableHead>Slug</TableHead><TableHead>Template</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Action</TableHead></TableRow></TableHeader>
                        <TableBody>{pages.map(p => (
                            <TableRow key={p.id}>
                                <TableCell className="font-medium">{p.title}</TableCell>
                                <TableCell className="text-xs text-muted-foreground">{p.slug}</TableCell>
                                <TableCell className="capitalize">{p.template}</TableCell>
                                <TableCell><Badge variant={p.status==='published'?'default':'secondary'}>{p.status}</Badge></TableCell>
                                <TableCell className="text-right"><Button size="sm" variant="ghost"><Eye className="w-4 h-4" /></Button></TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* BANNERS */}
            <TabsContent value="banners" className="mt-4">
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Title</TableHead><TableHead>Position</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                        <TableBody>{banners.map(b => (
                            <TableRow key={b.id}>
                                <TableCell>{b.title}</TableCell>
                                <TableCell className="uppercase text-xs">{b.position}</TableCell>
                                <TableCell><Badge variant={b.status==='published'?'default':'outline'}>{b.status}</Badge></TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* MENUS */}
            <TabsContent value="menus" className="mt-4"><Card><CardContent className="p-10 text-center">Menu Editor (Mock)</CardContent></Card></TabsContent>
            <TabsContent value="seo" className="mt-4"><Card><CardContent className="p-10 text-center">SEO Tools (Mock)</CardContent></Card></TabsContent>
            <TabsContent value="maintenance" className="mt-4"><Card><CardContent className="p-10 text-center">System Messages (Mock)</CardContent></Card></TabsContent>
        </Tabs>
    </div>
  );
};

export { CMSManagement };
