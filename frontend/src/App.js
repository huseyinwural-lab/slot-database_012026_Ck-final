import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import PlayerList from './pages/PlayerList';
import Finance from './pages/Finance';
import FraudCheck from './pages/FraudCheck';
import { Toaster } from 'sonner';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/players" element={<PlayerList />} />
          <Route path="/finance" element={<Finance />} />
          <Route path="/fraud" element={<FraudCheck />} />
          <Route path="/settings" element={<div className="p-10">Settings Placeholder</div>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        <Toaster position="top-right" theme="dark" />
      </Layout>
    </BrowserRouter>
  );
}

export default App;
