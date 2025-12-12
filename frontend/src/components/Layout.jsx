import React, { useState } from 'react';
import { useNavigate, NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Users, CreditCard, ShieldAlert, 
  Gamepad2, Gift, MessageSquare, Settings, LogOut,
  ListChecks, ToggleRight, Search, FlaskConical,
  FileText, Megaphone, BarChart3, Globe, Handshake,
  AlertOctagon, UserCog, ScrollText, Scale, Crown,
  KeyRound, Building
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { ScrollArea } from '@/components/ui/scroll-area';
import api from '../services/api';
import { useTenant } from '../hooks/useTenant';
import { useCapabilities } from '../context/CapabilitiesContext';

const SidebarItem = ({ to, icon: Icon, label, activeClassName }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
        isActive
          ? activeClassName || 'bg-primary text-primary-foreground'
          : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
      }`
    }
  >
    <Icon className="w-5 h-5" />
    {label}
  </NavLink>
);

const Layout = ({ children }) => {
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState([]);
  const navigate = useNavigate();

  const { tenant, loading: tenantLoading } = useTenant();
  const { isOwner, hasFeature } = useCapabilities();
  const tenantType = tenant?.type || 'owner';
  const tenantFeatures = tenant?.features || {};

  const handleSearch = async (val) => {
    if (val.length > 2) {
      try {
        const res = await api.get(`/v1/search?q=${val}`);
        setResults(res.data);
      } catch (e) { console.error(e); }
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card flex flex-col fixed h-full z-20">
        <div className="p-6">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
            CasinoAdmin
          </h1>
        </div>
        
        <ScrollArea className="flex-1 px-4">
          <div className="space-y-1 mb-6">
              <div className="px-4 text-xs font-semibold text-muted-foreground mb-2 mt-4 uppercase tracking-wider">Core</div>
              <SidebarItem to="/" icon={LayoutDashboard} label="Dashboard" />
              <SidebarItem to="/players" icon={Users} label="Players" />
              {isOwner && (
                <SidebarItem to="/finance" icon={CreditCard} label="Finance" />
              )}
              <SidebarItem to="/games" icon={Gamepad2} label="Games" />
              <SidebarItem
                to="/vip-games"
                icon={Crown}
                label="VIP Games"
                activeClassName="bg-yellow-500/20 text-yellow-500 border border-yellow-500/50"
              />
          </div>

          <div className="space-y-1 mb-6">
              <div className="px-4 text-xs font-semibold text-muted-foreground mb-2 mt-4 uppercase tracking-wider">Operations</div>
              {hasFeature('can_manage_kyc') && <SidebarItem to="/kyc" icon={FileText} label="KYC Verification" />}
              {isOwner && <SidebarItem to="/crm" icon={Megaphone} label="CRM & Comms" />}
              {hasFeature('can_manage_bonus') && <SidebarItem to="/bonuses" icon={Gift} label="Bonuses" />}
              {isOwner && <SidebarItem to="/affiliates" icon={Handshake} label="Affiliates" />}
              <SidebarItem to="/support" icon={MessageSquare} label="Support" />
          </div>

           <div className="space-y-1 mb-6">
              <div className="px-4 text-xs font-semibold text-muted-foreground mb-2 mt-4 uppercase tracking-wider">Risk & Compliance</div>
              {isOwner && <SidebarItem to="/risk" icon={AlertOctagon} label="Risk Rules" />}
              {isOwner && <SidebarItem to="/fraud" icon={ShieldAlert} label="Fraud Check" />}
              {isOwner && <SidebarItem to="/approvals" icon={ListChecks} label="Approval Queue" />}
              {isOwner && <SidebarItem to="/rg" icon={Scale} label="Responsible Gaming" />}
          </div>

          <div className="space-y-1 mb-6">
              <div className="px-4 text-xs font-semibold text-muted-foreground mb-2 mt-4 uppercase tracking-wider">System</div>
              {isOwner && <SidebarItem to="/cms" icon={Globe} label="CMS" />}
              {hasFeature('can_view_reports') && <SidebarItem to="/reports" icon={BarChart3} label="Reports" />}
              {isOwner && <SidebarItem to="/logs" icon={ScrollText} label="Logs" />}
              {hasFeature('can_manage_admins') && <SidebarItem to="/admins" icon={UserCog} label="Admin Users" />}
              {isOwner && <SidebarItem to="/tenants" icon={Building} label="Tenants" />}
              {isOwner && <SidebarItem to="/keys" icon={KeyRound} label="API Keys" />}
              {isOwner && <SidebarItem to="/features" icon={ToggleRight} label="Feature Flags" />}
              {hasFeature('can_use_game_robot') && isOwner && <SidebarItem to="/simulator" icon={FlaskConical} label="Simulator" />}
              {isOwner && <SidebarItem to="/settings" icon={Settings} label="Settings" />}
          </div>
        </ScrollArea>

        <div className="p-4 border-t border-border mt-auto bg-card">
          <button
            className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-destructive hover:bg-destructive/10 rounded-lg w-full transition-colors"
            onClick={() => {
              if (typeof window !== 'undefined') {
                localStorage.removeItem('admin_token');
                localStorage.removeItem('admin_user');
                window.location.href = '/login';
              }
            }}
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 min-h-screen flex flex-col">
        <header className="h-16 border-b border-border bg-card/50 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-4 flex-1">
             <div className="relative w-full max-w-md">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Global Search (Press Ctrl+K)"
                  className="pl-8 bg-secondary/50 border-0"
                  onFocus={() => setOpen(true)}
                />
             </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-right hidden md:block">
              <p className="font-medium">
                {(() => {
                  if (typeof window === 'undefined') return 'Admin';
                  try {
                    const raw = localStorage.getItem('admin_user');
                    if (!raw) return 'Admin';
                    const admin = JSON.parse(raw);
                    return admin.full_name || 'Admin';
                  } catch {
                    return 'Admin';
                  }
                })()}
              </p>
              <p className="text-xs text-muted-foreground">
                {(() => {
                  if (typeof window === 'undefined') return '';
                  try {
                    const raw = localStorage.getItem('admin_user');
                    if (!raw) return '';
                    const admin = JSON.parse(raw);
                    return admin.email || '';
                  } catch {
                    return '';
                  }
                })()}
              </p>
            </div>
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
              {(() => {
                if (typeof window === 'undefined') return 'A';
                try {
                  const raw = localStorage.getItem('admin_user');
                  if (!raw) return 'A';
                  const admin = JSON.parse(raw);
                  if (admin.full_name) {
                    return admin.full_name
                      .split(' ')
                      .filter(Boolean)
                      .slice(0, 2)
                      .map((p) => p[0]?.toUpperCase())
                      .join('');
                  }
                  if (admin.email) {
                    return admin.email[0]?.toUpperCase();
                  }
                  return 'A';
                } catch {
                  return 'A';
                }
              })()}
            </div>
          </div>
        </header>
        
        <div className="p-6 flex-1 overflow-auto">
          {children}
        </div>

        <CommandDialog open={open} onOpenChange={setOpen}>
          <CommandInput placeholder="Type to search players, transactions..." onValueChange={handleSearch} />
          <CommandList>
            <CommandEmpty>No results found.</CommandEmpty>
            <CommandGroup heading="Results">
                {results.map((item, i) => (
                    <CommandItem key={i} onSelect={() => {
                        setOpen(false);
                        if(item.type === 'player') navigate(`/players/${item.id}`);
                    }}>
                        {item.type === 'player' ? <Users className="mr-2 h-4 w-4" /> : <CreditCard className="mr-2 h-4 w-4" />}
                        <span>{item.title}</span>
                        <span className="ml-2 text-muted-foreground text-xs">({item.details})</span>
                    </CommandItem>
                ))}
            </CommandGroup>
          </CommandList>
        </CommandDialog>

      </main>
    </div>
  );
};

export default Layout;
