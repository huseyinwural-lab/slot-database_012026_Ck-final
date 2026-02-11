import { request } from '../http/client';

export const gamesApi = {
  listLobby: () => request({ method: 'GET', url: '/api/v1/player/games' }),
  launchGame: (gameId) =>
    request({ method: 'GET', url: `/api/v1/player/games/${gameId}/launch` }),
};
