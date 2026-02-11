import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '@/components/Layout';
import { GameCard } from '@/components/GameCard';
import { CategoryRail } from '@/components/CategoryRail';
import { SkeletonBlock } from '@/components/SkeletonBlock';
import { useGamesStore, useWalletStore, useVerificationStore } from '@/domain';

const Lobby = () => {
  const { games, lobbyStatus, fetchLobby, launchGame, launchStatus } = useGamesStore();
  const { markStale } = useWalletStore();
  const { emailState, smsState } = useVerificationStore();
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchLobby();
  }, [fetchLobby]);

  const filtered = useMemo(() => {
    if (!query) return games;
    return games.filter((game) => game.name.toLowerCase().includes(query.toLowerCase()));
  }, [games, query]);

  const handleLaunch = async (game) => {
    if (emailState !== 'verified' || smsState !== 'verified') return;
    const response = await launchGame(game);
    if (response.ok) {
      markStale();
      navigate('/game');
    }
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="lobby-page">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold" data-testid="lobby-title">Featured Games</h2>
            <p className="text-sm text-white/60" data-testid="lobby-subtitle">En iyi oyunları keşfedin.</p>
          </div>
          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Oyun ara"
            className="rounded-full border border-white/10 bg-black/40 px-4 py-2 text-sm"
            data-testid="lobby-search"
          />
        </div>

        {(emailState !== 'verified' || smsState !== 'verified') && (
          <div className="rounded-xl border border-orange-400/40 bg-orange-500/10 p-4 text-sm" data-testid="lobby-verification-banner">
            Oyun başlatmak için email ve SMS doğrulamalarını tamamlayın.
          </div>
        )}

        {lobbyStatus === 'loading' && (
          <div className="grid gap-4 md:grid-cols-3">
            {Array.from({ length: 6 }).map((_, idx) => (
              <SkeletonBlock key={idx} className="h-40" />
            ))}
          </div>
        )}

        {lobbyStatus === 'ready' && (
          <CategoryRail
            title="Trend"
            items={filtered.map((game) => (
              <GameCard key={game.id} game={game} onLaunch={handleLaunch} />
            ))}
          />
        )}

        {lobbyStatus === 'failed' && (
          <div className="rounded-xl border border-red-400/40 bg-red-500/10 p-4 text-sm" data-testid="lobby-error">
            Oyun listesi yüklenemedi.
          </div>
        )}

        {launchStatus === 'launching' && (
          <div className="text-sm text-white/60" data-testid="game-launch-loading">Oyun başlatılıyor...</div>
        )}
      </div>
    </Layout>
  );
};

export default Lobby;
