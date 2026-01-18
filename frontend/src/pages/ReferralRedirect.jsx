import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

const COOKIE_NAME = 'aff_ref';

const setCookie = (name, value, days) => {
  const expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
  const secure = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `${name}=${encodeURIComponent(value)}; Expires=${expires}; Path=/; SameSite=Lax${secure}`;
};

const ReferralRedirect = () => {
  const { code } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const run = async () => {
      try {
        const res = await api.get(`/v1/affiliates/r/${code}`);
        const ts = Date.now();
        const cookieValue = `${code}|${res.data.offer_id}|${ts}`;
        setCookie(COOKIE_NAME, cookieValue, 90);

        const dest = res.data.landing_path || '/';
        window.location.href = dest;
      } catch {
        navigate('/');
      }
    };

    if (code) run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  return (
    <div className="p-6">
      <div className="text-lg font-semibold">Redirecting…</div>
      <div className="text-muted-foreground text-sm">Setting referral cookie and sending you to the landing page.</div>
    </div>
  );
};

export default ReferralRedirect;
