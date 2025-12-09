import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Users, CreditCard, ShieldAlert, 
  Gamepad2, Gift, MessageSquare, Settings, LogOut 
} from 'lucide-react';

const SidebarItem = ({ to, icon: Icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
        isActive
          ? 'bg-primary text-primary-foreground'
          : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
      }`
    }
  >
    <Icon className="w-5 h-5" />
    {label}
  </NavLink>
);

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card flex flex-col fixed h-full z-20">
        <div className="p-6">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
            CasinoAdmin
          </h1>
        </div>
        
        <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
          <SidebarItem to="/" icon={LayoutDashboard} label="Dashboard" />
          <SidebarItem to="/players" icon={Users} label="Players" />
          <SidebarItem to="/finance" icon={CreditCard} label="Finance" />
          <SidebarItem to="/games" icon={Gamepad2} label="Games" />
          <SidebarItem to="/bonuses" icon={Gift} label="Bonuses" />
          <SidebarItem to="/fraud" icon={ShieldAlert} label="Fraud Check" />
          <SidebarItem to="/support" icon={MessageSquare} label="Support" />
          <SidebarItem to="/settings" icon={Settings} label="Settings" />
        </nav>

        <div className="p-4 border-t border-border mt-auto">
          <button className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-destructive hover:bg-destructive/10 rounded-lg w-full transition-colors">
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 min-h-screen flex flex-col">
        <header className="h-16 border-b border-border bg-card/50 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-10">
          <h2 className="text-lg font-semibold">Admin Panel</h2>
          <div className="flex items-center gap-4">
            <div className="text-sm text-right hidden md:block">
              <p className="font-medium">Super Admin</p>
              <p className="text-xs text-muted-foreground">admin@casino.com</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
              SA
            </div>
          </div>
        </header>
        <div className="p-6 flex-1 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
