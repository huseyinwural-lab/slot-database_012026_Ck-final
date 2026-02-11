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
    <Layout>
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
            className="rounded-lg bg-[var(--app-cta,#ff8b2c)] px-4 py-2 text-sm font-semibold text-black"
            data-testid="wallet-deposit-button"
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
          <p className="text-muted-foreground">Manage your funds and transactions</p>
        </div>
        <button 
          onClick={() => fetchWalletData(pagination.page)}
          className="p-2 bg-white/5 hover:bg-white/10 rounded-full transition-colors"
          title="Refresh Data"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-black/40 p-6 rounded-xl border border-white/5">
          <div className="text-sm text-muted-foreground uppercase tracking-wider mb-1">Available Balance</div>
          <div className="text-3xl font-mono text-white font-bold">
            ${(balance.available_real || 0).toFixed(2)}
          </div>
          <div className="text-xs text-green-400 mt-2 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" /> Ready to play or withdraw
          </div>
        </div>
        <div className="bg-black/40 p-6 rounded-xl border border-white/5">
          <div className="text-sm text-muted-foreground uppercase tracking-wider mb-1">Held Balance</div>
          <div className="text-3xl font-mono text-yellow-500 font-bold">
            ${(balance.held_real || 0).toFixed(2)}
          </div>
          <div className="text-xs text-yellow-400/70 mt-2 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" /> Locked in pending withdrawals
          </div>
        </div>
        <div className="bg-black/40 p-6 rounded-xl border border-primary/20 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Wallet className="w-24 h-24 text-primary" />
          </div>
          <div className="text-sm text-muted-foreground uppercase tracking-wider mb-1">Total Balance</div>
          <div className="text-3xl font-mono text-primary font-bold">
            ${(balance.total_real || 0).toFixed(2)}
          </div>
          <div className="text-xs text-primary/70 mt-2">
            Net Asset Value
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Actions Column */}
        <div className="lg:col-span-1 space-y-6">
          {/* Tabs */}
          <div className="flex bg-secondary/30 p-1 rounded-lg">
            <button 
              onClick={() => setActiveTab('deposit')}
              className={`flex-1 py-2 rounded-md font-medium text-sm transition-all ${activeTab === 'deposit' ? 'bg-primary text-white shadow-lg' : 'hover:bg-white/5 text-muted-foreground'}`}
            >
              Deposit
            </button>
            <button 
              onClick={() => setActiveTab('withdraw')}
              className={`flex-1 py-2 rounded-md font-medium text-sm transition-all ${activeTab === 'withdraw' ? 'bg-primary text-white shadow-lg' : 'hover:bg-white/5 text-muted-foreground'}`}
            >
              Withdraw
            </button>
          </div>

          {/* Action Forms */}
          <div className="bg-secondary/20 border border-white/5 rounded-xl p-6">
            {message && (
              <div className={`mb-4 p-3 rounded-lg text-sm flex items-start gap-2 ${message.type === 'success' ? 'bg-green-500/20 text-green-400' : message.type === 'error' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                {message.text}
              </div>
            )}

            {activeTab === 'deposit' ? (
              <form onSubmit={handleDeposit} className="space-y-4">
                <h3 className="text-xl font-semibold flex items-center gap-2">
                  <ArrowDownLeft className="text-green-500" /> Deposit Funds
                </h3>
                
                {/* Method Selector */}
                <div>
                   <label className="block text-sm text-muted-foreground mb-1">Payment Method</label>
                   <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setPaymentMethod('stripe')}
                        className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${paymentMethod === 'stripe' ? 'bg-primary/20 border-primary text-primary' : 'bg-black/20 border-white/10 hover:bg-white/5'}`}
                      >
                         Credit Card (Stripe)
                      </button>
                      <button
                        type="button"
                        onClick={() => setPaymentMethod('adyen')}
                        className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${paymentMethod === 'adyen' ? 'bg-primary/20 border-primary text-primary' : 'bg-black/20 border-white/10 hover:bg-white/5'}`}
                      >
                         Adyen (All Methods)
                      </button>
                   </div>
                </div>

                <div>
                  <label className="block text-sm text-muted-foreground mb-1">Amount ($)</label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-3 w-5 h-5 text-muted-foreground" />
                    <input 
                      type="number" 
                      min="10" 
                      step="0.01"
                      value={depositAmount}
                      onChange={e => setDepositAmount(e.target.value)}
                      className="w-full bg-black/20 border border-white/10 rounded-lg pl-10 p-3 focus:border-primary focus:outline-none transition-colors"
                      placeholder="Min $10.00"
                      required 
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[50, 100, 500].map(amt => (
                    <button 
                      key={amt} 
                      type="button" 
                      onClick={() => setDepositAmount(amt)}
                      className="bg-white/5 hover:bg-white/10 py-2 rounded-lg text-sm border border-white/5 transition-colors"
                    >
                      ${amt}
                    </button>
                  ))}
                </div>
                <button type="submit" disabled={processing} className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-lg transition-colors disabled:opacity-50">
                  {processing ? 'Redirecting...' : `Pay with ${paymentMethod === 'stripe' ? 'Stripe' : 'Adyen'}`}
                </button>
                <p className="text-xs text-center text-muted-foreground mt-2">
                  <CreditCard className="w-3 h-3 inline mr-1" /> Secure Payment via {paymentMethod === 'stripe' ? 'Stripe' : 'Adyen'}
                </p>
              </form>
            ) : (
              // WITHDRAW TAB - INTEGRATED WITHDRAWAL FORM
              lastPayoutId ? (
                <div className="space-y-4">
                  <WithdrawalStatus payoutId={lastPayoutId} />
                  <button 
                    onClick={() => setLastPayoutId(null)}
                    className="w-full bg-white/5 hover:bg-white/10 text-white font-bold py-2 rounded-lg transition-colors"
                  >
                    Start New Withdrawal
                  </button>
                </div>
              ) : (
                <WithdrawalForm 
                  playerId={playerId} 
                  playerEmail={playerEmail} 
                  onSuccess={handlePayoutSuccess}
                />
              )
            )}
          </div>
        </div>

        {/* History Column (Wider) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold flex items-center gap-2 text-lg">
              <History className="w-5 h-5 text-primary" /> Transaction History
            </h3>
            <span className="text-xs text-muted-foreground">Showing {transactions.length} records</span>
          </div>
          
          <div className="bg-secondary/20 rounded-xl border border-white/5 overflow-hidden">
            {transactions.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">
                <History className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p>No transactions found.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-white/5 text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3">Type</th>
                      <th className="px-4 py-3">Amount</th>
                      <th className="px-4 py-3">State</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3 text-right">ID</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {transactions.map(tx => (
                      <tr key={tx.id} className="hover:bg-white/5 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {tx.type === 'deposit' 
                              ? <ArrowDownLeft className="w-4 h-4 text-green-500" /> 
                              : <ArrowUpRight className="w-4 h-4 text-red-500" />
                            }
                            <span className="capitalize">{tx.type}</span>
                          </div>
                        </td>
                        <td className={`px-4 py-3 font-mono font-bold ${tx.type === 'deposit' ? 'text-green-400' : 'text-white'}`}>
                          {tx.type === 'deposit' ? '+' : '-'}${tx.amount.toFixed(2)}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full inline-block uppercase tracking-wide ${
                            tx.state === 'completed' || tx.state === 'paid' ? 'bg-green-500/20 text-green-400' : 
                            tx.state === 'pending' || tx.state === 'requested' || tx.state === 'created' || tx.state === 'payout_submitted' ? 'bg-yellow-500/20 text-yellow-400' : 
                            'bg-red-500/20 text-red-400'
                          }`}>
                            {tx.state}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs whitespace-nowrap">
                          {new Date(tx.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button 
                            onClick={() => copyToClipboard(tx.id)}
                            className="text-xs text-muted-foreground hover:text-white flex items-center gap-1 ml-auto"
                            title="Copy ID"
                          >
                            {tx.id.slice(0, 8)}... <Copy className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pagination Controls */}
          {pagination.total > 0 && (
            <div className="flex justify-between items-center pt-2">
              <button 
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page === 1 || loading}
                className="flex items-center gap-1 px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                aria-label="Previous Page"
              >
                <ChevronLeft className="w-4 h-4" /> Previous
              </button>
              <span className="text-sm text-muted-foreground">
                Page {pagination.page} of {totalPages || 1}
              </span>
              <button 
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page >= totalPages || loading}
                className="flex items-center gap-1 px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                aria-label="Next Page"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WalletPage;
