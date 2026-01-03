import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Play } from 'lucide-react';

const Home = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchGames = async () => {
        try {
            const res = await api.get('/player/games');
            const items = res.data?.items || res.data?.data?.items || [];
            setGames(Array.isArray(items) ? items : []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };
    fetchGames();
  }, []);

  const handlePlay = async (gameId) => {
      try {
          const res = await api.post('/player/client-games/launch', { game_id: gameId, currency: 'USD' });
          // backend returns { url: "/game/{session_id}" }
          const url = res.data?.url || res.data?.launch_url;
          navigate(url);
      } catch (err) {
          alert("Failed to launch game");
      }
  };

  if (loading) return <div className="text-center p-10">Loading Lobby...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
            Game Lobby
        </h1>
        <Input className="w-64" placeholder="Search games..." />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {games.length === 0 ? (
            <div className="col-span-full text-center text-muted-foreground">No games found.</div>
        ) : (
            games.map(game => (
                <Card key={game.id} className="group overflow-hidden border-0 bg-white/5 hover:bg-white/10 transition-all cursor-pointer" onClick={() => handlePlay(game.id)}>
                    <div className="aspect-[3/4] relative">
                        {game.image_url ? (
                            <img src={game.image_url} alt={game.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center bg-black/40 text-4xl">🎰</div>
                        )}
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                            <Button size="icon" className="rounded-full w-12 h-12 bg-primary hover:bg-primary/90">
                                <Play className="w-6 h-6 ml-1 text-white" />
                            </Button>
                        </div>
                    </div>
                    <CardContent className="p-3">
                        <h3 className="font-semibold truncate">{game.name || game.title}</h3>
                        <p className="text-xs text-muted-foreground capitalize">{game.provider_id || game.provider || ''}</p>
                    </CardContent>
                </Card>
            ))
        )}
      </div>
    </div>
  );
};

export default Home;
