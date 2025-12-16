import { useEffect, useState } from 'react';
import api from '../services/api';

// Geçici tenant context hook'u.
// Şimdilik backend gerçek auth yok, bu yüzden basit bir GET /v1/tenants ile
// varsayılan olarak default_casino'yı ve varsa demo_renter'ı kullanıyoruz.

export function useTenant() {
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/v1/tenants/');
        const data = res.data || {};
        const items = data.items || [];
        // Geçici mantık: ilk owner'ı current tenant kabul et
        const owner = items.find((t) => t.type === 'owner');
        const renter = items.find((t) => t.type === 'renter');
        setTenant(owner || renter || null);
      } catch (e) {
        console.error(e);
        setError(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return { tenant, loading, error };
}
