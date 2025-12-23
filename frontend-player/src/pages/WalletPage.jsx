import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { callMoneyAction } from '../services/moneyActions';
import { moneyPathErrorMessage } from '../services/moneyPathErrors';
import { 
  Wallet, ArrowUpRight, ArrowDownLeft, History, CreditCard, DollarSign, 
  ChevronLeft, ChevronRight, RefreshCw, Copy, AlertCircle 
} from 'lucide-react';

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
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [withdrawAddress, setWithdrawAddress] = useState('');
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState(null);
  const [actionStatus, setActionStatus] = useState({}); // key -> { status, message }

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
  }, []);

  const handlePageChange = (newPage) => {
    if (newPage < 1) return;
    fetchWalletData(newPage);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const handleDeposit = async (e) => {
    e.preventDefault();
    setProcessing(true);
    setMessage(null);

    const storedPlayer = localStorage.getItem('player_user');
    const player = storedPlayer ? JSON.parse(storedPlayer) : null;
    const playerId = player?.id || 'self';
    const scope = PLAYER_SCOPE;
    const action = 'deposit';

    const key = `${scope}:${playerId}:${action}`;
    setActionStatus((prev) => ({ ...prev, [key]: { status: 'in_flight' } }));

    try {
      await callMoneyAction({
        scope,
        id: playerId,
        action,
        requestFn: (idemKey) =>
          api.post('/player/wallet/deposit', {
            amount: parseFloat(depositAmount),
            method: 'credit_card', // Mock method
          }, {
            headers: {
              'Idempotency-Key': idemKey,
            },
          }),
        onStatus: (status) => {
          setActionStatus((prev) => ({
            ...prev,
            [key]: { status: status.status || status, message: status.message },
          }));
        },
      });
      setMessage({ type: 'success', text: 'Deposit successful!' });
      setDepositAmount('');
      fetchWalletData(1); // Refresh balance
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: moneyPathErrorMessage(err) });
    } finally {
      setProcessing(false);
    }
  };

  const handleWithdraw = async (e) => {
    e.preventDefault();
    setProcessing(true);
    setMessage(null);

    const storedPlayer = localStorage.getItem('player_user');
    const player = storedPlayer ? JSON.parse(storedPlayer) : null;
    const playerId = player?.id || 'self';
    const scope = PLAYER_SCOPE;
    const action = 'withdraw';

    const key = `${scope}:${playerId}:${action}`;
    setActionStatus((prev) => ({ ...prev, [key]: { status: 'in_flight' } }));

    try {
      await callMoneyAction({
        scope,
        id: playerId,
        action,
        requestFn: (idemKey) =>
          api.post('/player/wallet/withdraw', {
  const totalPages = Math.ceil(pagination.total / pagination.limit);

            amount: parseFloat(withdrawAmount),
            method: 'crypto',
            address: withdrawAddress,
          }, {
            headers: {
              'Idempotency-Key': idemKey,
            },
          }),
        onStatus: (status) => {
          setActionStatus((prev) => ({
            ...prev,
            [key]: { status: status.status || status, message: status.message },
          }));
        },
      });
      setMessage({ type: 'success', text: 'Withdrawal requested successfully!' });
      setWithdrawAmount('');
      setWithdrawAddress('');
      fetchWalletData(1);
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: moneyPathErrorMessage(err) });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header & Balance */}
      <div className="bg-secondary/50 p-6 rounded-2xl border border-white/10 flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Wallet className="text-primary" /> My Wallet
          </h1>
          <p className="text-muted-foreground">Manage your funds and transactions</p>
        </div>
        <div className="bg-black/40 px-6 py-3 rounded-xl border border-primary/20 text-center">
          <div className="text-xs text-muted-foreground uppercase tracking-wider">Total Balance</div>
          <div className="text-3xl font-mono text-green-400 font-bold">
            ${balance.balance_real?.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        {/* Actions Column */}
        <div className="md:col-span-2 space-y-6">
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
              <div className={`mb-4 p-3 rounded-lg text-sm ${message.type === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                {message.text}
              </div>
            )}

            {activeTab === 'deposit' ? (
              <form onSubmit={handleDeposit} className="space-y-4">
                <h3 className="text-xl font-semibold flex items-center gap-2">
                  <ArrowDownLeft className="text-green-500" /> Deposit Funds
                </h3>
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
                      className="w-full bg-black/20 border border-white/10 rounded-lg pl-10 p-3 focus:border-primary focus:outline-none"
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
                      className="bg-white/5 hover:bg-white/10 py-2 rounded-lg text-sm border border-white/5"
                    >
                      ${amt}
                    </button>
                  ))}
                </div>
                <button type="submit" disabled={processing} className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-lg transition-colors">
                  {processing ? 'Processing...' : 'Pay Now'}
                </button>
                <p className="text-xs text-center text-muted-foreground mt-2">
                  <CreditCard className="w-3 h-3 inline mr-1" /> Secure Payment via MockGateway
                </p>
              </form>
            ) : (
              <form onSubmit={handleWithdraw} className="space-y-4">
                <h3 className="text-xl font-semibold flex items-center gap-2">
                  <ArrowUpRight className="text-red-500" /> Request Withdrawal
                </h3>
                <div>
                  <label className="block text-sm text-muted-foreground mb-1">Amount ($)</label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-3 w-5 h-5 text-muted-foreground" />
                    <input 
                      type="number" 
                      min="10" 
                      max={balance.balance_real}
                      step="0.01"
                      value={withdrawAmount}
                      onChange={e => setWithdrawAmount(e.target.value)}
                      className="w-full bg-black/20 border border-white/10 rounded-lg pl-10 p-3 focus:border-primary focus:outline-none"
                      placeholder={`Max $${balance.balance_real?.toFixed(2)}`}
                      required 
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-muted-foreground mb-1">Wallet Address / IBAN</label>
                  <input 
                    type="text" 
                    value={withdrawAddress}
                    onChange={e => setWithdrawAddress(e.target.value)}
                    className="w-full bg-black/20 border border-white/10 rounded-lg p-3 focus:border-primary focus:outline-none"
                    placeholder="TR..."
                    required 
                  />
                </div>
                <button type="submit" disabled={processing} className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 rounded-lg transition-colors">
                  {processing ? 'Submitting...' : 'Request Payout'}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* History Column */}
        <div className="space-y-4">
          <h3 className="font-semibold flex items-center gap-2 text-lg">
            <History className="w-5 h-5 text-primary" /> Recent Transactions
          </h3>
          <div className="bg-secondary/20 rounded-xl border border-white/5 overflow-hidden">
            {transactions.length === 0 ? (
              <div className="p-6 text-center text-muted-foreground text-sm">No transactions yet.</div>
            ) : (
              <div className="divide-y divide-white/5">
                {transactions.slice(0, 5).map(tx => (
                  <div key={tx.id} className="p-4 flex justify-between items-center hover:bg-white/5 transition-colors">
                    <div>
                      <div className="font-medium text-sm flex items-center gap-2 capitalize">
                        {tx.type === 'deposit' 
                          ? <ArrowDownLeft className="w-3 h-3 text-green-500" /> 
                          : <ArrowUpRight className="w-3 h-3 text-red-500" />
                        }
                        {tx.type}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(tx.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`font-mono font-bold text-sm ${tx.type === 'deposit' ? 'text-green-400' : 'text-white'}`}>
                        {tx.type === 'deposit' ? '+' : '-'}${tx.amount.toFixed(2)}
                      </div>
                      <div className={`text-[10px] px-2 py-0.5 rounded-full inline-block mt-1 ${
                        tx.status === 'completed' ? 'bg-green-500/20 text-green-400' : 
                        tx.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' : 
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {tx.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WalletPage;
