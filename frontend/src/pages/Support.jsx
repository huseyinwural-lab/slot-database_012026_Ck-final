import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { MessageSquare, Mail, Book, Settings, Activity, User, Send, Plus, CheckCircle, Copy, Trash2 } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { clearLastError, getLastError } from '../services/supportDiagnostics';


const Support = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [tickets, setTickets] = useState([]);
  const [chats, setChats] = useState([]);
  const [kb, setKb] = useState([]);
  const [lastError, setLastErrorState] = useState(getLastError());

  const [canned, setCanned] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  
  // Ticket Reply
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [replyText, setReplyText] = useState("");

  const fetchData = async () => {
    try {
        if (activeTab === 'dashboard') setDashboard((await api.get('/v1/support/dashboard')).data);
        if (activeTab === 'inbox') setTickets((await api.get('/v1/support/tickets')).data);
        if (activeTab === 'chat') setChats((await api.get('/v1/support/chats')).data);
        if (activeTab === 'kb') setKb((await api.get('/v1/support/kb')).data);
        if (activeTab === 'settings') setCanned((await api.get('/v1/support/canned')).data);
    } catch (err) { console.error(err); }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    fetchData();
  };

  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === 'support_last_error') {
        setLastErrorState(getLastError());
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const handleReply = async () => {
    if (!selectedTicket || !replyText) return;
    try {
        await api.post(`/v1/support/tickets/${selectedTicket.id}/message`, {
            sender: "agent", content: replyText, time: new Date().toISOString()
        });
        toast.success("Reply Sent");
        setReplyText("");
        fetchData();
    } catch { toast.error("Failed"); }
  };

  const handleCreateCanned = async () => {
    try {
      await api.post('/v1/support/canned', { title: "New Response", content: "Text", category: "general" });
      fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Support Center</h2>
            <p className="text-sm text-muted-foreground">Diagnostics include the last captured Request ID for faster incident triage.</p>
          </div>
        </div>
        
        <Tabs value={activeTab} onValueChange={handleTabChange}>
            <TabsList className="grid grid-cols-5 w-full lg:w-[600px]">
                <TabsTrigger value="dashboard"><Activity className="w-4 h-4 mr-2" /> Overview</TabsTrigger>
                <TabsTrigger value="inbox"><Mail className="w-4 h-4 mr-2" /> Inbox</TabsTrigger>
                <TabsTrigger value="chat"><MessageSquare className="w-4 h-4 mr-2" /> Live Chat</TabsTrigger>
                <TabsTrigger value="kb"><Book className="w-4 h-4 mr-2" /> Help Center</TabsTrigger>
                <TabsTrigger value="settings"><Settings className="w-4 h-4 mr-2" /> Config</TabsTrigger>
            </TabsList>

            {/* DASHBOARD */}
            <TabsContent value="dashboard" className="mt-4">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-4">
                  <Card className="md:col-span-2">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Last Error (Diagnostics)</CardTitle>
                      <CardDescription>Share the Request ID with ops to locate correlated logs.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="text-sm">
                        <span className="font-medium">Request ID:</span>{' '}
                        <span className="font-mono">{lastError?.request_id || 'unavailable'}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {lastError?.status ? `Status: ${lastError.status}` : ''}{lastError?.message ? ` • ${lastError.message}` : ''}
                      </div>
                      <div className="flex gap-2 pt-1">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={!lastError?.request_id}
                          onClick={async () => {
                            try {
                              if (!lastError?.request_id) return;
                              await navigator.clipboard.writeText(lastError.request_id);
                              toast.success('Copied Request ID');
                            } catch (e) {
                              toast.error('Copy failed');
                            }
                          }}
                        >
                          <Copy className="w-4 h-4 mr-2" /> Copy
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            clearLastError();
                            setLastErrorState(null);
                            toast.success('Cleared');
                          }}
                        >
                          <Trash2 className="w-4 h-4 mr-2" /> Clear
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {dashboard ? (
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Open Tickets</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-500">{dashboard.open_tickets}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Active Chats</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-500">{dashboard.active_chats}</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">CSAT Score</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-500">{dashboard.csat_score}/5</div></CardContent></Card>
                        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Online Agents</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-500">{dashboard.agents_online}</div></CardContent></Card>
                    </div>
                ) : <div>Loading...</div>}
            </TabsContent>

            {/* INBOX */}
            <TabsContent value="inbox" className="mt-4">
                <div className="grid md:grid-cols-3 gap-6">
                    <Card className="md:col-span-1">
                        <CardHeader><CardTitle>Ticket Queue</CardTitle></CardHeader>
                        <ScrollArea className="h-[600px]">
                            <div className="space-y-2 p-4">
                                {tickets.map(t => (
                                    <div key={t.id} onClick={() => setSelectedTicket(t)} className={`p-3 border rounded cursor-pointer hover:bg-secondary/50 ${selectedTicket?.id === t.id ? 'border-primary bg-secondary/30' : ''}`}>
                                        <div className="flex justify-between items-start mb-1">
                                            <Badge variant="outline">{t.category}</Badge>
                                            <span className="text-xs text-muted-foreground">{new Date(t.created_at).toLocaleDateString()}</span>
                                        </div>
                                        <div className="font-bold text-sm truncate">{t.subject}</div>
                                        <div className="text-xs text-muted-foreground truncate">{t.player_email}</div>
                                    </div>
                                ))}
                            </div>
                        </ScrollArea>
                    </Card>
                    
                    <Card className="md:col-span-2 flex flex-col h-[700px]">
                        {selectedTicket ? (
                            <>
                                <CardHeader className="border-b bg-secondary/10">
                                    <div className="flex justify-between">
                                        <div>
                                            <CardTitle>{selectedTicket.subject}</CardTitle>
                                            <CardDescription>ID: {selectedTicket.id} • Player: {selectedTicket.player_email}</CardDescription>
                                        </div>
                                        <Badge className="h-fit">{selectedTicket.status}</Badge>
                                    </div>
                                </CardHeader>
                                <ScrollArea className="flex-1 p-4">
                                    <div className="space-y-4">
                                        <div className="bg-secondary/20 p-3 rounded-lg mr-10">
                                            <div className="font-bold text-xs mb-1">Player</div>
                                            {selectedTicket.description}
                                        </div>
                                        {selectedTicket.messages?.map((m, i) => (
                                            <div key={i} className={`p-3 rounded-lg ${m.sender === 'agent' ? 'ml-10 bg-primary/10' : 'mr-10 bg-secondary/20'}`}>
                                                <div className="font-bold text-xs mb-1 capitalize">{m.sender}</div>
                                                {m.content}
                                            </div>
                                        ))}
                                    </div>
                                </ScrollArea>
                                <div className="p-4 border-t bg-background">
                                    <Textarea value={replyText} onChange={e => setReplyText(e.target.value)} placeholder="Type reply..." className="mb-2" />
                                    <div className="flex justify-end gap-2">
                                        <Button variant="outline" size="sm">Canned Response</Button>
                                        <Button size="sm" onClick={handleReply}><Send className="w-4 h-4 mr-2" /> Reply</Button>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="flex items-center justify-center h-full text-muted-foreground">Select a ticket</div>
                        )}
                    </Card>
                </div>
            </TabsContent>

            {/* CHAT */}
            <TabsContent value="chat" className="mt-4">
                <Card>
                    <CardContent className="p-10 text-center text-muted-foreground">
                        <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <h3 className="text-lg font-medium">Live Chat Console</h3>
                        <p>No active sessions. Waiting for players...</p>
                        <Button className="mt-4" onClick={() => toast.info("Simulated Chat Request")}>Simulate Incoming Chat</Button>
                    </CardContent>
                </Card>
            </TabsContent>

            {/* KB */}
            <TabsContent value="kb" className="mt-4">
                <Card>
                    <CardHeader><CardTitle>Knowledge Base</CardTitle></CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader><TableRow><TableHead>Title</TableHead><TableHead>Category</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                            <TableBody>{kb.map(k => (
                                <TableRow key={k.id}>
                                    <TableCell className="font-medium">{k.title}</TableCell>
                                    <TableCell>{k.category}</TableCell>
                                    <TableCell><Badge variant="outline">{k.status}</Badge></TableCell>
                                </TableRow>
                            ))}</TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </TabsContent>

            {/* SETTINGS */}
            <TabsContent value="settings" className="mt-4">
                <div className="grid md:grid-cols-2 gap-6">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle>Canned Responses</CardTitle>
                            <Button size="sm" variant="ghost" onClick={handleCreateCanned}><Plus className="w-4 h-4" /></Button>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                {canned.map(c => (
                                    <div key={c.id} className="p-2 border rounded text-sm">
                                        <div className="font-bold">{c.title}</div>
                                        <div className="text-xs text-muted-foreground truncate">{c.content}</div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader><CardTitle>Automation Rules</CardTitle></CardHeader>
                        <CardContent className="text-sm text-muted-foreground">
                            Configure auto-responders and ticket routing logic here.
                        </CardContent>
                    </Card>
                </div>
            </TabsContent>
        </Tabs>
    </div>
  );
};

export default Support;
