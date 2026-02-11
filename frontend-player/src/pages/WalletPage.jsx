import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { useWalletStore, usePaymentsStore, useVerificationStore } from '@/domain';
import { useToast } from '@/components/ToastProvider';

const WalletPage = () => {
  const { status, balance, currency, transactions, fetchBalance, fetchTransactions } = useWalletStore();
  const { status: paymentStatus, createDeposit } = usePaymentsStore();
  const { emailState, smsState } = useVerificationStore();
  const [amount, setAmount] = useState('');
  const toast = useToast();

  useEffect(() => {
    fetchBalance();
    fetchTransactions();
  }, [fetchBalance, fetchTransactions]);

  const handleDeposit = async () => {
    if (emailState !== 'verified' || smsState !== 'verified') {
      toast.push('Doğrulama tamamlanmadan depozit yapılamaz', 'error');
      return;
    }
    const response = await createDeposit({ amount: Number(amount), currency: currency || 'USD' });
    if (response.ok) {
      toast.push('Depozit başlatıldı', 'success');
      fetchBalance();
    } else {
      toast.push('Depozit başarısız', 'error');
    }
  };

  return (
      <div className="space-y-6" data-testid="wallet-page">
        <div className="rounded-2xl border border-white/10 bg-black/40 p-6" data-testid="wallet-balance-card">
          <div className="text-sm text-white/60">Güncel Bakiye</div>
          <div className="text-3xl font-semibold" data-testid="wallet-balance">{balance} {currency}</div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-black/40 p-6 space-y-4">
          <div className="text-lg font-semibold" data-testid="wallet-deposit-title">Deposit</div>
          <input
            type="number"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            placeholder="Miktar"
            className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
            data-testid="wallet-deposit-input"
          />
          <button
            onClick={handleDeposit}
            className="rounded-lg bg-[var(--app-cta,#ff8b2c)] px-4 py-2 text-sm font-semibold text-black disabled:opacity-60"
            data-testid="wallet-deposit-button"
            disabled={!amount}
          >
            {paymentStatus === 'pending' ? 'Beklemede...' : 'Depozit Başlat'}
          </button>
        </div>

        <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
          <div className="text-lg font-semibold" data-testid="wallet-transactions-title">İşlem Geçmişi</div>
          {status === 'loading' && <div className="text-sm text-white/60">Yükleniyor...</div>}
          {status !== 'loading' && transactions.length === 0 && (
            <div className="text-sm text-white/60" data-testid="wallet-transactions-empty">Aktif işlem bulunmamaktadır</div>
          )}
          <div className="mt-4 space-y-2">
            {transactions.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between text-sm" data-testid={`wallet-transaction-${tx.id}`}>
                <div>
                  <div className="font-medium" data-testid={`wallet-transaction-${tx.id}-type`}>{tx.type}</div>
                  <div className="text-xs text-white/50" data-testid={`wallet-transaction-${tx.id}-date`}>{tx.created_at}</div>
                </div>
                <div className="font-semibold" data-testid={`wallet-transaction-${tx.id}-amount`}>{tx.amount}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default WalletPage;
