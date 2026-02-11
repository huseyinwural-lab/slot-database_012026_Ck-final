import React, { useState } from 'react';
import { Outlet, Link, useNavigate, NavLink } from 'react-router-dom';
import { Gamepad2, LogOut } from 'lucide-react';
import { BalancePill } from './BalancePill';
import { Modal } from './Modal';
import { ThemeCustomizer } from './ThemeCustomizer';
import { useAuthStore, useWalletStore } from '@/domain';

const Layout = () => {
  const navigate = useNavigate();
  const { token, user, logout } = useAuthStore();
  const { balance, currency } = useWalletStore();
  const [themeOpen, setThemeOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinkClass = ({ isActive }) =>
    `text-sm ${isActive ? 'text-[var(--app-accent,#19e0c3)]' : 'text-white/70 hover:text-white'}`;

  return (
    <div className="min-h-screen text-foreground font-sans" style={{ backgroundColor: 'var(--player-bg)' }} data-testid="player-layout">
      {/* Navbar */}
      <header
        className="border-b border-white/10 sticky top-0 z-50"
        style={{ backgroundColor: 'var(--player-header)' }}
        data-testid="player-header"
      >
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/lobby" className="flex items-center gap-2 text-2xl font-bold text-primary" data-testid="player-logo">
            <Gamepad2 className="w-8 h-8" />
            <span>CasinoLobby</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6" data-testid="player-nav">
            <NavLink to="/lobby" className={navLinkClass} data-testid="nav-lobby">Lobby</NavLink>
            <NavLink to="/wallet" className={navLinkClass} data-testid="nav-wallet">Wallet</NavLink>
            <NavLink to="/support" className={navLinkClass} data-testid="nav-support">Support</NavLink>
          </nav>

          <div className="flex items-center gap-4">
            {token ? (
              <>
                <div className="flex flex-col items-end mr-2" data-testid="player-user-info">
                    <span className="text-sm font-medium" data-testid="player-username">{user?.username || 'Player'}</span>
                </div>
                <BalancePill balance={balance} currency={currency} />
                <button 
                    onClick={handleLogout}
                    className="p-2 hover:bg-white/10 rounded-full transition-colors"
                    data-testid="logout-button"
                >
                    <LogOut className="w-5 h-5" />
                </button>
                <button
                  className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/70"
                  onClick={() => setThemeOpen(true)}
                  data-testid="theme-button"
                >
                  Tema
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm font-medium hover:text-primary" data-testid="nav-login">Log In</Link>
                <Link to="/register" className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-bold hover:bg-primary/90 transition-colors" data-testid="nav-register">
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer
        className="border-t border-white/10 py-8 mt-auto"
        style={{ backgroundColor: 'var(--player-footer)' }}
        data-testid="player-footer"
      >
        <div className="container mx-auto px-4 text-center text-muted-foreground text-sm">
          <p>© 2025 CasinoLobby. All rights reserved.</p>
          <p className="mt-2 text-xs">Responsible Gaming | 18+</p>
        </div>
      </footer>

      <Modal open={themeOpen} title="Tema Ayarları" onClose={() => setThemeOpen(false)}>
        <ThemeCustomizer />
      </Modal>
    </div>
  );
};

export default Layout;
