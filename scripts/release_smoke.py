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


def resolve_artifacts_dir():
    """Resolve a writable artifacts directory.

    CI runners may not allow writing to absolute paths like /app/.
    Priority:
      1) ARTIFACTS_DIR / RELEASE_SMOKE_ARTIFACTS_DIR env override
      2) $GITHUB_WORKSPACE/artifacts/release_smoke (or ./artifacts/release_smoke)
      3) /tmp/release_smoke fallback
    """
    from pathlib import Path

    raw = os.getenv("ARTIFACTS_DIR") or os.getenv("RELEASE_SMOKE_ARTIFACTS_DIR")
    if raw:
        p = Path(raw)
    else:
        p = Path(os.getenv("GITHUB_WORKSPACE", ".")) / "artifacts" / "release_smoke"

    try:
        p.mkdir(parents=True, exist_ok=True)
        testfile = p / ".write_test"
        testfile.write_text("ok")
        try:
            testfile.unlink()
        except FileNotFoundError:
            pass
        return str(p)
    except Exception:
        p2 = Path("/tmp") / "release_smoke"
        p2.mkdir(parents=True, exist_ok=True)
        return str(p2)


ARTIFACTS_DIR = resolve_artifacts_dir()

RUNNERS = [
    "bau_w12_runner.py",
    "bau_w13_runner.py",
    "bau_w14_mtt_runner.py",
    "bau_w14_collusion_runner.py",
    "policy_enforcement_test.py"
]

def run_script(script_name):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        return {"name": script_name, "status": "missing", "duration": 0, "error": "File not found"}
        
    print(f"{BLUE}-> Running {script_name}...{RESET}")
    start = time.time()
    
    # Propagate strict mode + envs
    env = os.environ.copy()
    if not env.get("BOOTSTRAP_OWNER_EMAIL"):
        env["BOOTSTRAP_OWNER_EMAIL"] = "admin@casino.com"
    if not env.get("BOOTSTRAP_OWNER_PASSWORD"):
        env["BOOTSTRAP_OWNER_PASSWORD"] = "Admin123!"
    if not env.get("API_BASE_URL"):
        env["API_BASE_URL"] = "http://localhost:8001/api/v1"

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )
        duration = (time.time() - start) * 1000 # ms
        
        # Save split logs
        with open(f"{ARTIFACTS_DIR}/{script_name}.stdout.log", "w") as f:
            f.write(result.stdout)
        with open(f"{ARTIFACTS_DIR}/{script_name}.stderr.log", "w") as f:
            f.write(result.stderr)

        if result.returncode == 0:
            print(f"{GREEN}[PASS] {script_name} ({duration/1000:.2f}s){RESET}")
            return {
                "name": script_name, 
                "status": "pass", 
                "duration_ms": int(duration),
                "exit_code": 0
            }
        else:
            print(f"{RED}[FAIL] {script_name} (Exit: {result.returncode}){RESET}")
            # Sanitize stderr for summary
            err_snip = result.stderr[-500:] if result.stderr else "No stderr"
            return {
                "name": script_name, 
                "status": "fail", 
                "duration_ms": int(duration),
                "exit_code": result.returncode,
                "last_error": err_snip
            }
            
    except subprocess.TimeoutExpired:
        print(f"{RED}[TIMEOUT] {script_name} exceeded 120s{RESET}")
        return {"name": script_name, "status": "timeout", "duration_ms": 120000, "exit_code": 124}

def main():
    print(f"{GREEN}=== T15-003: E2E RELEASE MATRIX (SMOKE) - STRICT MODE ==={RESET}")
    
    start_all = datetime.datetime.utcnow()
    results = []
    
    for runner in RUNNERS:
        results.append(run_script(runner))
            
    end_all = datetime.datetime.utcnow()
    
    # Stats
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] != "pass")
    
    summary = {
        "suite_name": "release_smoke_matrix",
        "started_at": start_all.isoformat(),
        "finished_at": end_all.isoformat(),
        "duration_ms": int((end_all - start_all).total_seconds() * 1000),
        "total": len(RUNNERS),
        "passed": passed,
        "failed": failed,
        "api_base_url": os.environ.get("API_BASE_URL", "default"),
        "results": results
    }
    
    with open(f"{ARTIFACTS_DIR}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{BLUE}=== SUMMARY ==={RESET}")
    print(f"Passed: {passed}/{len(RUNNERS)}")
    print(f"Artifacts: {ARTIFACTS_DIR}")
    
    if failed > 0:
        print(f"{RED}Suite FAILED.{RESET}")
        sys.exit(1)
    else:
        print(f"{GREEN}Suite PASSED.{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()
