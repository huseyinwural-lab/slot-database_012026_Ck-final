import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import PlayerList from './pages/PlayerList';
import PlayerDetail from './pages/PlayerDetail';
import Finance from './pages/Finance';
import GameManagement from './pages/GameManagement';
import BonusManagement from './pages/BonusManagement';
import FraudCheck from './pages/FraudCheck';
import Support from './pages/Support';
import { Toaster } from 'sonner';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/players" element={<PlayerList />} />
          <Route path="/players/:id" element={<PlayerDetail />} />
          <Route path="/finance" element={<Finance />} />
          <Route path="/games" element={<GameManagement />} />
          <Route path="/bonuses" element={<BonusManagement />} />
          <Route path="/fraud" element={<FraudCheck />} />
          <Route path="/support" element={<Support />} />
          <Route path="/settings" element={<div className="p-10 text-xl font-bold">Settings Panel (Coming Soon)</div>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        <Toaster position="top-right" theme="dark" />
      </Layout>
    </BrowserRouter>
  );
}

export default App;
