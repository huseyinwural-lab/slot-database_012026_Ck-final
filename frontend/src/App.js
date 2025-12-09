import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import PlayerList from './pages/PlayerList';
import PlayerDetail from './pages/PlayerDetail';
import Finance from './pages/Finance';
import ApprovalQueue from './pages/ApprovalQueue';
import GameManagement from './pages/GameManagement';
import BonusManagement from './pages/BonusManagement';
import FraudCheck from './pages/FraudCheck';
import Support from './pages/Support';
import FeatureFlags from './pages/FeatureFlags';
import Simulator from './pages/Simulator';
import VipGames from './pages/VipGames';
import { KYC, CRM, CMS, Affiliates, Risk, Admins, Logs, RG, Reports } from './pages/Modules';
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
          <Route path="/approvals" element={<ApprovalQueue />} />
          <Route path="/games" element={<GameManagement />} />
          <Route path="/vip-games" element={<VipGames />} />
          <Route path="/bonuses" element={<BonusManagement />} />
          <Route path="/fraud" element={<FraudCheck />} />
          <Route path="/support" element={<Support />} />
          <Route path="/features" element={<FeatureFlags />} />
          <Route path="/simulator" element={<Simulator />} />
          
          {/* New Modules */}
          <Route path="/kyc" element={<KYC />} />
          <Route path="/crm" element={<CRM />} />
          <Route path="/cms" element={<CMS />} />
          <Route path="/affiliates" element={<Affiliates />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/admins" element={<Admins />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/rg" element={<RG />} />
          <Route path="/reports" element={<Reports />} />
          
          <Route path="/settings" element={<div className="p-10 text-xl font-bold">Settings Panel (Multi-Tenant Config)</div>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        <Toaster position="top-right" theme="dark" />
      </Layout>
    </BrowserRouter>
  );
}

export default App;
