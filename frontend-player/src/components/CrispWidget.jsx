import { useEffect } from 'react';
import { env } from '@/config/env';
import { getStoredUser } from '@/domain/auth/session';

export const CrispWidget = ({ onReady }) => {
  useEffect(() => {
    if (!env.crispWebsiteId) return;
    window.$crisp = [];
    window.CRISP_WEBSITE_ID = env.crispWebsiteId;
    const script = document.createElement('script');
    script.src = 'https://client.crisp.chat/l.js';
    script.async = true;
    script.onload = () => {
      const user = getStoredUser();
      if (user && window.$crisp) {
        window.$crisp.push(['set', 'user:email', [user.email]]);
        if (user.username) {
          window.$crisp.push(['set', 'user:nickname', [user.username]]);
        }
        if (user.phone) {
          window.$crisp.push(['set', 'user:phone', [user.phone]]);
        }
        window.$crisp.push([
          'set',
          'session:data',
          [[
            ['playerId', user.id || ''],
            ['tenantId', user.tenant_id || 'default_casino'],
            ['vipLevel', user.vip_level || 'standard'],
          ]],
        ]);
      }
      onReady?.();
    };
    document.body.appendChild(script);
    return () => {
      script.remove();
    };
  }, [onReady]);

  return null;
};
