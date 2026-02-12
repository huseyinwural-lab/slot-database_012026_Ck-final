import { test, expect } from '@playwright/test';

test.describe('P0 Game History', () => {
  const timestamp = Date.now();
  const playerEmail = `history_${timestamp}@test.com`;
  let token;
  let playerId;

  test.beforeAll(async ({ request }) => {
    // 1. Register & Login
    await request.post('/api/v1/auth/player/register', {
        data: { email: playerEmail, password: "Password123!", username: `hist_${timestamp}`, phone: `+1555${timestamp.toString().slice(-7)}`, dob: "1990-01-01" }
    });
    const loginRes = await request.post('/api/v1/auth/player/login', {
        data: { email: playerEmail, password: "Password123!" }
    });
    const loginData = await loginRes.json();
    token = loginData.access_token;
    playerId = loginData.user.id;
    
    // 2. Mock Verify
    const headers = { Authorization: `Bearer ${token}` };
    await request.post('/api/v1/test/set-kyc', { data: { email: playerEmail, status: "verified" } });
    
    // 3. Deposit
    await request.post('/api/v1/player/wallet/deposit', {
        data: { amount: 1000, currency: "USD", method: "test" },
        headers: { ...headers, "Idempotency-Key": `dep_${timestamp}` }
    });

    // 4. Play Game (Simulate)
    // Round 1: Lose 50 (Bet only)
    await request.post('/api/v1/games/callback/simulator', {
        data: { action: "bet", player_id: playerId, game_id: "slot_1", round_id: `r1_${timestamp}`, tx_id: `tx1_${timestamp}`, amount: 50, currency: "USD" }
    });
    
    // Round 2: Win 200 (Bet 10)
    // Bet
    await request.post('/api/v1/games/callback/simulator', {
        data: { action: "bet", player_id: playerId, game_id: "slot_1", round_id: `r2_${timestamp}`, tx_id: `tx2_${timestamp}`, amount: 10, currency: "USD" }
    });
    // Win
    await request.post('/api/v1/games/callback/simulator', {
        data: { action: "win", player_id: playerId, game_id: "slot_1", round_id: `r2_${timestamp}`, tx_id: `tx3_${timestamp}`, amount: 200, currency: "USD" }
    });
  });

  test('Check Game History API', async ({ request }) => {
    const headers = { Authorization: `Bearer ${token}` };
    
    // Poll API until total >= 2 (Async updates might delay round visibility?)
    // GameEngine uses flush/commit immediately, so should be instant.
    // But check response debug
    const res = await request.get('/api/v1/player/history/games?limit=10', { headers });
    expect(res.ok()).toBeTruthy();
    
    const data = await res.json();
    console.log("History Data:", JSON.stringify(data));
    
    // Check if we have 2 rounds.
    // Round 1 (bet 50) and Round 2 (bet 10, win 200)
    expect(data.meta.total).toBeGreaterThanOrEqual(2);
    
    // Order is desc
    // Item 0 -> Round 2 (Latest)
    expect(data.items[0].round_id).toContain(`r2_${timestamp}`);
    expect(data.items[0].total_bet).toBe(10);
    expect(data.items[0].total_win).toBe(200);
    expect(data.items[0].net).toBe(190);
    
    // Item 1 -> Round 1
    expect(data.items[1].round_id).toContain(`r1_${timestamp}`);
    expect(data.items[1].total_bet).toBe(50);
    expect(data.items[1].total_win).toBe(0);
    expect(data.items[1].net).toBe(-50);
  });
});
