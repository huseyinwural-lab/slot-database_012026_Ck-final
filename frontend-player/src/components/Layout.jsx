import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { Gamepad2, User, LogIn, LogOut } from 'lucide-react';

const Layout = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('player_token');
  const user = JSON.parse(localStorage.getItem('player_user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('player_token');
    localStorage.removeItem('player_user');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      {/* Navbar */}
      <header className="border-b border-white/10 bg-black/50 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-2xl font-bold text-primary">
            <Gamepad2 className="w-8 h-8" />
            <span>CasinoLobby</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <Link to="/" className="hover:text-primary transition-colors">Lobby</Link>
            {/* Slots route not implemented yet (P1-1). */}
            <Link to="/wallet" className="hover:text-primary transition-colors">Wallet</Link>
            <Link to="/promotions" className="hover:text-primary transition-colors">Promotions</Link>
          </nav>

          <div className="flex items-center gap-4">
            {token ? (
              <>
                <div className="flex flex-col items-end mr-2">
                    <span className="text-sm font-medium">{user.username || 'Player'}</span>
                    <span className="text-xs text-green-400 font-mono">${user.balance_real?.toFixed(2) || '0.00'}</span>
                </div>
                <button 
                    onClick={handleLogout}
                    className="p-2 hover:bg-white/10 rounded-full transition-colors"
                >
                    <LogOut className="w-5 h-5" />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm font-medium hover:text-primary">Log In</Link>
                <Link to="/register" className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-bold hover:bg-primary/90 transition-colors">
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
      <footer className="border-t border-white/10 py-8 mt-auto bg-black/50">
        <div className="container mx-auto px-4 text-center text-muted-foreground text-sm">
          <p>© 2025 CasinoLobby. All rights reserved.</p>
          <p className="mt-2 text-xs">Responsible Gaming | 18+</p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
