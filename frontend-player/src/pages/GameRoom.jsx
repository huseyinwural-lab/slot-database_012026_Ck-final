import React from 'react';
import Layout from '@/components/Layout';
import { useGamesStore, useWalletStore } from '@/domain';

const GameRoom = () => {
  const { launchUrl, launchStatus, error, resetLaunch } = useGamesStore();
  const { fetchBalance } = useWalletStore();

  const handleRetry = () => {
    resetLaunch();
  };

  const handleExit = () => {
    fetchBalance();
  };

  return (
    <Layout>
      <div className="space-y-4" data-testid="game-room">
        {launchStatus === 'launched' && launchUrl ? (
          <div className="rounded-2xl border border-white/10 bg-black/50 p-4" data-testid="game-iframe-container">
            <iframe
              src={launchUrl}
              title="Game"
              className="h-[70vh] w-full rounded-xl"
              data-testid="game-iframe"
            />
            <div className="mt-4 flex gap-3">
              <button
                onClick={handleExit}
                className="rounded-full border border-white/10 px-4 py-2 text-sm"
                data-testid="game-exit"
              >
                Lobby'e Dön
              </button>
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border border-white/10 bg-black/50 p-6 text-sm" data-testid="game-launch-fallback">
            <div>Oyun başlatılamadı.</div>
            <div className="text-white/60">{error?.message}</div>
            <div className="mt-4 flex gap-3">
              <button
                onClick={handleRetry}
                className="rounded-full bg-[var(--app-cta,#ff8b2c)] px-4 py-2 text-sm font-semibold text-black"
                data-testid="game-retry"
              >
                Tekrar Dene
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default GameRoom;
