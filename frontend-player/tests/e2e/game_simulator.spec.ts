import { test, expect } from '@playwright/test';

test.describe('P0 Game Provider Simulator Flow', () => {
  const timestamp = Date.now();
  const playerEmail = `game_sim_${timestamp}@test.com`;
  let token;
  let playerId;

  test.beforeAll(async ({ request }) => {
    // 1. Setup & Register
    await request.post('/api/v1/auth/player/register', {
        data: {
            email: playerEmail,
            password: "Password123!",
            username: `sim_user_${timestamp}`,
            phone: `+1555${timestamp.toString().slice(-7)}`,
            dob: "1990-01-01"
        }
    });
    
    // 2. Login
    const loginRes = await request.post('/api/v1/auth/player/login', {
        data: { email: playerEmail, password: "Password123!" }
    });
    const loginData = await loginRes.json();
    token = loginData.access_token;
    playerId = loginData.user.id;
    console.log("Player ID:", playerId);
    
    const headers = { Authorization: `Bearer ${token}` };
    
    // 3. Verify & KYC (Mock)
    await request.post('/api/v1/test/set-kyc', { data: { email: playerEmail, status: "verified" } });
    
    // 4. Deposit 1000
    const depRes = await request.post('/api/v1/player/wallet/deposit', {
        data: { amount: 1000, currency: "USD", method: "test" },
        headers: { ...headers, "Idempotency-Key": `dep_${timestamp}` }
    });
    expect(depRes.ok()).toBeTruthy();
  });

  test('Game Cycle: Bet -> Win -> Rollback', async ({ request }) => {
    const gameId = "sim_slot_01";
    const roundId = `round_${Date.now()}`;
    const txBet = `tx_bet_${Date.now()}`;
    const txWin = `tx_win_${Date.now()}`;
    
    console.log("Starting Bet...");
    
    // 1. BET 100
    const betRes = await request.post('/api/v1/games/callback/simulator', {
        data: {
            action: "bet",
            player_id: playerId,
            game_id: gameId,
            round_id: roundId,
            tx_id: txBet,
            amount: 100,
            currency: "USD"
        }
    });
    
    const betData = await betRes.json();
    console.log("Bet Response:", JSON.stringify(betData));
    expect(betRes.ok()).toBeTruthy();
    expect(betData.data.balance).toBe(900); // 1000 - 100

    // 2. WIN 200
    const winRes = await request.post('/api/v1/games/callback/simulator', {
        data: {
            action: "win",
            player_id: playerId,
            game_id: gameId,
            round_id: roundId,
            tx_id: txWin,
            amount: 200,
            currency: "USD"
        }
    });
    expect(winRes.ok()).toBeTruthy();
    const winData = await winRes.json();
    expect(winData.data.balance).toBe(1100); // 900 + 200

    // 3. Rollback Bet (Simulate cancellation)
    // Should credit 100 back -> 1200
    const rbRes = await request.post('/api/v1/games/callback/simulator', {
        data: {
            action: "rollback",
            player_id: playerId,
            game_id: gameId,
            round_id: roundId,
            tx_id: `rb_${txBet}`,
            ref_tx_id: txBet,
            amount: 100,
            currency: "USD"
        }
    });
    expect(rbRes.ok()).toBeTruthy();
    const rbData = await rbRes.json();
    expect(rbData.data.balance).toBe(1200);
  });
});
