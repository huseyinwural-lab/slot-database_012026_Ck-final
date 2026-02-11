export const GameCard = ({ game, onLaunch }) => (
  <div className="rounded-xl border border-white/10 bg-black/30 p-4" data-testid={`game-card-${game.id}`}>
    <div className="h-28 rounded-lg bg-white/5" data-testid={`game-card-${game.id}-thumb`} />
    <div className="mt-3 flex items-center justify-between">
      <div>
        <div className="text-sm font-semibold" data-testid={`game-card-${game.id}-name`}>{game.name}</div>
        <div className="text-xs text-white/60" data-testid={`game-card-${game.id}-provider`}>{game.provider || 'Provider'}</div>
      </div>
      <button
        onClick={() => onLaunch(game)}
        className="rounded-full bg-[var(--app-cta,#ff8b2c)] px-4 py-2 text-xs font-semibold text-black"
        data-testid={`game-card-${game.id}-launch`}
      >
        Oyna
      </button>
    </div>
  </div>
);
