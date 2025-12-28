import sys
import os
import subprocess
import time

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

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
        return False
        
    print(f"{BLUE}-> Running {script_name}...{RESET}")
    start = time.time()
    
    # Retry Policy: 1 retry for network glitches
    retries = 1
    
    # Pass environment variables
    # We ensure BOOTSTRAP credentials are set for runner_utils.py to pick up
    env = os.environ.copy()
    if not env.get("BOOTSTRAP_OWNER_EMAIL"):
        env["BOOTSTRAP_OWNER_EMAIL"] = "admin@casino.com" # Fallback/Default for local
    if not env.get("BOOTSTRAP_OWNER_PASSWORD"):
        env["BOOTSTRAP_OWNER_PASSWORD"] = "Admin123!" # Fallback/Default for local
    if not env.get("API_BASE_URL"):
        env["API_BASE_URL"] = "http://localhost:8001/api/v1"

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
            
            if result.returncode == 0:
                duration = time.time() - start
                print(f"{GREEN}[PASS] {script_name} ({duration:.2f}s){RESET}")
                # Optional: Print stdout if needed, or save to log
                return True
            else:
                if attempt < retries:
                    print(f"{BLUE}   [RETRY] {script_name} failed, retrying...{RESET}")
                    continue
                else:
                    print(f"{RED}[FAIL] {script_name} (Exit: {result.returncode}){RESET}")
                    print("--- STDOUT ---")
                    print(result.stdout)
                    print("--- STDERR ---")
                    print(result.stderr)
                    return False
                    
        except subprocess.TimeoutExpired:
            print(f"{RED}[TIMEOUT] {script_name} exceeded 120s{RESET}")
            return False
            
    return False

def main():
    print(f"{GREEN}=== T15-003: E2E RELEASE MATRIX (SMOKE) ==={RESET}")
    
    success_count = 0
    failures = []
    
    for runner in RUNNERS:
        if run_script(runner):
            success_count += 1
        else:
            failures.append(runner)
            
    print(f"\n{BLUE}=== SUMMARY ==={RESET}")
    print(f"Total: {len(RUNNERS)}")
    print(f"Passed: {success_count}")
    print(f"Failed: {len(failures)}")
    
    if failures:
        print(f"{RED}Failed Runners: {', '.join(failures)}{RESET}")
        sys.exit(1)
    else:
        print(f"{GREEN}ALL GATES PASSED. RELEASE CANDIDATE VALID.{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
