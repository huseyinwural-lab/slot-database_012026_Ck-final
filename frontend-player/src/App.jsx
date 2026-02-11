import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Lobby from './pages/Lobby';
import Login from './pages/Login';
import Register from './pages/Register';
import WalletPage from './pages/WalletPage';
import GameRoom from './pages/GameRoom';
import VerifyEmail from './pages/VerifyEmail';
import VerifySms from './pages/VerifySms';
import Support from './pages/Support';
import Layout from './components/Layout';
import { ToastProvider } from './components/ToastProvider';
import { useAuthStore, useVerificationStore } from './domain';

const RequireAuth = ({ children }) => {
  const { token } = useAuthStore();
  if (!token) {
    return <Navigate to="/login" />;
  }
  return children;
};

const RequireVerified = ({ children }) => {
  const { emailState, smsState } = useVerificationStore();
  if (emailState !== 'verified') {
    return <Navigate to="/verify/email" />;
  }
  if (smsState !== 'verified') {
    return <Navigate to="/verify/sms" />;
  }
  return children;
};

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify/email" element={<VerifyEmail />} />
          <Route path="/verify/sms" element={<VerifySms />} />
          <Route
            path="/lobby"
            element={(
              <RequireAuth>
                <RequireVerified>
                  <Lobby />
                </RequireVerified>
              </RequireAuth>
            )}
          />
          <Route
            path="/wallet"
            element={(
              <RequireAuth>
                <RequireVerified>
                  <WalletPage />
                </RequireVerified>
              </RequireAuth>
            )}
          />
          <Route
            path="/game"
            element={(
              <RequireAuth>
                <RequireVerified>
                  <GameRoom />
                </RequireVerified>
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
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;