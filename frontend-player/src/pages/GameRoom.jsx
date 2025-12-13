import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Maximize, Minimize, X, Loader2, RefreshCw } from 'lucide-react';

const GameRoom = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [launchUrl, setLaunchUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fullScreen, setFullScreen] = useState(false);
  
  // Get user for balance display
  const user = JSON.parse(localStorage.getItem('player_user') || '{}');

  useEffect(() => {
    const launch = async () => {
      try {
        const res = await api.get(`/player/games/${id}/launch`);
        setLaunchUrl(res.data.launch_url);
      } catch (err) {
        console.error(err);
        setError("Failed to launch game. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    launch();
  }, [id]);

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setFullScreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
        setFullScreen(false);
      }
    }
  };

  return (
    <div className={`fixed inset-0 z-50 bg-black flex flex-col ${fullScreen ? 'p-0' : 'p-4'}`}>
      {/* Game Header */}
      <div className="h-14 bg-secondary/90 backdrop-blur border-b border-white/10 flex items-center justify-between px-6 rounded-t-xl mx-auto w-full max-w-[1400px]">
        <div className="flex items-center gap-4">
            <span className="font-bold text-lg">Game Room</span>
            <div className="h-4 w-px bg-white/20"></div>
            <span className="text-sm font-mono text-green-400">Bal: ${user.balance_real?.toFixed(2) || '0.00'}</span>
        </div>
        
        <div className="flex items-center gap-2">
            <button 
                onClick={() => window.location.reload()} 
                className="p-2 hover:bg-white/10 rounded-full transition-colors" 
                title="Reload Game"
            >
                <RefreshCw className="w-5 h-5" />
            </button>
            <button 
                onClick={toggleFullScreen} 
                className="p-2 hover:bg-white/10 rounded-full transition-colors" 
                title="Fullscreen"
            >
                {fullScreen ? <Minimize className="w-5 h-5" /> : <Maximize className="w-5 h-5" />}
            </button>
            <button 
                onClick={() => navigate('/')} 
                className="bg-red-600/20 hover:bg-red-600 text-red-500 hover:text-white px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-2"
            >
                <X className="w-4 h-4" /> Exit
            </button>
        </div>
      </div>

      {/* Game Container */}
      <div className="flex-1 bg-black relative rounded-b-xl overflow-hidden mx-auto w-full max-w-[1400px] border border-t-0 border-white/10">
        {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
                <Loader2 className="w-10 h-10 animate-spin mb-4 text-primary" />
                <p>Connecting to game provider...</p>
            </div>
        ) : error ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-red-400">
                <div className="bg-red-500/10 p-6 rounded-xl border border-red-500/20 text-center">
                    <p className="font-bold mb-2">Error</p>
                    <p>{error}</p>
                    <button onClick={() => navigate('/')} className="mt-4 text-sm underline hover:text-white">Return to Lobby</button>
                </div>
            </div>
        ) : (
            // In real app, this is the provider's iframe
            // For MVP, we use a placeholder that LOOKS like a game or a mock URL
            <iframe 
                src={launchUrl || "https://example.com"} 
                className="w-full h-full border-0" 
                allowFullScreen 
                title="Game Frame"
            />
        )}
      </div>
    </div>
  );
};

export default GameRoom;
