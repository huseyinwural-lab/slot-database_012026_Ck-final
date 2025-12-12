import React, { createContext, useState, useEffect, useContext } from 'react';
import { AuthContext } from './AuthContext';
import api from '../services/api';

export const CapabilitiesContext = createContext();

export const CapabilitiesProvider = ({ children }) => {
  const { user } = useContext(AuthContext);
  const [capabilities, setCapabilities] = useState(null);
  const [isOwner, setIsOwner] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchCapabilities();
    } else {
      setCapabilities(null);
      setIsOwner(false);
      setLoading(false);
    }
  }, [user]);

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
