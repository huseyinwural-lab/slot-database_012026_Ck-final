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
import { Shield, User, Users, Lock, Key, Mail, History, Plus, Settings } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

const AdminManagement = () => {
  const [activeTab, setActiveTab] = useState("users");
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [teams, setTeams] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [invites, setInvites] = useState([]);
  const [keys, setKeys] = useState([]);
  const [policy, setPolicy] = useState(null);
  
  // Create States
  const [isUserOpen, setIsUserOpen] = useState(false);
  const [newUser, setNewUser] = useState({ full_name: '', email: '', role: 'support' });

  const fetchData = async () => {
    try {
        if (activeTab === 'users') setUsers((await api.get('/v1/admin/users')).data);
        if (activeTab === 'roles') setRoles((await api.get('/v1/admin/roles')).data);
        if (activeTab === 'teams') setTeams((await api.get('/v1/admin/teams')).data);
        if (activeTab === 'sessions') setSessions((await api.get('/v1/admin/sessions')).data);
        if (activeTab === 'invites') setInvites((await api.get('/v1/admin/invites')).data);
        if (activeTab === 'keys') setKeys((await api.get('/v1/admin/keys')).data);
        if (activeTab === 'security') setPolicy((await api.get('/v1/admin/security')).data);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  const handleCreateUser = async () => {
    try { await api.post('/v1/admin/users', { ...newUser, username: newUser.email.split('@')[0] }); setIsUserOpen(false); fetchData(); toast.success("User Created"); } catch { toast.error("Failed"); }
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2"><Shield className="w-8 h-8 text-blue-600" /> Admin & Security</h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <ScrollArea className="w-full whitespace-nowrap rounded-md border">
                <TabsList className="w-full flex justify-start">
                    <TabsTrigger value="users"><User className="w-4 h-4 mr-2" /> Admins</TabsTrigger>
                    <TabsTrigger value="roles"><Settings className="w-4 h-4 mr-2" /> Roles</TabsTrigger>
                    <TabsTrigger value="teams"><Users className="w-4 h-4 mr-2" /> Teams</TabsTrigger>
                    <TabsTrigger value="security"><Lock className="w-4 h-4 mr-2" /> Security</TabsTrigger>
                    <TabsTrigger value="sessions"><History className="w-4 h-4 mr-2" /> Sessions</TabsTrigger>
                    <TabsTrigger value="invites"><Mail className="w-4 h-4 mr-2" /> Invites</TabsTrigger>
                    <TabsTrigger value="keys"><Key className="w-4 h-4 mr-2" /> API Keys</TabsTrigger>
                </TabsList>
            </ScrollArea>

            {/* USERS */}
            <TabsContent value="users" className="mt-4">
                <div className="flex justify-end mb-4">
                    <Dialog open={isUserOpen} onOpenChange={setIsUserOpen}>
                        <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add Admin</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>New Admin User</DialogTitle></DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2"><Label>Full Name</Label><Input value={newUser.full_name} onChange={e=>setNewUser({...newUser, full_name: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Email</Label><Input value={newUser.email} onChange={e=>setNewUser({...newUser, email: e.target.value})} /></div>
                                <div className="space-y-2"><Label>Role</Label>
                                    <Select value={newUser.role} onValueChange={v=>setNewUser({...newUser, role: v})}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent><SelectItem value="support">Support</SelectItem><SelectItem value="manager">Manager</SelectItem><SelectItem value="admin">Super Admin</SelectItem></SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleCreateUser} className="w-full">Create</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Email</TableHead><TableHead>Role</TableHead><TableHead>Status</TableHead><TableHead>2FA</TableHead></TableRow></TableHeader>
                        <TableBody>{users.map(u => (
                            <TableRow key={u.id}>
                                <TableCell>{u.full_name}</TableCell>
                                <TableCell>{u.email}</TableCell>
                                <TableCell className="capitalize">{u.role}</TableCell>
                                <TableCell><Badge variant={u.status==='active'?'default':'secondary'}>{u.status}</Badge></TableCell>
                                <TableCell>{u.is_2fa_enabled ? <CheckCircle className="w-4 h-4 text-green-500" /> : <span className="text-muted-foreground">-</span>}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* ROLES */}
            <TabsContent value="roles" className="mt-4">
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Role Name</TableHead><TableHead>Description</TableHead><TableHead>Users</TableHead></TableRow></TableHeader>
                        <TableBody>{roles.map(r => (
                            <TableRow key={r.id}>
                                <TableCell className="font-bold">{r.name}</TableCell>
                                <TableCell>{r.description}</TableCell>
                                <TableCell>{r.user_count}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* TEAMS */}
            <TabsContent value="teams" className="mt-4"><Card><CardContent className="p-10 text-center">Teams Management (Mock)</CardContent></Card></TabsContent>
            
            {/* SESSIONS */}
            <TabsContent value="sessions" className="mt-4"><Card><CardContent className="p-10 text-center">Active Sessions (Mock)</CardContent></Card></TabsContent>
            
            {/* INVITES */}
            <TabsContent value="invites" className="mt-4"><Card><CardContent className="p-10 text-center">Invite Management (Mock)</CardContent></Card></TabsContent>
            
            {/* KEYS */}
            <TabsContent value="keys" className="mt-4"><Card><CardContent className="p-10 text-center">API Keys (Mock)</CardContent></Card></TabsContent>
            
            {/* SECURITY */}
            <TabsContent value="security" className="mt-4">
                {policy && (
                    <Card>
                        <CardHeader><CardTitle>Security Policy</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div><Label>Min Password Length</Label><Input value={policy.password_min_length} readOnly /></div>
                                <div><Label>Session Timeout (min)</Label><Input value={policy.session_timeout_minutes} readOnly /></div>
                                <div><Label>Max Login Attempts</Label><Input value={policy.max_login_attempts} readOnly /></div>
                                <div className="flex items-center gap-2 pt-6"><input type="checkbox" checked={policy.require_2fa} readOnly /> <Label>Require 2FA</Label></div>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </TabsContent>
        </Tabs>
    </div>
  );
};

// Missing CheckCircle import fix
const CheckCircle = (props) => <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>;

export { AdminManagement };
