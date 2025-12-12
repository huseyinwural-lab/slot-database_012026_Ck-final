import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';

export const CapabilitiesContext = createContext();

export const CapabilitiesProvider = ({ children }) => {
  const [capabilities, setCapabilities] = useState(null);
  const [isOwner, setIsOwner] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in (token exists)
    const token = localStorage.getItem('admin_token');
    if (token) {
      fetchCapabilities();
    } else {
      setCapabilities(null);
      setIsOwner(false);
      setLoading(false);
    }
  }, []);

  const fetchCapabilities = async () => {
    try {
      const response = await api.get('/v1/tenants/capabilities');
      const data = response.data;

      setCapabilities(data.features || {});
      setIsOwner(data.is_owner || false);
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
