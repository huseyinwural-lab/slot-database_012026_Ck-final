import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import RequireAuth from './components/RequireAuth';
import RequireFeature from './components/RequireFeature';
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
import APIKeysPage from './pages/APIKeysPage';
import AcceptInvite from './pages/AcceptInvite';
import { Toaster } from 'sonner';
import { CapabilitiesProvider } from './context/CapabilitiesContext';

function App() {
  return (
    <BrowserRouter>
      <CapabilitiesProvider>
        <Layout>
          <Routes>
            <Route path="/login" element={<Login />} />

          <Route
            path="/"
            element={(
              <RequireAuth>
                <Dashboard />
              </RequireAuth>
            )}
          />
          <Route
            path="/players"
            element={(
              <RequireAuth>
                <PlayerList />
              </RequireAuth>
            )}
          />
          <Route
            path="/players/:id"
            element={(
              <RequireAuth>
                <PlayerDetail />
              </RequireAuth>
            )}
          />
          <Route
            path="/finance"
            element={(
              <RequireAuth>
                <Finance />
              </RequireAuth>
            )}
          />
          <Route
            path="/approvals"
            element={(
              <RequireAuth>
                <ApprovalQueue />
              </RequireAuth>
            )}
          />
          <Route
            path="/games"
            element={(
              <RequireAuth>
                <GameManagement />
              </RequireAuth>
            )}
          />
          <Route
            path="/vip-games"
            element={(
              <RequireAuth>
                <VipGames />
              </RequireAuth>
            )}
          />
          <Route
            path="/bonuses"
            element={(
              <RequireAuth>
                <BonusManagement />
              </RequireAuth>
            )}
          />
          <Route
            path="/fraud"
            element={(
              <RequireAuth>
                <FraudCheck />
              </RequireAuth>
            )}
          />
          <Route
            path="/support"
            element={(
              <RequireAuth>
                <Support />
              </RequireAuth>
            )}
          />
          <Route
            path="/features"
            element={(
              <RequireAuth>
                <FeatureFlags />
              </RequireAuth>
            )}
          />
          <Route
            path="/simulator"
            element={(
              <RequireAuth>
                <SimulationLab />
              </RequireAuth>
            )}
          />
          
          {/* New Modules */}
          <Route
            path="/kyc"
            element={(
              <RequireAuth>
                <KYCManagement />
              </RequireAuth>
            )}
          />
          <Route
            path="/crm"
            element={(
              <RequireAuth>
                <CRM />
              </RequireAuth>
            )}
          />
          <Route
            path="/cms"
            element={(
              <RequireAuth>
                <CMSManagement />
              </RequireAuth>
            )}
          />
          <Route
            path="/affiliates"
            element={(
              <RequireAuth>
                <AffiliateManagement />
              </RequireAuth>
            )}
          />
          <Route
            path="/risk"
            element={(
              <RequireAuth>
                <RiskManagement />
              </RequireAuth>
            )}
          />
          <Route
            path="/admins"
            element={(
              <RequireAuth>
                <AdminManagement />
              </RequireAuth>
            )}
          />
          <Route
            path="/logs"
            element={(
              <RequireAuth>
                <SystemLogs />
              </RequireAuth>
            )}
          />
          <Route
            path="/rg"
            element={(
              <RequireAuth>
                <ResponsibleGaming />
              </RequireAuth>
            )}
          />
          <Route
            path="/reports"
            element={(
              <RequireAuth>
                <Reports />
              </RequireAuth>
            )}
          />
          <Route
            path="/tenants"
            element={(
              <RequireAuth>
                <TenantsPage />
              </RequireAuth>
            )}
          />
          
          <Route
            path="/keys"
            element={(
              <RequireAuth>
                <APIKeysPage />
              </RequireAuth>
            )}
          />
          <Route path="/accept-invite" element={<AcceptInvite />} />
          <Route
            path="/settings"
            element={(
              <RequireAuth>
                <SettingsPanel />
              </RequireAuth>
            )}
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        <Toaster position="top-right" theme="dark" />
      </Layout>
    </BrowserRouter>
  );
}

export default App;
