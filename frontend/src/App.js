import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import RequireAuth from './components/RequireAuth';
import RequireFeature from './components/RequireFeature';
import Dashboard from './pages/Dashboard';
import PlayerList from './pages/PlayerList';
import PlayerDetail from './pages/PlayerDetail';
import PlayerWallet from './pages/PlayerWallet';
import Finance from './pages/Finance';
import FinanceWithdrawals from './pages/FinanceWithdrawals';
import ApprovalQueue from './pages/ApprovalQueue';
import GameManagement from './pages/GameManagement';
import BonusManagement from './pages/BonusManagement';
import ReferralRedirect from './pages/ReferralRedirect';
import FraudCheck from './pages/FraudCheck';
import Support from './pages/Support';
import { FeatureFlags } from './pages/FeatureFlags';
import SimulationLab from './pages/SimulationLab';
import RobotsPage from './pages/RobotsPage';
import MathAssetsPage from './pages/MathAssetsPage';
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
import AuditLog from './pages/AuditLog';
import SettingsPanel from './pages/SettingsPanel';
import OpsStatus from './pages/OpsStatus';
import TenantsPage from './pages/TenantsPage';
import KillSwitchPage from './pages/KillSwitchPage';
import Login from './pages/Login';
import APIKeysPage from './pages/APIKeysPage';
import AcceptInvite from './pages/AcceptInvite';
import OwnerRevenue from './pages/OwnerRevenue';
import TenantRevenue from './pages/TenantRevenue';
import RevenueAllTenantsRedirect from './pages/RevenueAllTenantsRedirect';
import RevenueMyTenantRedirect from './pages/RevenueMyTenantRedirect';
import { Toaster } from 'sonner';
import { CapabilitiesProvider } from './context/CapabilitiesContext';
import ModuleDisabled from './pages/ModuleDisabled'; 
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <CapabilitiesProvider>
          <Layout>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/accept-invite" element={<AcceptInvite />} />
              <Route path="/module-disabled" element={<ModuleDisabled />} />

              <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
              <Route path="/players" element={<RequireAuth><PlayerList /></RequireAuth>} />
              <Route path="/players/:id" element={<RequireAuth><PlayerDetail /></RequireAuth>} />
              <Route path="/player/wallet" element={<RequireAuth><PlayerWallet /></RequireAuth>} />
              <Route path="/finance" element={<RequireAuth><Finance /></RequireAuth>} />
              <Route path="/approvals" element={<RequireAuth><ApprovalQueue /></RequireAuth>} />
              <Route path="/finance/withdrawals" element={<RequireAuth><FinanceWithdrawals /></RequireAuth>} />
              <Route path="/games" element={<RequireAuth><GameManagement /></RequireAuth>} />
              <Route path="/vip-games" element={<RequireAuth><VipGames /></RequireAuth>} />
              
              <Route path="/r/:code" element={<ReferralRedirect />} />

              <Route path="/bonuses" element={
                <RequireAuth>
                  <RequireFeature feature="can_manage_bonus"><BonusManagement /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/fraud" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><FraudCheck /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/support" element={<RequireAuth><Support /></RequireAuth>} />
              
              <Route path="/features" element={
                <RequireAuth>
                  <RequireFeature feature="can_manage_experiments"><FeatureFlags /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/simulator" element={
                <RequireAuth>
                  <RequireFeature feature="can_use_game_robot" requireOwner={true}><SimulationLab /></RequireFeature>
                </RequireAuth>
              } />
              <Route path="/robots" element={
                <RequireAuth>
                  <RequireFeature feature="can_use_game_robot"><RobotsPage /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/math-assets" element={
                <RequireAuth>
                  <RequireFeature feature="can_use_game_robot"><MathAssetsPage /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/kyc" element={
                <RequireAuth>
                  <RequireFeature feature="can_manage_kyc"><KYCManagement /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/crm" element={
                <RequireAuth>
                  <RequireFeature feature="can_use_crm"><CRM /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/cms" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><CMSManagement /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/affiliates" element={
                <RequireAuth>
                  <RequireFeature feature="can_manage_affiliates"><AffiliateManagement /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/risk" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><RiskManagement /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/admins" element={
                <RequireAuth>
                  <RequireFeature feature="can_manage_admins"><AdminManagement /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/logs" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><SystemLogs /></RequireFeature>
                </RequireAuth>
              } />

              <Route path="/audit" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><AuditLog /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/ops" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><OpsStatus /></RequireFeature>
                </RequireAuth>
              } />

              <Route path="/rg" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><ResponsibleGaming /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/reports" element={
                <RequireAuth>
                  <RequireFeature feature="can_view_reports"><Reports /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/tenants" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><TenantsPage /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/keys" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><APIKeysPage /></RequireFeature>
                </RequireAuth>
              } />

              <Route path="/revenue/all-tenants" element={
                <RequireAuth>
                  <RequireFeature requireOwner={true}><OwnerRevenue /></RequireFeature>
                </RequireAuth>
              } />
              
              <Route path="/revenue/my-tenant" element={
                <RequireAuth><TenantRevenue /></RequireAuth>
              } />
              
              <Route path="/kill-switch" element={
                <RequireAuth>
                  <RequireFeature feature="can_use_kill_switch"><KillSwitchPage /></RequireFeature>
                </RequireAuth>
              } />

              <Route path="/settings" element={<RequireAuth><SettingsPanel /></RequireAuth>} />
              
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
            <Toaster position="top-right" theme="dark" />
          </Layout>
        </CapabilitiesProvider>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
