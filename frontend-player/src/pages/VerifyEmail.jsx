import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVerificationStore } from '@/domain';
import { useToast } from '@/components/ToastProvider';

const VerifyEmail = () => {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const { sendEmail, confirmEmail, emailState } = useVerificationStore();
  const toast = useToast();
  const navigate = useNavigate();

  const handleSend = async () => {
    const response = await sendEmail({ email });
    if (response.ok) toast.push('Email kodu gönderildi', 'success');
    else toast.push('Email gönderilemedi', 'error');
  };

  const handleConfirm = async () => {
    const response = await confirmEmail({ email, code });
    if (response.ok) {
      toast.push('Email doğrulandı', 'success');
      navigate('/verify/sms');
    } else {
      toast.push('Kod hatalı', 'error');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6" data-testid="verify-email-page">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-black/60 p-6 space-y-4">
        <h2 className="text-xl font-semibold" data-testid="verify-email-title">Email Doğrulama</h2>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Email"
          className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
          data-testid="verify-email-input"
        />
        <button
          onClick={handleSend}
          className="w-full rounded-lg bg-[var(--app-accent,#19e0c3)] px-4 py-2 text-sm font-semibold text-black"
          data-testid="verify-email-send"
        >
          Kodu Gönder
        </button>
        <input
          type="text"
          value={code}
          onChange={(event) => setCode(event.target.value)}
          placeholder="Doğrulama Kodu"
          className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
          data-testid="verify-email-code"
        />
        <button
          onClick={handleConfirm}
          className="w-full rounded-lg bg-[var(--app-cta,#ff8b2c)] px-4 py-2 text-sm font-semibold text-black"
          data-testid="verify-email-confirm"
        >
          Email Doğrula
        </button>
        <div className="text-xs text-white/60" data-testid="verify-email-state">Durum: {emailState}</div>
      </div>
    </div>
  );
};

export default VerifyEmail;
