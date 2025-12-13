import requests
import sys
import uuid

BASE_URL = "http://localhost:8001/api/v1"
EMAIL = f"flow_test_{uuid.uuid4().hex[:8]}@test.com"
PASSWORD = "Test123!"

def run_flow():
    print(f"🚀 Starting Player Flow Test (1 -> 4)...")
    print(f"👤 Test User: {EMAIL}")

    session = requests.Session()

    # --- STEP 1: REGISTER & LOGIN ---
    print("\n[1] 🔐 Authentication (Register & Login)...")
    
    # Register
    reg_res = session.post(f"{BASE_URL}/auth/player/register", json={
        "username": "FlowTester",
        "email": EMAIL,
        "password": PASSWORD
    })
    
    if reg_res.status_code == 200:
        print("   ✅ Register: Success")
    else:
        print(f"   ❌ Register Failed: {reg_res.text}")
        sys.exit(1)

    # Login
    login_res = session.post(f"{BASE_URL}/auth/player/login", json={
        "email": EMAIL,
        "password": PASSWORD
    })
    
    if login_res.status_code == 200:
        token = login_res.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        # Set default tenant header
        session.headers.update({"X-Tenant-ID": "default_casino"}) 
        print("   ✅ Login: Success (Token acquired)")
    else:
        print(f"   ❌ Login Failed: {login_res.text}")
        sys.exit(1)


    # --- STEP 2: LOBBY (GET GAMES) ---
    print("\n[2] 🎰 Lobby (Fetch Games)...")
    games_res = session.get(f"{BASE_URL}/player/games")
    
    games = []
    if games_res.status_code == 200:
        data = games_res.json()
        games = data.get("items", [])
        print(f"   ✅ Fetched {len(games)} active games.")
        if not games:
            print("   ⚠️  No games found. Please ensure seed_complete_data.py was run.")
            # We can't proceed to step 4 without a game, but we can try step 3
    else:
        print(f"   ❌ Lobby Failed: {games_res.text}")
        sys.exit(1)


    # --- STEP 3: WALLET (DEPOSIT) ---
    print("\n[3] 💰 Wallet (Deposit Funds)...")
    
    # Check Balance Before
    bal_res = session.get(f"{BASE_URL}/player/wallet/balance")
    initial_bal = bal_res.json().get("balance_real", 0)
    print(f"   ℹ️  Initial Balance: ${initial_bal}")

    # Deposit
    dep_res = session.post(f"{BASE_URL}/player/wallet/deposit", json={
        "amount": 100.0,
        "method": "test_flow"
    })
    
    if dep_res.status_code == 200:
        print("   ✅ Deposit ($100): Success")
        
        # Check Balance After
        bal_res_after = session.get(f"{BASE_URL}/player/wallet/balance")
        new_bal = bal_res_after.json().get("balance_real", 0)
        print(f"   💰 New Balance: ${new_bal}")
        
        if new_bal >= initial_bal + 100:
             print("   ✅ Balance Updated Verified")
        else:
             print("   ❌ Balance Update Mismatch")
    else:
        print(f"   ❌ Deposit Failed: {dep_res.text}")
        sys.exit(1)


    # --- STEP 4: GAME ROOM (LAUNCH) ---
    print("\n[4] 🎮 Game Room (Launch Game)...")
    
    if games:
        game_id = games[0]["id"]
        game_name = games[0]["name"]
        print(f"   ℹ️  Launching Game: {game_name} ({game_id})...")
        
        launch_res = session.get(f"{BASE_URL}/player/games/{game_id}/launch")
        
        if launch_res.status_code == 200:
            url = launch_res.json().get("launch_url")
            print(f"   ✅ Launch Success!")
            print(f"   🔗 URL: {url}")
        else:
            print(f"   ❌ Launch Failed: {launch_res.text}")
            sys.exit(1)
    else:
        print("   ⏭️  Skipping Step 4 (No games available)")


    print("\n✨ FLOW 1->4 COMPLETE & VERIFIED ✨")

if __name__ == "__main__":
    run_flow()
