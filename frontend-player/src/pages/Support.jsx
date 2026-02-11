import { useState } from 'react';
import Layout from '@/components/Layout';
import { CrispWidget } from '@/components/CrispWidget';
import { env } from '@/config/env';
import { useSupportStore } from '@/domain';
import { useToast } from '@/components/ToastProvider';

const Support = () => {
  const [message, setMessage] = useState('');
  const { submitTicket } = useSupportStore();
  const toast = useToast();

  const handleTicket = async () => {
    const response = await submitTicket({ message });
    if (response.ok) {
      toast.push('Destek talebi alındı', 'success');
      setMessage('');
    } else {
      toast.push('Destek talebi gönderilemedi', 'error');
    }
  };

  return (
      <div className="space-y-6" data-testid="support-page">
        <h2 className="text-2xl font-semibold" data-testid="support-title">Canlı Destek</h2>
        {env.crispWebsiteId ? (
          <div className="rounded-xl border border-white/10 bg-black/40 p-6" data-testid="support-crisp">
            <CrispWidget />
            <p className="text-sm text-white/60">Sağ alttaki chat ikonundan destek alabilirsiniz.</p>
          </div>
        ) : (
          <div className="rounded-xl border border-white/10 bg-black/40 p-6 space-y-4" data-testid="support-ticket">
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Destek talebinizi yazın"
              className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
              rows={4}
              data-testid="support-ticket-input"
            />
            <button
              onClick={handleTicket}
              className="rounded-lg bg-[var(--app-accent,#19e0c3)] px-4 py-2 text-sm font-semibold text-black"
              data-testid="support-ticket-submit"
            >
              Talep Gönder
            </button>
          </div>
        )}
      </div>
  );
};

export default Support;
