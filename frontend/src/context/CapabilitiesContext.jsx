import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';

export const CapabilitiesContext = createContext();

export const CapabilitiesProvider = ({ children }) => {
  const [capabilitiesObject, setCapabilitiesObject] = useState({});
  const [capabilitiesList, setCapabilitiesList] = useState([]);
  const [isOwner, setIsOwner] = useState(false);
  const [tenantRole, setTenantRole] = useState(null);
  const [tenantName, setTenantName] = useState('');
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
      if (token && !capabilitiesObject) {
        console.log('🔄 Window focused, refetching capabilities');
        fetchCapabilities();
      }
    };
    
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [capabilitiesObject]);

  const fetchCapabilities = async () => {
    try {
      const response = await api.get('/v1/tenants/capabilities');
      const data = response.data;

      console.log('✅ Capabilities fetched:', data);
      setCapabilitiesObject(data.features || {});
      setCapabilitiesList(Object.entries(data.features || {}).map(([key, value]) => ({ key, value })));
      setIsOwner(data.is_owner || false);
      setTenantRole(data.tenant_role || null);
      setTenantName(data.tenant_name || 'Casino');
      console.log('✅ isOwner set to:', data.is_owner);
    } catch (error) {
      console.error('Failed to fetch capabilities:', error);
      // If token exists but capabilities fail (e.g., 403/503 due to tenant context),
      // keep the user authenticated; just mark capabilities as empty.
      setCapabilitiesObject({});
      setCapabilitiesList([]);
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
        tenantName,
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
