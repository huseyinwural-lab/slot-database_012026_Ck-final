import sys
import os
import subprocess
import time
import json
import datetime

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = "/app/artifacts/release_smoke"

# Runners to execute in order
RUNNERS = [
    "bau_w12_runner.py",        # Growth Loop (Affiliate + CRM)
    "bau_w13_runner.py",        # VIP & Loyalty
    "bau_w14_mtt_runner.py",    # MTT Mechanics
    "bau_w14_collusion_runner.py", # Risk/Collusion
    "policy_enforcement_test.py"   # Negative Testing (T15-005)
]

def run_script(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"{RED}[ERROR] Script not found: {script_name}{RESET}")
        return {"name": script_name, "status": "missing", "duration": 0}
        
    print(f"{BLUE}-> Running {script_name}...{RESET}")
    start = time.time()
    
    # Retry Policy: 1 retry for network glitches
    retries = 1
    
    # Pass environment variables
    env = os.environ.copy()
    if not env.get("BOOTSTRAP_OWNER_EMAIL"):
        env["BOOTSTRAP_OWNER_EMAIL"] = "admin@casino.com"
    if not env.get("BOOTSTRAP_OWNER_PASSWORD"):
        env["BOOTSTRAP_OWNER_PASSWORD"] = "Admin123!"
    if not env.get("API_BASE_URL"):
        env["API_BASE_URL"] = "http://localhost:8001/api/v1"

    last_result = None
    stdout_log = ""
    stderr_log = ""

    for attempt in range(retries + 1):
        try:
            # We run via subprocess to isolate event loops
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=120, # 2 min timeout per script
                env=env
            )
            
            stdout_log = result.stdout
            stderr_log = result.stderr
            last_result = result

            if result.returncode == 0:
                duration = time.time() - start
                print(f"{GREEN}[PASS] {script_name} ({duration:.2f}s){RESET}")
                return {
                    "name": script_name, 
                    "status": "pass", 
                    "duration": duration,
                    "stdout": stdout_log
                }
            else:
                if attempt < retries:
                    print(f"{BLUE}   [RETRY] {script_name} failed, retrying...{RESET}")
                    continue
                else:
                    print(f"{RED}[FAIL] {script_name} (Exit: {result.returncode}){RESET}")
                    # Only print stderr to console on failure
                    print("--- STDERR ---")
                    print(stderr_log)
                    return {
                        "name": script_name, 
                        "status": "fail", 
                        "duration": time.time() - start,
                        "error_code": result.returncode,
                        "stdout": stdout_log,
                        "stderr": stderr_log
                    }
                    
        except subprocess.TimeoutExpired:
            print(f"{RED}[TIMEOUT] {script_name} exceeded 120s{RESET}")
            return {"name": script_name, "status": "timeout", "duration": 120}
            
    return {"name": script_name, "status": "unknown", "duration": 0}

def main():
    print(f"{GREEN}=== T15-003: E2E RELEASE MATRIX (SMOKE) ==={RESET}")
    
    # Ensure artifacts dir exists
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    results = []
    success_count = 0
    failures = []
    
    for runner in RUNNERS:
        res = run_script(runner)
        results.append(res)
        
        # Save individual logs
        with open(f"{ARTIFACTS_DIR}/{runner}.log", "w") as f:
            f.write(f"=== {runner} ===\n")
            f.write(f"Status: {res['status']}\n")
            f.write("--- STDOUT ---\n")
            f.write(res.get("stdout", ""))
            f.write("\n--- STDERR ---\n")
            f.write(res.get("stderr", ""))

        if res["status"] == "pass":
            success_count += 1
        else:
            failures.append(runner)
            
    # Save Summary
    summary = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "total": len(RUNNERS),
        "passed": success_count,
        "failed": len(failures),
        "results": results
    }
    with open(f"{ARTIFACTS_DIR}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{BLUE}=== SUMMARY ==={RESET}")
    print(f"Total: {len(RUNNERS)}")
    print(f"Passed: {success_count}")
    print(f"Failed: {len(failures)}")
    print(f"Artifacts saved to: {ARTIFACTS_DIR}")
    
    if failures:
        print(f"{RED}Failed Runners: {', '.join(failures)}{RESET}")
        sys.exit(1)
    else:
        print(f"{GREEN}ALL GATES PASSED. RELEASE CANDIDATE VALID.{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
