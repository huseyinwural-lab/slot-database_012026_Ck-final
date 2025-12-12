import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';

export const CapabilitiesContext = createContext();

export const CapabilitiesProvider = ({ children }) => {
  const [capabilities, setCapabilities] = useState(null);
  const [isOwner, setIsOwner] = useState(false);
  const [tenantRole, setTenantRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in (token exists)
    const token = localStorage.getItem('admin_token');
    console.log('🔑 Token check:', token ? 'EXISTS' : 'MISSING');
    
    if (token) {
      console.log('🔄 Fetching capabilities...');
      fetchCapabilities();
    } else {
      console.log('❌ No token, skipping capabilities fetch');
      setCapabilities(null);
      setIsOwner(false);
      setLoading(false);
    }
  }, []);
  
  // Refetch when window gets focus (for login flow)
  useEffect(() => {
    const handleFocus = () => {
      const token = localStorage.getItem('admin_token');
      if (token && !capabilities) {
        console.log('🔄 Window focused, refetching capabilities');
        fetchCapabilities();
      }
    };
    
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [capabilities]);

  const fetchCapabilities = async () => {
    try {
      const response = await api.get('/v1/tenants/capabilities');
      const data = response.data;

      console.log('✅ Capabilities fetched:', data);
      setCapabilities(data.features || {});
      setIsOwner(data.is_owner || false);
      setTenantRole(data.tenant_role || null);
      console.log('✅ isOwner set to:', data.is_owner);
    } catch (error) {
      console.error('Failed to fetch capabilities:', error);
      setCapabilities({});
      setIsOwner(false);
    } finally {
      setLoading(false);
    }
  };

  const hasFeature = (featureKey) => {
    if (!capabilities) return false;
    return capabilities[featureKey] === true;
  };

  return (
    <CapabilitiesContext.Provider
      value={{
        capabilities,
        loading,
        isOwner,
        tenantRole,
        hasFeature,
        refetch: fetchCapabilities
      }}
    >
      {children}
    </CapabilitiesContext.Provider>
  );
};

export const useCapabilities = () => {
  const context = useContext(CapabilitiesContext);
  if (!context) {
    throw new Error('useCapabilities must be used within CapabilitiesProvider');
  }
  return context;
};
