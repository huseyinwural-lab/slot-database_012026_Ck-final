import React, { useMemo, useState } from 'react';
import { useNavigate, NavLink } from 'react-router-dom';
import KillSwitchTooltipWrapper from './KillSwitchTooltipWrapper';
import { Search, LogOut, CreditCard, Users } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ScrollArea } from '@/components/ui/scroll-area';
import api from '../services/api';
import { useCapabilities } from '../context/CapabilitiesContext';
import { MENU_ITEMS } from '../config/menu';

import TenantSwitcher from './TenantSwitcher';

const SidebarItem = ({ to, icon: Icon, label, activeClassName, className, disabled, disabledTooltip, badgeText }) => {
  if (disabled) {
    return (
      <KillSwitchTooltipWrapper disabled={true} tooltip={disabledTooltip}>
        <div
          role="link"
          aria-disabled="true"
          tabIndex={0}
          onClick={(e) => e.preventDefault()}
          className={`grid grid-cols-[20px_1fr] items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors min-h-[40px] opacity-50 cursor-not-allowed ${
            className || 'text-muted-foreground'
          }`}
        >
          <Icon className="w-5 h-5" />
          <div className="flex items-center justify-between gap-2">
            <span className="leading-none">{label}</span>
            {badgeText ? (
              <Badge variant="secondary" className="text-[10px] px-2 py-0 h-5">
                {badgeText}
              </Badge>
            ) : null}
          </div>
        </div>
      </KillSwitchTooltipWrapper>
    );
  }

  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `grid grid-cols-[20px_1fr] items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors min-h-[40px] ${
          className || (isActive
            ? activeClassName || 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:bg-secondary hover:text-foreground')
        }`
      }
    >
      <Icon className="w-5 h-5" />
      <span className="leading-none">{label}</span>
    </NavLink>
  );
};

const Layout = ({ children }) => {
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState([]);
  const navigate = useNavigate();

  const { isOwner, tenantName, hasFeature, capabilities, loading: capabilitiesLoading } = useCapabilities();

  const killSwitches = useMemo(
    () => (capabilities?.kill_switches || {}),
    [capabilities?.kill_switches]
  );
  
  const menuFlags = useMemo(
    () => capabilities?.menu_flags || {},
    [capabilities?.menu_flags]
  );

  // Theme Config based on Role
  const theme = isOwner ? {
    sidebarBg: 'bg-card',
    headerGradient: 'from-primary to-blue-400',
    iconColor: 'text-primary',
    brandName: 'Platform Admin',
    activeItem: 'bg-primary text-primary-foreground',
    disabledItem: 'opacity-50 cursor-not-allowed'
  } : {
    sidebarBg: 'bg-slate-900',
    headerGradient: 'from-emerald-400 to-teal-500',
    iconColor: 'text-emerald-400',
    brandName: tenantName || 'Tenant Portal',
    activeItem: 'bg-emerald-600 text-white',
    disabledItem: 'opacity-50 cursor-not-allowed'
  };

  const handleSearch = async () => {};

  const groupedMenu = useMemo(() => {
    const visibleItems = MENU_ITEMS.filter(item => {
        const isCrmKillDisabled = item.key === 'ops.crm' && killSwitches?.crm === true;

        // 1. Owner check
        if (item.ownerOnly && !isOwner) return false;
        if (item.tenantOnly && isOwner) return false;

        // 2. Feature check (Legacy)
        // Kill Switch P0: if a module is disabled by kill switch, keep the menu item visible
        // (disabled styling + tooltip) so it's not perceived as a bug.
        if (item.feature && !hasFeature(item.feature) && !isCrmKillDisabled) return false;

        // 3. Menu Flag check (New)
        // If flag is explicitly false, hide it. Otherwise show.
        if (menuFlags[item.key] === false) return false;

        return true;
    });

    // Group by section
    const groups = {};
    visibleItems.forEach(item => {
        if (!groups[item.section]) groups[item.section] = [];
        groups[item.section].push(item);
    });
    
    // Order sections based on MENU_ITEMS order logic (preserved via insertion order usually, but let's be safe if needed)
    // Actually dict keys iteration order is insertion order in modern JS.
    return groups;
  }, [isOwner, hasFeature, menuFlags, killSwitches]);

  return (
    <div className="min-h-screen bg-background">
      {/* TooltipProvider ensures tooltips work across the app */}
      <TooltipProvider delayDuration={200}>
        <div className="flex">
      {/* Sidebar */}
      <aside className={`w-64 border-r border-border ${theme.sidebarBg} flex flex-col fixed h-full z-20 transition-colors duration-300`}>
        <div className="p-6">
          <h1 className={`text-2xl font-bold bg-gradient-to-r ${theme.headerGradient} bg-clip-text text-transparent`}>
            {theme.brandName}
          </h1>
          {!isOwner && <p className="text-xs text-muted-foreground mt-1">Tenant Panel</p>}
        </div>
        
        <ScrollArea className="flex-1 px-4">
            {Object.entries(groupedMenu).map(([section, items]) => (
                <div key={section} className="space-y-1 mb-6">
                    <div className="px-4 text-xs font-semibold text-muted-foreground mb-2 mt-4 uppercase tracking-wider">
                        {section}
                    </div>
                    <ul className="space-y-1">
                        {items.map(item => (
                            <li key={item.key}>
                                <SidebarItem 
                                    to={item.path} 
                                    icon={item.icon} 
                                    label={item.label} 
                                    activeClassName={theme.activeItem}
                                    className={item.className}
                                    disabled={(item.key === 'ops.crm' && killSwitches?.crm === true) || item.comingSoon}
                                    disabledTooltip={item.comingSoon ? 'Yakında' : 'Module disabled by Kill Switch'}
                                    badgeText={item.comingSoon ? 'Yakında' : null}
                                />
                            </li>
                        ))}
                    </ul>
                </div>
            ))}
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
                <KillSwitchTooltipWrapper disabled={true} tooltip="Search service is being updated">
                  <Input
                    placeholder="Global Search (Press Ctrl+K)"
                    className="pl-8 bg-secondary/50 border-0"
                    readOnly
                    onFocus={(e) => e.currentTarget.blur()}
                  />
                </KillSwitchTooltipWrapper>
             </div>
          </div>
          <div className="flex items-center gap-4">
            <TenantSwitcher />
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

        {/* Global Search disabled (P1-1) because backend /v1/search is not available. */}

      </main>
        </div>
      </TooltipProvider>
    </div>
  );
};

export default Layout;
