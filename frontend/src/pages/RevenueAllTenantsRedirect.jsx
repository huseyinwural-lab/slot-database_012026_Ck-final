import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

// Phase C: Keep scope limited to /revenue and /my-revenue.
// Redirect legacy internal links to the existing revenue pages.
const RevenueAllTenantsRedirect = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const search = location.search || '';
    navigate(`/revenue${search}`, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
};

export default RevenueAllTenantsRedirect;
