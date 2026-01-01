import { test, expect, request as pwRequest } from '@playwright/test';

test.describe('Smart Game Loop', () => {
  test.setTimeout(120000);

  test('Session -> Smart Spin -> Valid Audit', async ({ page }) => {
    const API_URL = process.env.E2E_API_BASE || 'http://localhost:8001';
    
    // 1. Setup User
    const uniqueId = Date.now();
    const email = `smart_gamer_${uniqueId}@example.com`;
    const apiContext = await pwRequest.newContext({ baseURL: API_URL });
    
    await apiContext.post('/api/v1/auth/player/register', {
      data: { username: `gamer${uniqueId}`, email, password: 'Password123!', tenant_id: 'default_casino' }
    });
    
    const loginRes = await apiContext.post('/api/v1/auth/player/login', {
      data: { email, password: 'Password123!', tenant_id: 'default_casino' }
    });
    const token = (await loginRes.json()).access_token;
    
    // Deposit 100
    const depositRes = await apiContext.post('/api/v1/player/wallet/deposit', {
        headers: { 
            'Authorization': `Bearer ${token}`,
            'Idempotency-Key': `dep-${Date.now()}`
        },
        data: { amount: 100, method: 'test' }
    });
    if (!depositRes.ok()) {
        console.log('Deposit Failed:', depositRes.status(), await depositRes.text());
    }
    if (!depositRes.ok()) {
        console.log('Deposit Failed:', depositRes.status(), await depositRes.text());
    }

    // 2. Launch Game (Classic 777 - has Robot)
    // First get games to find ID
    const gamesRes = await apiContext.get('/api/v1/player/client-games', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const games = await gamesRes.json();
    // games_client returns List[Game] directly (not wrapped in items)
    const game = Array.isArray(games) ? games.find(g => g.external_id === 'classic777') : games.items?.find(g => g.external_id === 'classic777');
    
    expect(game).toBeTruthy();
    
    const launchRes = await apiContext.post('/api/v1/player/client-games/launch', {
        data: { game_id: game.id, currency: 'USD' },
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const launchData = await launchRes.json();
    const sessionId = launchData.session_id;
    
    // 3. Spin via Mock Provider API (Simulate Client)
    const spinRes = await apiContext.post('/api/v1/mock-provider/spin', {
        data: { session_id: sessionId, amount: 1.0, currency: 'USD' }
    });
    expect(spinRes.ok()).toBeTruthy();
    
    const spinData = await spinRes.json();
    
    // 4. Verification
    expect(spinData.audit).toBeTruthy();
    expect(spinData.audit.robot_id).toBeTruthy();
    expect(spinData.grid).toHaveLength(3); // 3 Rows
    
    console.log(`Spin Result: Win=${spinData.win}, Balance=${spinData.balance}`);
    
    if (spinData.win > 0) {
        expect(spinData.lines.length).toBeGreaterThan(0);
    }
    
    console.log('Smart Game Engine PASS');
  });
});
