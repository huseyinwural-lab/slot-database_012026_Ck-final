import { request } from '../http/client';

export const gamesApi = {
  listLobby: () => request({ method: 'GET', url: '/api/v1/player/lobby/games' }),
  launchGame: (payload) =>
    request({ method: 'POST', url: '/api/v1/player/lobby/launch', data: payload }),
};
