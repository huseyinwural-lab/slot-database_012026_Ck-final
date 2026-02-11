import { useEffect } from 'react';
import { env } from '@/config/env';

export const CrispWidget = ({ onReady }) => {
  useEffect(() => {
    if (!env.crispWebsiteId) return;
    window.$crisp = [];
    window.CRISP_WEBSITE_ID = env.crispWebsiteId;
    const script = document.createElement('script');
    script.src = 'https://client.crisp.chat/l.js';
    script.async = true;
    script.onload = () => onReady?.();
    document.body.appendChild(script);
    return () => {
      script.remove();
    };
  }, [onReady]);

  return null;
};
