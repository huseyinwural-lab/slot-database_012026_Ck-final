import os
import re
import sys
from datetime import datetime, timedelta

# Configuration
DOCS_DIR = "/app/docs/ops"
SCRIPTS_DIR = "/app/scripts"
ROOT_DIR = "/app"

CORE_DOCS = [
    "knowledge_base_index.md",
    "go_live_runbook.md",
    "onboarding_pack.md",
    "bau_governance.md"
]

def check_file_existence(base_path, rel_path):
    # Handle absolute paths in docs (e.g. /app/...) vs relative
    if rel_path.startswith("/app"):
        abs_path = rel_path
    elif rel_path.startswith("/"):
        abs_path = rel_path # Assume root match
    else:
        # Resolve relative to doc location? Or assumes from root? 
        # Markdown links usually relative to file. 
        # But for this simple check, we'll try resolving from doc dir first, then root.
        abs_path = os.path.join(base_path, rel_path)
        if not os.path.exists(abs_path):
            abs_path = os.path.join(ROOT_DIR, rel_path)
    
    return os.path.exists(abs_path)

def check_script_references(content):
    # Regex to find `scripts/something.py` or `/app/scripts/...`
    # Simple pattern: words ending in .py or .sh inside ` ` or following /scripts/
    refs = re.findall(r'scripts/[\w\-_]+\.(?:py|sh)', content)
    missing = []
    for ref in refs:
        # Ref is likely "scripts/foo.py". Check if it exists in SCRIPTS_DIR
        script_name = os.path.basename(ref)
        full_path = os.path.join(SCRIPTS_DIR, script_name)
        if not os.path.exists(full_path):
            missing.append(script_name)
    return missing

def check_freshness(content, filename):
    match = re.search(r'\*\*Last Reviewed:\*\* (\d{4}-\d{2}-\d{2})', content)
    if match:
        date_str = match.group(1)
        review_date = datetime.strptime(date_str, "%Y-%m-%d")
        if datetime.now() - review_date > timedelta(days=90):
            return f"STALE (>90 days, last: {date_str})"
    return None # No date found or fresh

def main():
    print("=== Docs Drift Check ===")
    errors = 0
    warnings = 0

    for doc_name in CORE_DOCS:
        doc_path = os.path.join(DOCS_DIR, doc_name)
        if not os.path.exists(doc_path):
            print(f"[FAIL] Core doc missing: {doc_name}")
            errors += 1
            continue

        print(f"[*] Checking {doc_name}...")
        with open(doc_path, 'r') as f:
            content = f.read()

        # 1. Check Script References
        missing_scripts = check_script_references(content)
        if missing_scripts:
            print(f"    [FAIL] Missing scripts referenced: {', '.join(missing_scripts)}")
            errors += 1
        
        # 2. Freshness
        stale_msg = check_freshness(content, doc_name)
        if stale_msg:
            print(f"    [WARN] Document is stale: {stale_msg}")
            warnings += 1
        
        # 3. Simple Link Check (Regex for [text](path))
        links = re.findall(r'\[.*?\]\((.*?)\)', content)
        for link in links:
            # Ignore http links and anchors
            if link.startswith("http") or link.startswith("#"):
                continue
            
            # Clean path (remove query params or anchors)
            link_clean = link.split('#')[0]
            if not link_clean: continue

            # For now, strict check on file existence
            # Docs in /app/docs/ops/ refer to other docs usually relatively or absolute
            doc_dir = os.path.dirname(doc_path)
            if not check_file_existence(doc_dir, link_clean):
                print(f"    [FAIL] Broken link: {link}")
                errors += 1

    print(f"\nSummary: {errors} Errors, {warnings} Warnings")
    if errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
