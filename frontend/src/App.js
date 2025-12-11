import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import RequireAuth from './components/RequireAuth';
import Dashboard from './pages/Dashboard';
import PlayerList from './pages/PlayerList';
import PlayerDetail from './pages/PlayerDetail';
import Finance from './pages/Finance';
import ApprovalQueue from './pages/ApprovalQueue';
import GameManagement from './pages/GameManagement';
import BonusManagement from './pages/BonusManagement';
import FraudCheck from './pages/FraudCheck';
import Support from './pages/Support';
import { FeatureFlags } from './pages/FeatureFlags';
import SimulationLab from './pages/SimulationLab';
import VipGames from './pages/VipGames';
import KYCManagement from './pages/KYCManagement';
import { CRM } from './pages/CRM';
import { AffiliateManagement } from './pages/AffiliateManagement';
import RiskManagement from './pages/RiskManagement';
import ResponsibleGaming from './pages/ResponsibleGaming';
import { CMSManagement } from './pages/CMSManagement';
import { Reports } from './pages/Reports';
import { SystemLogs } from './pages/SystemLogs';
import { AdminManagement } from './pages/AdminManagement';
import SettingsPanel from './pages/SettingsPanel';
import TenantsPage from './pages/TenantsPage';
import Login from './pages/Login';
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
          <Route path="/simulator" element={<SimulationLab />} />
          
          {/* New Modules */}
          <Route path="/kyc" element={<KYCManagement />} />
          <Route path="/crm" element={<CRM />} />
          <Route path="/cms" element={<CMSManagement />} />
          <Route path="/affiliates" element={<AffiliateManagement />} />
          <Route path="/risk" element={<RiskManagement />} />
          <Route path="/admins" element={<AdminManagement />} />
          <Route path="/logs" element={<SystemLogs />} />
          <Route path="/rg" element={<ResponsibleGaming />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/tenants" element={<TenantsPage />} />
          
          <Route path="/settings" element={<SettingsPanel />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        <Toaster position="top-right" theme="dark" />
      </Layout>
    </BrowserRouter>
  );
}

export default App;
