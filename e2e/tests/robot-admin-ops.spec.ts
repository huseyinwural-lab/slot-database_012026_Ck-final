import { test, expect, request as pwRequest } from '@playwright/test';

test.describe('Robot Admin Ops', () => {
  test.setTimeout(120000);

  test('Admin Clone -> Bind -> Player Spin Verify', async ({ page }) => {
    const API_URL = process.env.E2E_API_BASE || 'http://localhost:8001';
    
    // 1. Admin Login
    const adminContext = await pwRequest.newContext({ baseURL: API_URL });
    const adminLoginRes = await adminContext.post('/api/v1/auth/login', {
      data: { email: 'admin@casino.com', password: 'Admin123!' }
    });
    const adminToken = (await adminLoginRes.json()).access_token;
    expect(adminToken).toBeTruthy();
    
    // 2. Clone Robot
    // First get existing robot
    const robotsRes = await adminContext.get('/api/v1/robots', {
      headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    const robotsData = await robotsRes.json();
    const originalRobot = robotsData.items.find(r => r.name.includes('Classic 777'));
    expect(originalRobot).toBeTruthy();
    
    // Clone
    const cloneRes = await adminContext.post(`/api/v1/robots/${originalRobot.id}/clone`, {
      headers: { 'Authorization': `Bearer ${adminToken}`, 'X-Reason': 'E2E Test Clone' },
      data: { name_suffix: " (E2E Test)" }
    });
    expect(cloneRes.ok()).toBeTruthy();
    const clonedRobot = await cloneRes.json();
    
    // Enable Cloned Robot
    await adminContext.post(`/api/v1/robots/${clonedRobot.id}/toggle`, {
      headers: { 'Authorization': `Bearer ${adminToken}`, 'X-Reason': 'E2E Test Toggle' }
    });
    
    // 3. Bind to Game
    // Find Game
    const gamesRes = await adminContext.get('/api/v1/games', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    const games = await gamesRes.json();
    const game = games.items.find(g => g.external_id === 'classic777');
    expect(game).toBeTruthy();
    
    const bindRes = await adminContext.post(`/api/v1/games/${game.id}/robot`, {
        headers: { 'Authorization': `Bearer ${adminToken}`, 'X-Reason': 'E2E Test Bind' },
        data: { robot_id: clonedRobot.id }
    });
    expect(bindRes.ok()).toBeTruthy();
    
    // 4. Player Flow
    const uniqueId = Date.now();
    const playerContext = await pwRequest.newContext({ baseURL: API_URL });
    
    // Register & Login
    await playerContext.post('/api/v1/auth/player/register', {
      data: { username: `robotuser${uniqueId}`, email: `robot_${uniqueId}@example.com`, password: 'Password123!', tenant_id: 'default_casino' }
    });
    const pLoginRes = await playerContext.post('/api/v1/auth/player/login', {
      data: { email: `robot_${uniqueId}@example.com`, password: 'Password123!', tenant_id: 'default_casino' }
    });
    const pToken = (await pLoginRes.json()).access_token;
    
    // Deposit
    await playerContext.post('/api/v1/player/wallet/deposit', {
        headers: { 'Authorization': `Bearer ${pToken}`, 'Idempotency-Key': `dep-${uniqueId}` },
        data: { amount: 100, method: 'test' }
    });
    
    // Launch (Create Session)
    const launchRes = await playerContext.post('/api/v1/player/client-games/launch', {
        headers: { 'Authorization': `Bearer ${pToken}` },
        data: { game_id: game.id, currency: 'USD' }
    });
    const launchData = await launchRes.json();
    const sessionId = launchData.session_id;
    
    // Spin
    const spinRes = await playerContext.post('/api/v1/mock-provider/spin', {
        data: { session_id: sessionId, amount: 1.0, currency: 'USD' }
    });
    expect(spinRes.ok()).toBeTruthy();
    const spinData = await spinRes.json();
    
    // 5. Verify Audit
    console.log("Spin Audit Robot ID:", spinData.audit.robot_id);
    console.log("Expected Cloned ID:", clonedRobot.id);
    
    expect(spinData.audit.robot_id).toBe(clonedRobot.id);
    console.log('Robot Admin Ops PASS');
  });
});
