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
import { 
  Shield, User, Users, Lock, Key, Mail, History, Plus, Settings, 
  FileText, Grid3x3, Globe, Smartphone, AlertTriangle, UserPlus,
  CheckCircle, XCircle, Eye, Download, Filter, Search, Calendar
} from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';

const AdminManagement = () => {
  const [activeTab, setActiveTab] = useState("users");
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [teams, setTeams] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [invites, setInvites] = useState([]);
  const [keys, setKeys] = useState([]);
  const [policy, setPolicy] = useState(null);
  
  // NEW: Critical Features
  const [activityLogs, setActivityLogs] = useState([]);
  const [loginHistory, setLoginHistory] = useState([]);
  const [permissionMatrix, setPermissionMatrix] = useState([]);
  const [ipRestrictions, setIpRestrictions] = useState([]);
  const [deviceRestrictions, setDeviceRestrictions] = useState([]);
  
  // Create States
  const [isUserOpen, setIsUserOpen] = useState(false);
  const [newUser, setNewUser] = useState({ full_name: '', email: '', role: '', allowed_modules: [], password_mode: 'manual', password: '' });
  const [isIPDialogOpen, setIsIPDialogOpen] = useState(false);
  const [newIP, setNewIP] = useState({ ip_address: '', restriction_type: 'allowed', reason: '' });
  
  // Filters
  const [activityFilter, setActivityFilter] = useState({ admin_id: '', module: '', action: '' });
  const [loginFilter, setLoginFilter] = useState({ admin_id: '', result: '', suspicious_only: false });

  const fetchData = async () => {
    try {
        if (activeTab === 'users') setUsers((await api.get('/v1/admin/users')).data);
        if (activeTab === 'roles') setRoles((await api.get('/v1/admin/roles')).data);
        if (activeTab === 'teams') setTeams((await api.get('/v1/admin/teams')).data);
        if (activeTab === 'sessions') setSessions((await api.get('/v1/admin/sessions')).data);
        if (activeTab === 'invites') setInvites((await api.get('/v1/admin/invites')).data);
        if (activeTab === 'keys') setKeys((await api.get('/v1/admin/keys')).data);
        if (activeTab === 'security') setPolicy((await api.get('/v1/admin/security')).data);
        
        // NEW: Fetch critical features
        if (activeTab === 'activity-log') {
          const params = new URLSearchParams();
          if (activityFilter.admin_id) params.append('admin_id', activityFilter.admin_id);
          if (activityFilter.module) params.append('module', activityFilter.module);
          if (activityFilter.action) params.append('action', activityFilter.action);
          setActivityLogs((await api.get(`/v1/admin/activity-log?${params}`)).data);
        }
        
        if (activeTab === 'login-history') {
          const params = new URLSearchParams();
          if (loginFilter.admin_id) params.append('admin_id', loginFilter.admin_id);
          if (loginFilter.result) params.append('result', loginFilter.result);
          if (loginFilter.suspicious_only) params.append('suspicious_only', 'true');
          setLoginHistory((await api.get(`/v1/admin/login-history?${params}`)).data);
        }
        
        if (activeTab === 'permission-matrix') {
          setPermissionMatrix((await api.get('/v1/admin/permission-matrix')).data);
        }
        
        if (activeTab === 'ip-device') {
          setIpRestrictions((await api.get('/v1/admin/ip-restrictions')).data);
          setDeviceRestrictions((await api.get('/v1/admin/device-restrictions')).data);
        }
        
    } catch (err) { console.error(err); toast.error('Failed to load data'); }
  };

  useEffect(() => { fetchData(); }, [activeTab, activityFilter, loginFilter]);

  const handleCreateUser = async () => {
    try {
      if (!newUser.full_name || !newUser.email) {
        toast.error('Full name and email are required');
        return;
      }
      if (newUser.password_mode === 'manual' && !newUser.password) {
        toast.error('Password is required in manual mode');
        return;
      }
      const baseModules = ['players', 'games', 'bonuses', 'reports', 'fraud', 'settings'];
      let allowedModules = [...newUser.allowed_modules];

      if (newUser.role === 'Super Admin') {
        // Süper Admin her şeye erişir
        allowedModules = baseModules;
      } else if (newUser.role === 'Manager') {
        // Manager can access everything except critical areas (fraud, settings)
        allowedModules = baseModules.filter(m => !['fraud', 'settings'].includes(m));
      }

      await api.post('/v1/admin/users', {
        full_name: newUser.full_name,
        email: newUser.email,
        role: newUser.role || 'Admin',
        allowed_modules: allowedModules,
        password_mode: newUser.password_mode,
        password: newUser.password_mode === 'manual' ? newUser.password : undefined,
      });
      setIsUserOpen(false);
      setNewUser({ full_name: '', email: '', role: '', allowed_modules: [], password_mode: 'manual', password: '' });
      fetchData();
      toast.success('Admin user created');
    } catch (err) {
      console.error(err);
      toast.error('Operation failed');
    }
  };
  
  const handleAddIPRestriction = async () => {
    try {
      await api.post('/v1/admin/ip-restrictions', {
        ...newIP,
        added_by: 'current_admin',
        is_active: true
      });
      setIsIPDialogOpen(false);
      setNewIP({ ip_address: '', restriction_type: 'allowed', reason: '' });
      fetchData();
      toast.success('IP restriction added');
    } catch { toast.error('Başarısız'); }
  };
  
  const handleApproveDevice = async (deviceId) => {
    try {
      await api.put(`/v1/admin/device-restrictions/${deviceId}/approve`, { approved_by: 'current_admin' });
      fetchData();
      toast.success('Device approved');
    } catch { toast.error('Başarısız'); }
  };
  
  const handleExportLogs = (data, filename) => {
    const csv = [
      Object.keys(data[0] || {}).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    toast.success('Export successful');
  };

  return (
    <div className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Shield className="w-8 h-8 text-blue-600" /> Admin & Security Management
        </h2>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
            <ScrollArea className="w-full whitespace-nowrap rounded-md border">
                <TabsList className="w-full flex justify-start">
                    <TabsTrigger value="users"><User className="w-4 h-4 mr-2" /> Admin Users</TabsTrigger>
                    <TabsTrigger value="roles"><Settings className="w-4 h-4 mr-2" /> Roles</TabsTrigger>
                    <TabsTrigger value="teams"><Users className="w-4 h-4 mr-2" /> Teams</TabsTrigger>
                    <TabsTrigger value="activity-log"><FileText className="w-4 h-4 mr-2" /> 📜 Activity Log</TabsTrigger>
                    <TabsTrigger value="permission-matrix"><Grid3x3 className="w-4 h-4 mr-2" /> 🧩 Permission Matrix</TabsTrigger>
                    <TabsTrigger value="ip-device"><Globe className="w-4 h-4 mr-2" /> 🛡️ IP & Devices</TabsTrigger>
                    <TabsTrigger value="login-history"><History className="w-4 h-4 mr-2" /> 🔑 Login History</TabsTrigger>
                    <TabsTrigger value="security"><Lock className="w-4 h-4 mr-2" /> Security</TabsTrigger>
                    <TabsTrigger value="sessions"><Calendar className="w-4 h-4 mr-2" /> Sessions</TabsTrigger>
                    <TabsTrigger value="invites"><Mail className="w-4 h-4 mr-2" /> Invites</TabsTrigger>
                    <TabsTrigger value="keys"><Key className="w-4 h-4 mr-2" /> API Keys</TabsTrigger>
                    <TabsTrigger value="risk-score"><AlertTriangle className="w-4 h-4 mr-2" /> 🟩 Risk Score</TabsTrigger>
                    <TabsTrigger value="delegation"><UserPlus className="w-4 h-4 mr-2" /> 🟩 Delegation</TabsTrigger>
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
                                <div className="space-y-2">
                                  <Label>Role</Label>
                                  <div className="grid grid-cols-3 gap-2 text-sm">
                                    {['Super Admin', 'Manager', 'Admin'].map(roleOpt => (
                                      <button
                                        key={roleOpt}
                                        type="button"
                                        onClick={() => setNewUser({ ...newUser, role: roleOpt })}
                                        className={`rounded border px-3 py-2 text-xs ${
                                          newUser.role === roleOpt
                                            ? 'bg-primary text-primary-foreground border-primary'
                                            : 'hover:bg-secondary'
                                        }`}
                                      >
                                        {roleOpt}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                                <div className="space-y-2">
                                  <Label>Permission Scopes (modules)</Label>
                                  <div className="grid grid-cols-2 gap-2 text-sm">
                                    {[
                                      { key: 'players', label: 'Players' },
                                      { key: 'games', label: 'Games' },
                                      { key: 'bonuses', label: 'Bonuses' },
                                      { key: 'reports', label: 'Reports' },
                                      { key: 'fraud', label: 'Fraud / Risk' },
                                      { key: 'settings', label: 'Settings' },
                                    ].map(mod => {
                                      // Rol bazlı otomatik seçim mantığı
                                      let forced = false;
                                      if (newUser.role === 'Super Admin') {
                                        forced = true;
                                      } else if (newUser.role === 'Manager') {
                                        // Manager kritik alanlar dışında erişsin: Fraud ve Settings hariç hepsine erişsin
                                        if (!['fraud', 'settings'].includes(mod.key)) {
                                          forced = true;
                                        }
                                      }

                                      const checked = forced || newUser.allowed_modules.includes(mod.key);
                                      const toggle = () => {
                                        if (forced) return; // Super Admin / Manager için zorunlu alanlar değiştirilemez
                                        setNewUser({
                                          ...newUser,
                                          allowed_modules: checked
                                            ? newUser.allowed_modules.filter(m => m !== mod.key)
                                            : [...newUser.allowed_modules, mod.key],
                                        });
                                      };

                                      return (
                                        <button
                                          key={mod.key}
                                          type="button"
                                          onClick={toggle}
                                          className={`flex items-center justify-between rounded border px-3 py-2 text-xs ${
                                            checked ? 'bg-primary text-primary-foreground border-primary' : 'hover:bg-secondary'
                                          } ${forced ? 'cursor-not-allowed opacity-80' : ''}`}
                                        >
                                          <span>{mod.label}</span>
                                          {checked && <span>✓</span>}
                                        </button>
                                      );
                                    })}
                                  </div>
                                </div>
                                <div className="space-y-2">
                                  <Label>Password Mode</Label>
                                  <div className="flex gap-2 text-sm">
                                    <button
                                      type="button"
                                      className={`flex-1 rounded border px-3 py-2 ${
                                        newUser.password_mode === 'manual'
                                          ? 'bg-primary text-primary-foreground border-primary'
                                          : 'hover:bg-secondary'
                                      }`}
                                      onClick={() => setNewUser({ ...newUser, password_mode: 'manual' })}
                                    >
                                      Set Password Manually
                                    </button>
                                    <button
                                      type="button"
                                      className={`flex-1 rounded border px-3 py-2 ${
                                        newUser.password_mode === 'invite'
                                          ? 'bg-primary text-primary-foreground border-primary'
                                          : 'hover:bg-secondary'
                                      }`}
                                      onClick={() => setNewUser({ ...newUser, password_mode: 'invite', password: '' })}
                                    >
                                      Invite Link / First Login Password
                                    </button>
                                  </div>
                                </div>
                                {newUser.password_mode === 'manual' && (
                                  <div className="space-y-2">
                                    <Label>Password (must satisfy policy)</Label>
                                    <Input
                                      type="password"
                                      placeholder="At least 8 chars, incl. uppercase, number and special character"
                                      value={newUser.password}
                                      onChange={e => setNewUser({ ...newUser, password: e.target.value })}
                                    />
                                  </div>
                                )}
                                <Button onClick={handleCreateUser} className="w-full">Create</Button>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Ad</TableHead><TableHead>Email</TableHead><TableHead>Rol</TableHead><TableHead>Status</TableHead><TableHead>2FA</TableHead></TableRow></TableHeader>
                        <TableBody>{users.map(u => (
                            <TableRow key={u.id}>
                                <TableCell>{u.full_name}</TableCell>
                                <TableCell>{u.email}</TableCell>
                                <TableCell className="capitalize">{u.role}</TableCell>
                                <TableCell><Badge variant={u.status==='active'?'default':'secondary'}>{u.status}</Badge></TableCell>
                                <TableCell>{u.is_2fa_enabled ? <CheckCircle className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-gray-400" />}</TableCell>
                            </TableRow>
                        ))}</TableBody>
                    </Table>
                </CardContent></Card>
            </TabsContent>

            {/* ROLES */}
            <TabsContent value="roles" className="mt-4">
                <Card><CardContent className="pt-6">
                    <Table>
                        <TableHeader><TableRow><TableHead>Role Name</TableHead><TableHead>Description</TableHead><TableHead>User Count</TableHead></TableRow></TableHeader>
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
            <TabsContent value="teams" className="mt-4">
              <Card><CardContent className="p-10 text-center text-muted-foreground">Team management (under development)</CardContent></Card>
            </TabsContent>
            
            {/* 📜 ACTIVITY LOG - ZORUNLU 1 */}
            <TabsContent value="activity-log" className="mt-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">📜 Admin Activity Log (Audit)</CardTitle>
                      <CardDescription>All admin actions are recorded here for auditing</CardDescription>
                    </div>
                    <Button onClick={() => handleExportLogs(activityLogs, 'activity_log.csv')}>
                      <Download className="w-4 h-4 mr-2" /> CSV Export
                    </Button>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Filters */}
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Filter by admin</Label>
                        <Input placeholder="Admin ID" value={activityFilter.admin_id} onChange={e => setActivityFilter({...activityFilter, admin_id: e.target.value})} />
                      </div>
                      <div>
                        <Label>Module</Label>
                        <Select value={activityFilter.module || "all"} onValueChange={v => setActivityFilter({...activityFilter, module: v === "all" ? "" : v})}>
                          <SelectTrigger><SelectValue placeholder="All" /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All</SelectItem>
                            <SelectItem value="players">Players</SelectItem>
                            <SelectItem value="finance">Finance</SelectItem>
                            <SelectItem value="games">Games</SelectItem>
                            <SelectItem value="bonuses">Bonuses</SelectItem>
                            <SelectItem value="cms">CMS</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>Action Type</Label>
                        <Input placeholder="Action" value={activityFilter.action} onChange={e => setActivityFilter({...activityFilter, action: e.target.value})} />
                      </div>
                    </div>
                    
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Admin</TableHead>
                          <TableHead>Action</TableHead>
                          <TableHead>Module</TableHead>
                          <TableHead>IP Address</TableHead>
                          <TableHead>Time</TableHead>
                          <TableHead>Risk</TableHead>
                          <TableHead></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {activityLogs.map(log => (
                          <TableRow key={log.id}>
                            <TableCell className="font-medium">{log.admin_name}</TableCell>
                            <TableCell>{log.action}</TableCell>
                            <TableCell><Badge variant="outline">{log.module}</Badge></TableCell>
                            <TableCell className="text-xs text-muted-foreground">{log.ip_address}</TableCell>
                            <TableCell className="text-xs">{new Date(log.timestamp).toLocaleString('tr-TR')}</TableCell>
                            <TableCell>
                              <Badge variant={log.risk_level === 'critical' ? 'destructive' : log.risk_level === 'high' ? 'destructive' : 'secondary'}>
                                {log.risk_level}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Dialog>
                                <DialogTrigger asChild>
                                  <Button variant="ghost" size="sm"><Eye className="w-4 h-4" /></Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-2xl">
                                  <DialogHeader><DialogTitle>Log Detail</DialogTitle></DialogHeader>
                                  <div className="space-y-4">
                                    <div><Label>Admin</Label><p>{log.admin_name} ({log.admin_id})</p></div>
                                    <div><Label>Action</Label><p>{log.action}</p></div>
                                    <div><Label>Before Snapshot</Label><pre className="bg-gray-100 p-2 rounded text-xs overflow-auto max-h-40">{JSON.stringify(log.before_snapshot, null, 2)}</pre></div>
                                    <div><Label>After Snapshot</Label><pre className="bg-gray-100 p-2 rounded text-xs overflow-auto max-h-40">{JSON.stringify(log.after_snapshot, null, 2)}</pre></div>
                                  </div>
                                </DialogContent>
                              </Dialog>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    {activityLogs.length === 0 && <p className="text-center text-muted-foreground py-8">Henüz aktivite kaydı yok</p>}
                  </CardContent>
                </Card>
            </TabsContent>

            {/* 🧩 PERMISSION MATRIX - ZORUNLU 2 */}
            <TabsContent value="permission-matrix" className="mt-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">🧩 Permission Matrix</CardTitle>
                      <CardDescription>Role-based authorization map - see which role can access which module at a glance</CardDescription>
                    </div>
                    <Button onClick={() => handleExportLogs(permissionMatrix, 'permission_matrix.csv')}>
                      <Download className="w-4 h-4 mr-2" /> Matrix Export
                    </Button>
                  </CardHeader>
                  <CardContent>
                    {roles.length > 0 ? (
                      <div className="space-y-6">
                        {roles.map(role => {
                          const rolePerms = permissionMatrix.filter(m => m.role_id === role.id);
                          return (
                            <div key={role.id} className="border rounded-lg p-4">
                              <h3 className="text-lg font-bold mb-4">{role.name}</h3>
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    <TableHead>Module</TableHead>
                                    <TableHead className="text-center">Read</TableHead>
                                    <TableHead className="text-center">Write</TableHead>
                                    <TableHead className="text-center">Approve</TableHead>
                                    <TableHead className="text-center">Export</TableHead>
                                    <TableHead className="text-center">Restricted</TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {rolePerms.map(perm => (
                                    <TableRow key={perm.id}>
                                      <TableCell className="font-medium capitalize">{perm.module}</TableCell>
                                      <TableCell className="text-center">{perm.permissions.read ? <CheckCircle className="w-4 h-4 text-green-500 mx-auto" /> : <XCircle className="w-4 h-4 text-gray-300 mx-auto" />}</TableCell>
                                      <TableCell className="text-center">{perm.permissions.write ? <CheckCircle className="w-4 h-4 text-green-500 mx-auto" /> : <XCircle className="w-4 h-4 text-gray-300 mx-auto" />}</TableCell>
                                      <TableCell className="text-center">{perm.permissions.approve ? <CheckCircle className="w-4 h-4 text-green-500 mx-auto" /> : <XCircle className="w-4 h-4 text-gray-300 mx-auto" />}</TableCell>
                                      <TableCell className="text-center">{perm.permissions.export ? <CheckCircle className="w-4 h-4 text-green-500 mx-auto" /> : <XCircle className="w-4 h-4 text-gray-300 mx-auto" />}</TableCell>
                                      <TableCell className="text-center">{perm.permissions.restricted ? <CheckCircle className="w-4 h-4 text-red-500 mx-auto" /> : <XCircle className="w-4 h-4 text-gray-300 mx-auto" />}</TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-center text-muted-foreground py-8">Rol bulunamadı. Önce rol oluşturun.</p>
                    )}
                  </CardContent>
                </Card>
            </TabsContent>

            {/* 🛡️ IP & DEVICE RESTRICTIONS - ZORUNLU 3 */}
            <TabsContent value="ip-device" className="mt-4">
                <div className="grid gap-6">
                  {/* IP Restrictions */}
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                      <div>
                        <CardTitle className="flex items-center gap-2">🛡️ IP Restrictions</CardTitle>
                        <CardDescription>Manage IP whitelist and blacklist for admin users</CardDescription>
                      </div>
                      <Dialog open={isIPDialogOpen} onOpenChange={setIsIPDialogOpen}>
                        <DialogTrigger asChild><Button><Plus className="w-4 h-4 mr-2" /> Add IP</Button></DialogTrigger>
                        <DialogContent>
                          <DialogHeader><DialogTitle>New IP Restriction</DialogTitle></DialogHeader>
                          <div className="space-y-4 py-4">
                            <div className="space-y-2">
                              <Label>IP Address</Label>
                              <Input placeholder="192.168.1.1" value={newIP.ip_address} onChange={e=>setNewIP({...newIP, ip_address: e.target.value})} />
                            </div>
                            <div className="space-y-2">
                              <Label>Type</Label>
                              <Select value={newIP.restriction_type} onValueChange={v=>setNewIP({...newIP, restriction_type: v})}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="allowed">✅ Allowed (Whitelist)</SelectItem>
                                  <SelectItem value="blocked">🚫 Blocked (Blacklist)</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="space-y-2">
                              <Label>Reason</Label>
                              <Textarea placeholder="Why is this being added?" value={newIP.reason} onChange={e=>setNewIP({...newIP, reason: e.target.value})} />
                            </div>
                            <Button onClick={handleAddIPRestriction} className="w-full">Add</Button>
                          </div>
                        </DialogContent>
                      </Dialog>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>IP Address</TableHead>
                            <TableHead>Tip</TableHead>
                            <TableHead>Reason</TableHead>
                            <TableHead>Added By</TableHead>
                            <TableHead>Date</TableHead>
                            <TableHead></TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {ipRestrictions.map(ip => (
                            <TableRow key={ip.id}>
                              <TableCell className="font-mono">{ip.ip_address}</TableCell>
                              <TableCell>
                                <Badge variant={ip.restriction_type === 'allowed' ? 'default' : 'destructive'}>
                                  {ip.restriction_type === 'allowed' ? '✅ Allowed' : '🚫 Blocked'}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-xs text-muted-foreground">{ip.reason || '-'}</TableCell>
                              <TableCell className="text-xs">{ip.added_by}</TableCell>
                              <TableCell className="text-xs">{new Date(ip.added_at).toLocaleDateString('tr-TR')}</TableCell>
                              <TableCell>
                                <Button variant="ghost" size="sm" className="text-red-600">Remove</Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      {ipRestrictions.length === 0 && <p className="text-center text-muted-foreground py-8">No IP restrictions yet.</p>}
                    </CardContent>
                  </Card>

                  {/* Device Restrictions */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">📱 Device Management</CardTitle>
                      <CardDescription>Manage device approvals and restrictions for admin users</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Admin</TableHead>
                            <TableHead>Cihaz</TableHead>
                            <TableHead>Tip</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Son Görülme</TableHead>
                            <TableHead></TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {deviceRestrictions.map(device => (
                            <TableRow key={device.id}>
                              <TableCell>{device.admin_id}</TableCell>
                              <TableCell>
                                <div>
                                  <p className="font-medium">{device.device_name || 'Unknown Device'}</p>
                                  <p className="text-xs text-muted-foreground">{device.browser_info}</p>
                                </div>
                              </TableCell>
                              <TableCell><Badge variant="outline">{device.device_type || 'unknown'}</Badge></TableCell>
                              <TableCell>
                                <Badge variant={
                                  device.status === 'approved' ? 'default' : 
                                  device.status === 'blocked' ? 'destructive' : 
                                  'secondary'
                                }>
                                  {device.status}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-xs">{new Date(device.last_seen).toLocaleString('tr-TR')}</TableCell>
                              <TableCell>
                                {device.status === 'pending' && (
                                  <Button size="sm" onClick={() => handleApproveDevice(device.id)}>
                                    <CheckCircle className="w-4 h-4 mr-1" /> Approve
                                  </Button>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      {deviceRestrictions.length === 0 && <p className="text-center text-muted-foreground py-8">No device records yet.</p>}
                    </CardContent>
                  </Card>
                </div>
            </TabsContent>

            {/* 🔑 LOGIN HISTORY - ZORUNLU 4 */}
            <TabsContent value="login-history" className="mt-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">🔑 Admin Login History</CardTitle>
                      <CardDescription>All admin login attempts (successful and failed)</CardDescription>
                    </div>
                    <Button onClick={() => handleExportLogs(loginHistory, 'login_history.csv')}>
                      <Download className="w-4 h-4 mr-2" /> CSV Export
                    </Button>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Filters */}
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Filter by admin</Label>
                        <Input placeholder="Admin ID" value={loginFilter.admin_id} onChange={e => setLoginFilter({...loginFilter, admin_id: e.target.value})} />
                      </div>
                      <div>
                        <Label>Result</Label>
                        <Select value={loginFilter.result || "all"} onValueChange={v => setLoginFilter({...loginFilter, result: v === "all" ? "" : v})}>
                          <SelectTrigger><SelectValue placeholder="All" /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All</SelectItem>
                            <SelectItem value="success">✅ Başarılı</SelectItem>
                            <SelectItem value="failed">❌ Başarısız</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex items-end">
                        <Button 
                          variant={loginFilter.suspicious_only ? 'default' : 'outline'}
                          onClick={() => setLoginFilter({...loginFilter, suspicious_only: !loginFilter.suspicious_only})}
                          className="w-full"
                        >
                          <Filter className="w-4 h-4 mr-2" /> Only suspicious
                        </Button>
                      </div>
                    </div>

                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Admin</TableHead>
                          <TableHead>Login Time</TableHead>
                          <TableHead>IP Address</TableHead>
                          <TableHead>Cihaz</TableHead>
                          <TableHead>Location</TableHead>
                          <TableHead>Result</TableHead>
                          <TableHead>Sebep</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {loginHistory.map(login => (
                          <TableRow key={login.id} className={login.is_suspicious ? 'bg-red-50' : ''}>
                            <TableCell className="font-medium">
                              {login.admin_name}
                              {login.is_suspicious && <Badge variant="destructive" className="ml-2 text-xs">⚠️ SUSPICIOUS</Badge>}
                            </TableCell>
                            <TableCell className="text-xs">{new Date(login.login_time).toLocaleString('en-US')}</TableCell>
                            <TableCell className="font-mono text-xs">{login.ip_address}</TableCell>
                            <TableCell className="text-xs">{login.device_info}</TableCell>
                            <TableCell className="text-xs">{login.location || '-'}</TableCell>
                            <TableCell>
                              <Badge variant={login.result === 'success' ? 'default' : 'destructive'}>
                                {login.result === 'success' ? '✅ Success' : '❌ Failed'}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-xs text-muted-foreground">
                              {login.failure_reason || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    {loginHistory.length === 0 && <p className="text-center text-muted-foreground py-8">No login history yet.</p>}
                  </CardContent>
                </Card>
            </TabsContent>

            {/* 🟩 ADMIN RISK SCORE - OPSİYONEL 5 */}
            <TabsContent value="risk-score" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">🟩 Admin Risk Score (Optional)</CardTitle>
                    <CardDescription>Risk assessment per admin - new devices, new countries, failed login attempts</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Admin</TableHead>
                          <TableHead>Risk Score</TableHead>
                          <TableHead>Risk Level</TableHead>
                          <TableHead>Factors</TableHead>
                          <TableHead>Last Updated</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {users.slice(0, 3).map((user, idx) => {
                          const riskScore = [25, 45, 80][idx];
                          const riskLevel = riskScore < 30 ? 'Low' : riskScore < 60 ? 'Medium' : 'High';
                          const factors = [
                            ['Normal activity'],
                            ['New device +10', 'Failed login +5'],
                            ['New country +20', 'Unusual actions +30']
                          ][idx];
                          
                          return (
                            <TableRow key={user.id}>
                              <TableCell className="font-medium">{user.full_name}</TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                                    <div 
                                      className={`h-full ${riskLevel === 'Low' ? 'bg-green-500' : riskLevel === 'Medium' ? 'bg-yellow-500' : 'bg-red-500'}`}
                                      style={{ width: `${riskScore}%` }}
                                    />
                                  </div>
                                  <span className="text-sm font-mono">{riskScore}/100</span>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant={riskLevel === 'Low' ? 'default' : riskLevel === 'Medium' ? 'secondary' : 'destructive'}>
                                  {riskLevel}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="space-y-1">
                                  {factors.map((f, i) => <p key={i} className="text-xs text-muted-foreground">{f}</p>)}
                                </div>
                              </TableCell>
                              <TableCell className="text-xs">{new Date().toLocaleDateString('en-US')}</TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
            </TabsContent>

            {/* 🟩 DELEGATION - OPSİYONEL 6 */}
            <TabsContent value="delegation" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">🟩 Delegation / Proxy (Optional)</CardTitle>
                    <CardDescription>When an admin is on leave, they can temporarily delegate their permissions to another admin</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-end">
                        <Button><Plus className="w-4 h-4 mr-2" /> New Delegation</Button>
                      </div>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Primary Admin</TableHead>
                            <TableHead>Delegate Admin</TableHead>
                            <TableHead>Start</TableHead>
                            <TableHead>End</TableHead>
                            <TableHead>Delegated Permissions</TableHead>
                            <TableHead>Status</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          <TableRow>
                            <TableCell className="font-medium">Mehmet Yilmaz</TableCell>
                            <TableCell>Ayse Demir</TableCell>
                            <TableCell className="text-xs">2025-12-20</TableCell>
                            <TableCell className="text-xs">2025-12-27</TableCell>
                            <TableCell><Badge variant="outline">Player Management</Badge></TableCell>
                            <TableCell><Badge>Active</Badge></TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell className="font-medium">Ali Kaya</TableCell>
                            <TableCell>Fatma Sahin</TableCell>
                            <TableCell className="text-xs">2025-12-10</TableCell>
                            <TableCell className="text-xs">2025-12-15</TableCell>
                            <TableCell><Badge variant="outline">Finance Approve</Badge></TableCell>
                            <TableCell><Badge variant="secondary">Completed</Badge></TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
            </TabsContent>

            {/* SESSIONS */}
            <TabsContent value="sessions" className="mt-4">
              <Card>
                <CardHeader><CardTitle>Aktif Oturumlar</CardTitle></CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Admin</TableHead>
                        <TableHead>IP</TableHead>
                        <TableHead>Cihaz</TableHead>
                        <TableHead>Giriş</TableHead>
                        <TableHead>Son Aktivite</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sessions.map(s => (
                        <TableRow key={s.id}>
                          <TableCell>{s.admin_name}</TableCell>
                          <TableCell className="font-mono text-xs">{s.ip_address}</TableCell>
                          <TableCell className="text-xs">{s.device_info}</TableCell>
                          <TableCell className="text-xs">{new Date(s.login_time).toLocaleString('tr-TR')}</TableCell>
                          <TableCell className="text-xs">{new Date(s.last_active).toLocaleString('tr-TR')}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {sessions.length === 0 && <p className="text-center text-muted-foreground py-8">Aktif oturum yok</p>}
                </CardContent>
              </Card>
            </TabsContent>
            
            {/* INVITES */}
            <TabsContent value="invites" className="mt-4">
              <Card><CardContent className="p-10 text-center text-muted-foreground">Invite management (under development)</CardContent></Card>
            </TabsContent>
            
            {/* KEYS */}
            <TabsContent value="keys" className="mt-4">
              <Card><CardContent className="p-10 text-center text-muted-foreground">API keys (under development)</CardContent></Card>
            </TabsContent>
            
            {/* SECURITY */}
            <TabsContent value="security" className="mt-4">
                {policy && (
                    <Card>
                        <CardHeader><CardTitle>Security Policy</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div><Label>Minimum Password Length</Label><Input value={policy.password_min_length} readOnly /></div>
                                <div><Label>Session Timeout (min)</Label><Input value={policy.session_timeout_minutes} readOnly /></div>
                                <div><Label>Max Login Attempts</Label><Input value={policy.max_login_attempts} readOnly /></div>
                                <div className="flex items-center gap-2 pt-6"><input type="checkbox" checked={policy.require_2fa} readOnly /> <Label>2FA Required</Label></div>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </TabsContent>
        </Tabs>
    </div>
  );
};

export { AdminManagement };
