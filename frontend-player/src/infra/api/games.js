import { request } from '../http/client';

export const gamesApi = {
  listLobby: () => request({ method: 'GET', url: '/player/games' }),
  launchGame: (gameId) =>
    request({ method: 'GET', url: `/player/games/${gameId}/launch` }),
};
