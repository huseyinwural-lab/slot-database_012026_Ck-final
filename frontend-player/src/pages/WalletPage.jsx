import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { callMoneyAction } from '../services/moneyActions';
import { moneyPathErrorMessage } from '../services/moneyPathErrors';
import { 
  Wallet, ArrowUpRight, ArrowDownLeft, History, CreditCard, DollarSign, 
  ChevronLeft, ChevronRight, RefreshCw, Copy, AlertCircle 
} from 'lucide-react';
import { WithdrawalForm } from '../components/WithdrawalForm';
import { WithdrawalStatus } from '../components/WithdrawalStatus';

const WalletPage = () => {
  const [activeTab, setActiveTab] = useState('deposit');
  const [balance, setBalance] = useState({ 
    available_real: 0, 
    held_real: 0, 
    total_real: 0, 
    currency: 'USD' 
  });
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, total: 0, limit: 10 });
  
  // Form States
  const [depositAmount, setDepositAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('stripe');
  // Withdrawal State
  const [lastPayoutId, setLastPayoutId] = useState(null);
  
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState(null);

  const PLAYER_SCOPE = 'player';

  const fetchWalletData = async (pageNum = 1) => {
    setLoading(true);
    try {
      const [balRes, txRes] = await Promise.all([
        api.get('/player/wallet/balance'),
        api.get(`/player/wallet/transactions?page=${pageNum}&limit=${pagination.limit}`)
      ]);
      
      setBalance(balRes.data);
      setTransactions(txRes.data.items || []);
      setPagination(prev => ({
        ...prev,
        page: pageNum,
        total: txRes.data.meta?.total || 0
      }));
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: 'Veriler yüklenirken hata oluştu.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWalletData(1);
    checkReturnFromStripe();
    checkReturnFromAdyen();
  }, []);

  const checkReturnFromAdyen = () => {
      const query = new URLSearchParams(window.location.search);
      const provider = query.get('provider');
      const resultCode = query.get('resultCode');
      
      if (provider === 'adyen') {
          const txId = query.get('tx_id');

          if (resultCode === 'Authorised') {
               setMessage({ type: 'success', text: 'Adyen Payment Authorised! Balance will update shortly.' });

               // Clean noisy params but preserve tx_id for deterministic wallet contract.
               const url = new URL(window.location.href);
               url.search = '';
               if (txId) url.searchParams.set('tx_id', txId);
               window.history.replaceState({}, document.title, url.toString());

               fetchWalletData(1);
          } else if (resultCode) {
               setMessage({ type: 'error', text: `Adyen Payment Result: ${resultCode}` });

               const url = new URL(window.location.href);
               url.search = '';
               if (txId) url.searchParams.set('tx_id', txId);
               window.history.replaceState({}, document.title, url.toString());
          }
      }
  };

  const checkReturnFromStripe = () => {
      const query = new URLSearchParams(window.location.search);
      const sessionId = query.get('session_id');
      const status = query.get('status');

      const txId = query.get('tx_id');

      if (sessionId && status === 'success') {
          setMessage({ type: 'info', text: 'Verifying payment...' });
          setProcessing(true); // Show processing state
          pollPaymentStatus(sessionId);
      } else if (status === 'cancel') {
          setMessage({ type: 'error', text: 'Payment cancelled.' });

          // Clean URL but preserve tx_id
          const url = new URL(window.location.href);
          url.search = '';
          if (txId) url.searchParams.set('tx_id', txId);
          window.history.replaceState({}, document.title, url.toString());
      }
  };

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
      if (attempts > 10) { // 20 seconds timeout
          setMessage({ type: 'error', text: 'Payment status check timed out. Please check transaction history.' });
          setProcessing(false);
          window.history.replaceState({}, document.title, window.location.pathname);
          fetchWalletData(1);
          return;
      }
      
      try {
          const res = await api.get(`/payments/stripe/checkout/status/${sessionId}`);
          if (res.data.payment_status === 'paid') {
              setMessage({ type: 'success', text: 'Payment Successful!' });
              setProcessing(false);
              window.history.replaceState({}, document.title, window.location.pathname);
              fetchWalletData(1);
          } else if (res.data.status === 'expired' || res.data.status === 'failed') {
               setMessage({ type: 'error', text: 'Payment failed or expired.' });
               setProcessing(false);
               window.history.replaceState({}, document.title, window.location.pathname);
          } else {
              // Retry
              setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2000);
          }
      } catch (e) {
          console.error(e);
          // Retry on error
          setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2000);
      }
  };


  const handlePageChange = (newPage) => {
    if (newPage < 1) return;
    fetchWalletData(newPage);
  };

  const copyToClipboard = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
  };

  const handleDeposit = async (e) => {
    e.preventDefault();
    setProcessing(true);
    setMessage(null);

    try {
       let endpoint = '/payments/stripe/checkout/session';
       if (paymentMethod === 'adyen') {
           endpoint = '/payments/adyen/checkout/session';
       }

       const res = await api.post(
         endpoint,
         {
           amount: parseFloat(depositAmount),
           currency: 'USD',
         }
       );

       const txId = res.data?.tx_id;
       if (!txId) {
         // Fail-early: tx_id is mandatory contract for wallet deposit flows.
         throw new Error('Deposit checkout response missing tx_id');
       }

       // Contract: write tx_id into URL immediately (provider-agnostic) for E2E determinism.
       const url = new URL(window.location.href);
       url.searchParams.set('tx_id', txId);
       window.history.replaceState(null, '', url.toString());

       if (res.data.url) {
           // Redirect
           window.location.href = res.data.url;
       } else {
           throw new Error("No redirect URL returned");
       }
    } catch (err) {
       console.error(err);
       setMessage({ type: 'error', text: moneyPathErrorMessage(err) });
       setProcessing(false);
    }
  };

  // Get Player ID
  const storedPlayer = localStorage.getItem('player_user');
  const player = storedPlayer ? JSON.parse(storedPlayer) : null;
  const playerId = player?.id;
  const playerEmail = player?.email || 'user@example.com';

  const handlePayoutSuccess = (data) => {
      setLastPayoutId(data.payout_id);
      fetchWalletData(1); // Refresh history
  };

  const totalPages = Math.ceil(pagination.total / pagination.limit);

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-10">
      {/* Header */}
      <div className="bg-secondary/50 p-6 rounded-2xl border border-white/10 flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Wallet className="text-primary" /> My Wallet
          </h1>
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
