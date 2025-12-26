import asyncio
import sys
import os
import json
import hashlib

sys.path.append("/app/backend")
from app.services.slot_math.engine import SlotMathEngine

def run_slot_engine_e2e():
    print("Starting Slot Engine v1 E2E Test...")
    log = []
    
    # 1. Setup Assets
    # Standard 5 Reels
    reels = [
        ["A", "K", "Q", "J", "10", "WILD", "SCATTER", "A", "K", "10"], # Reel 1
        ["A", "K", "Q", "J", "10", "WILD", "SCATTER", "Q", "J", "10"], # Reel 2
        ["A", "K", "Q", "J", "10", "WILD", "SCATTER", "K", "Q", "10"], # Reel 3
        ["A", "K", "Q", "J", "10", "WILD", "A", "K", "J", "10"],       # Reel 4
        ["A", "K", "Q", "J", "10", "A", "K", "Q", "J", "10"]           # Reel 5
    ]
    
    # Paytable
    paytable = {
        "A": {3: 5, 4: 20, 5: 100},
        "K": {3: 4, 4: 15, 5: 80},
        "Q": {3: 3, 4: 10, 5: 50},
        "J": {3: 2, 4: 8, 5: 40},
        "10": {3: 1, 4: 5, 5: 20},
        "WILD": {5: 500} # Wild native pay
    }
    
    # Lines (Standard 3 lines for simplicity in test)
    # Line 0: Middle [1,1,1,1,1]
    # Line 1: Top [0,0,0,0,0]
    # Line 2: Bottom [2,2,2,2,2]
    lines = [
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [2, 2, 2, 2, 2]
    ]
    
    engine = SlotMathEngine(reels, paytable, lines)
    
    # 2. Test Determinism (Replay)
    seed = "test_seed_123"
    result1 = engine.spin(seed, total_bet=1.0)
    result2 = engine.spin(seed, total_bet=1.0)
    
    if result1.grid == result2.grid and result1.total_win == result2.total_win:
        log.append("Determinism Check: PASS")
    else:
        log.append("Determinism Check: FAIL (Results differ)")
        
    # 3. Test Evaluation Logic
    # We'll force a seed if we knew one, but let's just log the output
    log.append("\n--- Spin Result 1 ---")
    log.append(f"Stops: {result1.stops}")
    log.append("Grid:")
    for row in result1.grid:
        log.append(f"  {row}")
    
    log.append(f"Wins: {len(result1.line_wins)}")
    for win in result1.line_wins:
        log.append(f"  Line {win['line_index']} ({win['symbol']} x{win['count']}): {win['amount']}")
        
    log.append(f"Total Win: {result1.total_win}")
    log.append(f"Scatter: {result1.scatter_count} (Trigger: {result1.is_scatter_trigger})")
    
    # 4. Audit Tail Simulation
    # We prove we can construct the audit payload
    audit_payload = {
        "round_id": "rnd_123",
        "grid_hash": hashlib.sha256(json.dumps(result1.grid).encode()).hexdigest(),
        "payout": result1.total_win,
        "stops": result1.stops
    }
    log.append(f"\nAudit Payload: {json.dumps(audit_payload)}")
    
    # Write Artifact
    with open("/app/artifacts/bau/week3/e2e_slot_engine_payline.txt", "w") as f:
        f.write("\n".join(log))
        
    print("Slot Engine E2E Complete.")

if __name__ == "__main__":
    run_slot_engine_e2e()
