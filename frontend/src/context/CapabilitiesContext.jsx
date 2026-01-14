import React, { createContext, useState, useEffect, useContext, useRef, useCallback } from 'react';
import api from '../services/api';

export const CapabilitiesContext = createContext();

export const CapabilitiesProvider = ({ children }) => {
  const [capabilitiesObject, setCapabilitiesObject] = useState({});
  const [capabilitiesList, setCapabilitiesList] = useState([]);
  const [isOwner, setIsOwner] = useState(false);
  const [tenantRole, setTenantRole] = useState(null);
  const [tenantName, setTenantName] = useState('');
  const [loading, setLoading] = useState(true);

  // In-memory cache (P3-FE-CAP-01)
  const cacheRef = useRef({
    data: null,
    at: 0,
    tenantKey: null,
  });

  const TTL_MS = 60_000;

  const getTenantKey = () => {
    if (typeof window === 'undefined') return 'ssr';
    return localStorage.getItem('impersonate_tenant_id') || 'default';
  };

  const applyCapabilities = useCallback((data) => {
    const featuresObj = data.features || {};
    setCapabilitiesObject(featuresObj);
    setCapabilitiesList(Object.keys(featuresObj));
    setIsOwner(data.is_owner || false);
    setTenantRole(data.tenant_role || null);
    setTenantName(data.tenant_name || 'Casino');
  }, []);

  const invalidateCapabilities = useCallback(() => {
    cacheRef.current = { data: null, at: 0, tenantKey: null };
  }, []);

  const refreshCapabilities = useCallback(async ({ force = false } = {}) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null;
    if (!token) {
      setCapabilitiesObject({});
      setCapabilitiesList([]);
      setIsOwner(false);
      setLoading(false);
      return;
    }

    const tenantKey = getTenantKey();
    const cached = cacheRef.current;
    const now = Date.now();

    const canUseCache =
      !force &&
      cached.data &&
      cached.tenantKey === tenantKey &&
      now - cached.at < TTL_MS;

    if (canUseCache) {
      applyCapabilities(cached.data);
      setLoading(false);
      return;
    }

    // Mark loading at the start so consumers can gate UI.
    setLoading(true);

    try {
      const response = await api.get('/v1/tenants/capabilities');
      const data = response.data;
      cacheRef.current = { data, at: now, tenantKey };
      applyCapabilities(data);
    } catch (error) {
      console.error('Failed to fetch capabilities:', error);
      // keep authenticated; capabilities empty
      setCapabilitiesObject({});
      setCapabilitiesList([]);
      setIsOwner(false);
    } finally {
      setLoading(false);
    }
  }, [applyCapabilities]);

  // Initial load
  useEffect(() => {
    refreshCapabilities({ force: false });
  }, [refreshCapabilities]);

  // Refetch when window gets focus (login flow) — only if cache empty or TTL passed
  useEffect(() => {
    const handleFocus = () => {
      refreshCapabilities({ force: false });
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [refreshCapabilities]);

  const hasFeature = (featureKey) => {
    if (!capabilitiesObject) return false;
    return capabilitiesObject[featureKey] === true;
  };

  // Centralized feature flag resolver (single source of truth for UI capability checks)
  // Defaults to false when a key is missing.
  const featureFlags = {
    gamesConfigEnabled: hasFeature('GAMES_CONFIG_ENABLED') === true,
    gamesAnalyticsEnabled: hasFeature('GAMES_ANALYTICS_ENABLED') === true,
  };

  return (
    <CapabilitiesContext.Provider
      value={{
        capabilities: capabilitiesObject, // Keep backward compatibility
        capabilitiesObject,
        capabilitiesList,
        loading,
        isOwner,
        tenantRole,
        tenantName,
        hasFeature,
        featureFlags,
        // P3-FE-CAP-01
        refreshCapabilities,
        invalidateCapabilities,
        refetch: refreshCapabilities
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
