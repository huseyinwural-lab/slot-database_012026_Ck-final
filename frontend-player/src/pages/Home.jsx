import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Play, Star, TrendingUp } from 'lucide-react';

const Home = () => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGames = async () => {
      try {
        // Fetch active games from backend
        const res = await api.get('/player/games');
        setGames(res.data?.items || []);
      } catch (err) {
        console.error("Failed to load games", err);
      } finally {
        setLoading(false);
      }
    };
    fetchGames();
  }, []);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative h-[300px] rounded-2xl overflow-hidden bg-gradient-to-r from-purple-900 to-indigo-900 flex items-center px-10">
        <div className="max-w-xl space-y-4 relative z-10">
          <span className="bg-yellow-500 text-black font-bold px-2 py-1 rounded text-xs uppercase tracking-wider">New Arrival</span>
          <h1 className="text-5xl font-extrabold text-white">Big Bass Splash</h1>
          <p className="text-gray-200 text-lg">Catch the biggest wins in the new release from Pragmatic Play. High volatility and huge multipliers await!</p>
          <button className="bg-primary text-white px-8 py-3 rounded-lg font-bold text-lg hover:bg-primary/90 transition">Play Now</button>
        </div>
        <div className="absolute right-0 top-0 h-full w-1/2 bg-[url('https://placehold.co/800x400/222/222')] opacity-50 mix-blend-overlay"></div>
      </div>

      {/* Categories */}
      <div className="flex gap-4 overflow-x-auto pb-2">
        {['All Games', 'Slots', 'Live Casino', 'Table Games', 'Jackpots', 'Bonus Buy'].map(cat => (
            <button key={cat} className="px-6 py-2 rounded-full bg-white/5 hover:bg-white/10 whitespace-nowrap transition-colors border border-white/10">
                {cat}
            </button>
        ))}
      </div>

      {/* Game Grid */}
      <section>
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Star className="text-yellow-500 fill-yellow-500" /> Popular Games
        </h2>
        
        {loading ? (
            <div className="text-center py-10 text-muted-foreground">Loading games...</div>
        ) : games.length === 0 ? (
            <div className="text-center py-10 text-muted-foreground border border-dashed rounded-xl border-white/10">
                <p>No active games found for this lobby.</p>
                <p className="text-xs mt-2">Please contact support or check back later.</p>
            </div>
        ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {games.map(game => (
                    <Link to={`/game/${game.id}`} key={game.id} className="group relative aspect-[3/4] bg-secondary rounded-xl overflow-hidden hover:ring-2 hover:ring-primary transition-all">
                        <img 
                            src={game.image_url || 'https://placehold.co/300x400/222/FFF?text=Game'} 
                            alt={game.name} 
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" 
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/90 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-4">
                            <h3 className="font-bold text-white truncate">{game.name}</h3>
                            <p className="text-xs text-gray-300">{game.provider}</p>
                            <button className="mt-3 w-full bg-primary text-white py-2 rounded-lg font-bold flex items-center justify-center gap-2">
                                <Play className="w-4 h-4 fill-white" /> Play
                            </button>
                        </div>
                    </Link>
                ))}
            </div>
        )}
      </section>
    </div>
  );
};

export default Home;