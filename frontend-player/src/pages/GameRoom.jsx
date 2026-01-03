import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import api from '../services/api';

const GameRoom = () => {
  const { id: sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  
  // Mock Game State
  const [balance, setBalance] = useState(0);
  const [lastWin, setLastWin] = useState(0);
  const [spinning, setSpinning] = useState(false);
  const [bet, setBet] = useState(1.0);

  const handleSpin = async () => {
      setSpinning(true);
      setLastWin(0);
      try {
          // Simulate game client logic
          // Determine local outcome (RNG) just for fun, but real logic is backend
          const isWin = Math.random() > 0.7; // 30% win rate
          const winAmount = isWin ? bet * (Math.floor(Math.random() * 5) + 2) : 0;
          
          const res = await api.post('/mock-provider/spin', {
              session_id: sessionId,
              amount: bet,
              currency: "USD"
          });

          setBalance(res.data.balance);
          setLastWin(res.data.win);
      } catch (err) {
          alert(err.response?.data?.detail || "Spin failed");
      } finally {
          setSpinning(false);
      }
  };

  useEffect(() => {
      // Initial balance check
      api.get('/player/wallet/balance').then(res => setBalance(res.data.total_real));
  }, []);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-black">
      {/* Game Header */}
      <div className="bg-zinc-900 border-b border-zinc-800 p-2 flex items-center justify-between">
        <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
            <ArrowLeft className="w-4 h-4 mr-2" /> Lobby
        </Button>
        <div className="font-mono font-bold text-yellow-500">
            BAL: ${balance.toFixed(2)}
        </div>
      </div>

      {/* Game Area (Mock Iframe) */}
      <div className="flex-1 flex items-center justify-center bg-zinc-950 relative overflow-hidden">
          {/* Background FX */}
          <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-purple-900 via-black to-black"></div>
          
          <div className="w-[800px] h-[600px] bg-zinc-900 rounded-xl border border-zinc-700 shadow-2xl relative flex flex-col">
              {/* Mock Reel Area */}
              <div className="flex-1 flex items-center justify-center p-10 space-x-4">
                  {[1, 2, 3].map(i => (
                      <div key={i} className="w-1/3 h-full bg-black rounded-lg border border-zinc-800 flex items-center justify-center text-6xl animate-pulse">
                          {spinning ? "❓" : (lastWin > 0 ? "🍒" : "🍋")}
                      </div>
                  ))}
              </div>
              
              {/* Controls */}
              <div className="h-24 bg-zinc-800 border-t border-zinc-700 p-4 flex items-center justify-between">
                  <div className="space-x-2">
                      <span className="text-xs text-muted-foreground uppercase">Bet</span>
                      <div className="flex gap-1">
                          {[1, 2, 5, 10].map(amt => (
                              <button 
                                key={amt}
                                onClick={() => setBet(amt)}
                                className={`w-10 h-10 rounded border text-sm font-bold ${bet === amt ? 'bg-yellow-500 text-black border-yellow-600' : 'bg-zinc-700 hover:bg-zinc-600 border-zinc-600'}`}
                              >
                                  ${amt}
                              </button>
                          ))}
                      </div>
                  </div>
                  
                  <div className="text-center">
                      <div className="text-xs text-muted-foreground uppercase">Win</div>
                      <div className={`text-2xl font-bold ${lastWin > 0 ? 'text-green-400 animate-bounce' : 'text-zinc-500'}`}>
                          ${lastWin.toFixed(2)}
                      </div>
                  </div>

                  <Button 
                    size="lg" 
                    className="w-32 h-16 text-xl font-bold bg-green-600 hover:bg-green-500 rounded-full shadow-lg border-b-4 border-green-800 active:border-b-0 active:translate-y-1 transition-all"
                    onClick={handleSpin}
                    disabled={spinning}
                  >
                    {spinning ? '...' : 'SPIN'}
                  </Button>
              </div>
          </div>
      </div>
    </div>
  );
};

export default GameRoom;
