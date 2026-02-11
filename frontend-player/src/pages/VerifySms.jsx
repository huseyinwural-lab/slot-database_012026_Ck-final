import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVerificationStore } from '@/domain';
import { useToast } from '@/components/ToastProvider';

const VerifySms = () => {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const { sendSms, confirmSms, smsState } = useVerificationStore();
  const toast = useToast();
  const navigate = useNavigate();

  const handleSend = async () => {
    const response = await sendSms({ phone });
    if (response.ok) toast.push('SMS kodu gönderildi', 'success');
    else toast.push('SMS gönderilemedi', 'error');
  };

  const handleConfirm = async () => {
    const response = await confirmSms({ phone, code });
    if (response.ok) {
      toast.push('SMS doğrulandı', 'success');
      navigate('/login');
    } else {
      toast.push('Kod hatalı', 'error');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6" data-testid="verify-sms-page">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-black/60 p-6 space-y-4">
        <h2 className="text-xl font-semibold" data-testid="verify-sms-title">SMS Doğrulama</h2>
        <input
          type="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          placeholder="Telefon"
          className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
          data-testid="verify-sms-input"
        />
        <button
          onClick={handleSend}
          className="w-full rounded-lg bg-[var(--app-accent,#19e0c3)] px-4 py-2 text-sm font-semibold text-black"
          data-testid="verify-sms-send"
        >
          Kodu Gönder
        </button>
        <input
          type="text"
          value={code}
          onChange={(event) => setCode(event.target.value)}
          placeholder="Doğrulama Kodu"
          className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
          data-testid="verify-sms-code"
        />
        <button
          onClick={handleConfirm}
          className="w-full rounded-lg bg-[var(--app-cta,#ff8b2c)] px-4 py-2 text-sm font-semibold text-black"
          data-testid="verify-sms-confirm"
        >
          SMS Doğrula
        </button>
        <div className="text-xs text-white/60" data-testid="verify-sms-state">Durum: {smsState}</div>
      </div>
    </div>
  );
};

export default VerifySms;
