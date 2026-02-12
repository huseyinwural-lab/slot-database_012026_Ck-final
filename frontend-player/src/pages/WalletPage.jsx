import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { walletApi } from '@/infra/api/wallet';
import { usePaymentsStore, useVerificationStore } from '@/domain';
import { useToast } from '@/components/ToastProvider';

const WalletPage = () => {
  const [balanceData, setBalance] = useState({ available: 0, held: 0, total: 0, currency: 'USD' });
  const [transactions, setTransactions] = useState([]);
  const { createDeposit, status: payStatus } = usePaymentsStore();
  const { emailState, smsState } = useVerificationStore();
  const toast = useToast();

  const [activeTab, setActiveTab] = useState('deposit');
  const [amount, setAmount] = useState('');
  const [withdrawAddress, setWithdrawAddress] = useState('');

  const fetchWallet = async () => {
    const res = await walletApi.getBalance();
    if (res.ok) {
      setBalance({
        available: res.data.available_real || 0,
        held: res.data.held_real || 0,
        total: res.data.total_real || 0,
        currency: 'USD' // backend default
      });
    }
    const txRes = await walletApi.getTransactions();
    if (txRes.ok) setTransactions(txRes.data.items || []);
  };

  useEffect(() => {
    fetchWallet();
  }, []);

  const handleDeposit = async () => {
    if (emailState !== 'verified' || smsState !== 'verified') {
        toast.push('Verification required', 'error');
        return;
    }
    const res = await createDeposit({ amount: Number(amount), currency: 'USD' });
    if (res?.ok) {
        toast.push('Deposit initiated', 'success');
        if (res.data?.redirect_url) window.location.href = res.data.redirect_url;
        fetchWallet();
        setAmount('');
    } else {
        toast.push('Deposit failed', 'error');
    }
  };

  const handleWithdraw = async () => {
    if (emailState !== 'verified' || smsState !== 'verified') {
        toast.push('Verification required', 'error');
        return;
    }
    if (Number(amount) > balanceData.available) {
        toast.push('Insufficient funds', 'error');
        return;
    }
    const res = await walletApi.requestWithdraw({
        amount: Number(amount),
        method: 'test_bank', // Default for P0
        address: withdrawAddress
    });
    
    if (res.ok) {
        toast.push('Withdrawal requested', 'success');
        fetchWallet();
        setAmount('');
        setWithdrawAddress('');
    } else {
        toast.push(res.error?.message || 'Withdrawal failed', 'error');
    }
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="wallet-page">
        {/* Balance Card */}
        <div className="rounded-2xl border border-white/10 bg-black/40 p-6" data-testid="wallet-balance-card">
          <div className="text-sm text-white/60">Available Balance</div>
          <div className="text-3xl font-semibold text-[var(--app-accent)]" data-testid="wallet-balance">
            {balanceData.available} {balanceData.currency}
          </div>
          {balanceData.held > 0 && (
             <div className="text-xs text-white/40 mt-1">Locked: {balanceData.held} {balanceData.currency}</div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-4 border-b border-white/10">
            <button 
                onClick={() => setActiveTab('deposit')}
                className={`pb-2 px-4 text-sm font-medium ${activeTab === 'deposit' ? 'text-[var(--app-accent)] border-b-2 border-[var(--app-accent)]' : 'text-white/60'}`}
                data-testid="tab-deposit"
            >
                Deposit
            </button>
            <button 
                onClick={() => setActiveTab('withdraw')}
                className={`pb-2 px-4 text-sm font-medium ${activeTab === 'withdraw' ? 'text-[var(--app-accent)] border-b-2 border-[var(--app-accent)]' : 'text-white/60'}`}
                data-testid="tab-withdraw"
            >
                Withdraw
            </button>
        </div>

        {/* Forms */}
        <div className="rounded-2xl border border-white/10 bg-black/40 p-6 space-y-4">
            <div className="text-lg font-semibold capitalize">{activeTab}</div>
            
            <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="Amount"
                className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
                data-testid="amount-input"
            />

            {activeTab === 'withdraw' && (
                <input
                    type="text"
                    value={withdrawAddress}
                    onChange={(e) => setWithdrawAddress(e.target.value)}
                    placeholder="IBAN / Address"
                    className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm"
                    data-testid="address-input"
                />
            )}

            <button
                onClick={activeTab === 'deposit' ? handleDeposit : handleWithdraw}
                className="rounded-lg bg-[var(--app-cta,#ff8b2c)] px-4 py-2 text-sm font-semibold text-black disabled:opacity-60 w-full"
                data-testid="submit-button"
                disabled={!amount || (activeTab === 'withdraw' && !withdrawAddress)}
            >
                {activeTab === 'deposit' ? 'Deposit Now' : 'Request Withdrawal'}
            </button>
        </div>

        {/* History */}
        <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
          <div className="text-lg font-semibold mb-4">History</div>
          <div className="space-y-2">
            {transactions.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between text-sm p-2 border-b border-white/5 last:border-0" data-testid={`tx-${tx.id}`}>
                <div>
                  <div className="font-medium capitalize text-white/90">{tx.type}</div>
                  <div className="text-xs text-white/50">{tx.status} • {new Date(tx.created_at).toLocaleDateString()}</div>
                </div>
                <div className={`font-semibold ${tx.type === 'deposit' ? 'text-green-400' : 'text-red-400'}`}>
                    {tx.type === 'deposit' ? '+' : '-'}{tx.amount}
                </div>
              </div>
            ))}
            {transactions.length === 0 && <div className="text-white/40 text-sm">No transactions</div>}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default WalletPage;
