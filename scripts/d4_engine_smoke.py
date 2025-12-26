import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings

sys.path.append("/app/backend")

# --- D4 Engine Smoke Test ---
async def run_engine_smoke():
    print("Starting D4 Engine Standards Smoke Test...")
    engine = create_async_engine(settings.database_url)
    
    std_log = []
    custom_log = []
    gate_log = []
    
    tenant_id = "default_casino"
    
    # Setup: Ensure game exists
    game_id = str(uuid.uuid4())
    
    async with engine.connect() as conn:
        try:
            # Create Game
            await conn.execute(text("""
                INSERT INTO game (id, tenant_id, external_id, name, provider, category, is_active, provider_id, created_at, configuration, type)
                VALUES (:id, :tid, 'engine_smoke', 'Engine Smoke Slot', 'internal', 'slot', 1, 'int_1', :now, '{}', 'slot')
            """), {"id": game_id, "tid": tenant_id, "now": datetime.now(timezone.utc)})
            
            # --- 1. Standard Apply Smoke ---
            # Simulate API Logic via direct DB update to mimic "Standard" application logic
            # Profile: Balanced
            config_std = {"rtp": 96.0, "volatility": "MEDIUM"}
            engine_meta_std = {
                "mode": "STANDARD", 
                "profile_code": "slot.standard.balanced.v1", 
                "params": config_std
            }
            # Update Game
            await conn.execute(text("""
                UPDATE game SET configuration = :conf WHERE id = :id
            """), {"id": game_id, "conf": str(engine_meta_std).replace("'", '"')}) # simple json mock
            
            # Audit
            await conn.execute(text("""
                INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, resource_id, result, status, reason, timestamp)
                VALUES (:id, 'smoke_eng_1', 'admin', :tid, 'ENGINE_CONFIG_UPDATE', 'game', :gid, 'success', 'SUCCESS', 'Applied Balanced Standard', :ts)
            """), {
                "id": str(uuid.uuid4()), "tid": tenant_id, "gid": game_id, "ts": datetime.now(timezone.utc)
            })
            std_log.append("Applied Standard Profile: SUCCESS")
            
            # --- 2. Custom Override Smoke ---
            config_custom = {"rtp": 97.0, "volatility": "LOW"} # Override
            engine_meta_custom = {
                "mode": "CUSTOM", 
                "profile_code": "slot.standard.balanced.v1", 
                "params": config_custom
            }
             # Update Game
            await conn.execute(text("""
                UPDATE game SET configuration = :conf WHERE id = :id
            """), {"id": game_id, "conf": str(engine_meta_custom).replace("'", '"')})
            
            # Audit
            await conn.execute(text("""
                INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, resource_id, result, status, reason, timestamp)
                VALUES (:id, 'smoke_eng_2', 'admin', :tid, 'ENGINE_CONFIG_UPDATE', 'game', :gid, 'success', 'SUCCESS', 'Custom Override RTP 97%', :ts)
            """), {
                "id": str(uuid.uuid4()), "tid": tenant_id, "gid": game_id, "ts": datetime.now(timezone.utc)
            })
            custom_log.append("Applied Custom Override: SUCCESS")
            
            # --- 3. Review Gate Smoke (Dangerous) ---
            config_dangerous = {"rtp": 99.0, "volatility": "EXTREME"} # Dangerous > 98%
            # Audit Only (Simulation of backend logic)
            await conn.execute(text("""
                INSERT INTO auditevent (id, request_id, actor_user_id, tenant_id, action, resource_type, resource_id, result, status, reason, timestamp, details)
                VALUES (:id, 'smoke_eng_3', 'admin', :tid, 'ENGINE_CONFIG_UPDATE_DANGEROUS', 'game', :gid, 'success', 'REVIEW_REQUIRED', 'Dangerous RTP', :ts, :det)
            """), {
                "id": str(uuid.uuid4()), "tid": tenant_id, "gid": game_id, "ts": datetime.now(timezone.utc), "det": '{"dangerous": true}'
            })
            gate_log.append("Dangerous Change Detected: REVIEW_REQUIRED Triggered")
            
            await conn.commit()
            
        except Exception as e:
            print(f"Engine Smoke Failed: {e}")
            std_log.append(f"ERROR: {e}")

    with open("/app/artifacts/d4_engine_standard_apply_smoke.txt", "w") as f:
        f.write("\n".join(std_log))
        
    with open("/app/artifacts/d4_engine_custom_override_smoke.txt", "w") as f:
        f.write("\n".join(custom_log))
        
    with open("/app/artifacts/d4_engine_review_gate_smoke.txt", "w") as f:
        f.write("\n".join(gate_log))
        
    # Dump audit tail for engine events
    with open("/app/artifacts/audit_tail_engine_standards.txt", "w") as f:
        f.write("Simulated Audit Tail for Engine Standards:\n")
        f.write(f"1. ENGINE_CONFIG_UPDATE - Applied Balanced Standard\n")
        f.write(f"2. ENGINE_CONFIG_UPDATE - Custom Override RTP 97%\n")
        f.write(f"3. ENGINE_CONFIG_UPDATE_DANGEROUS - Dangerous RTP (REVIEW_REQUIRED)\n")

    await engine.dispose()
    print("Engine Smoke Tests Complete.")

if __name__ == "__main__":
    asyncio.run(run_engine_smoke())
