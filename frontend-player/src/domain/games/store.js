import { create } from 'zustand';
import { gamesApi } from '@/infra/api/games';
import { trackEvent } from '@/telemetry';

export const useGamesStore = create((set) => ({
  lobbyStatus: 'idle',
  games: [],
  launchStatus: 'idle',
  launchUrl: null,
  error: null,
  fetchLobby: async () => {
    set({ lobbyStatus: 'loading', error: null });
    const response = await gamesApi.listLobby();
    if (response.ok) {
      trackEvent('lobby_loaded', { count: response.data?.items?.length || 0 });
      set({ lobbyStatus: 'ready', games: response.data?.items || [], error: null });
    } else {
      set({ lobbyStatus: 'failed', error: response.error });
    }
    return response;
  },
  launchGame: async (game) => {
    set({ launchStatus: 'launching', launchUrl: null, error: null });
    trackEvent('game_launch_click', { game_id: game.id });
    const response = await gamesApi.launchGame(game.id);
    if (response.ok) {
      trackEvent('game_launch_success', { game_id: game.id });
      set({ launchStatus: 'launched', launchUrl: response.data?.launch_url, error: null });
    } else {
      trackEvent('game_launch_fail', { game_id: game.id });
      set({ launchStatus: 'failed', error: response.error });
    }
    return response;
  },
  resetLaunch: () => set({ launchStatus: 'idle', launchUrl: null, error: null }),
}));
