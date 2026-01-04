#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  echo "[DOCS_SMOKE][FAIL] $1" >&2
  exit 1
}

info() {
  echo "[DOCS_SMOKE] $1"
}

info "Starting docs smoke checks"

# 1) Required files
REQ_FILES=(
  "docs/new/en/guides/quickstart.md"
  "docs/new/tr/guides/quickstart.md"
  "docs/new/en/guides/ops-manual.md"
  "docs/new/tr/guides/ops-manual.md"
  "docs/new/en/guides/admin-panel-manual.md"
  "docs/new/tr/guides/admin-panel-manual.md"
  "docs/new/en/guides/user-manual.md"
  "docs/new/tr/guides/user-manual.md"
)

for f in "${REQ_FILES[@]}"; do
  [[ -f "$f" ]] || fail "Missing required doc: $f"
done

# 2) EN/TR parallel set (by relative path)
info "Checking EN/TR mirrored file set"
EN_LIST=$(find docs/new/en -type f -name '*.md' | sed 's#^docs/new/en/##' | sort)
TR_LIST=$(find docs/new/tr -type f -name '*.md' | sed 's#^docs/new/tr/##' | sort)

if [[ "$EN_LIST" != "$TR_LIST" ]]; then
  echo "--- EN only ---" >&2
  comm -23 <(printf "%s\n" "$EN_LIST") <(printf "%s\n" "$TR_LIST") >&2 || true
  echo "--- TR only ---" >&2
  comm -13 <(printf "%s\n" "$EN_LIST") <(printf "%s\n" "$TR_LIST") >&2 || true
  fail "EN/TR docs are not mirrored"
fi

# 3) Required headings in Quickstart/Ops Manual
info "Checking required headings"
for lang in en tr; do
  QS="docs/new/$lang/guides/quickstart.md"
  OM="docs/new/$lang/guides/ops-manual.md"

  if [[ "$lang" == "en" ]]; then
    grep -q "^# Quickstart" "$QS" || fail "$QS missing title"
    grep -q "^# Operations Manual" "$OM" || fail "$OM missing title"
  else
    # TR titles (fully translated)
    grep -q "^# Hızlı Başlangıç" "$QS" || fail "$QS missing TR title"
    grep -q "^# Operasyonel Rehber" "$OM" || fail "$OM missing TR title"
  fi

  grep -q "## 1" "$QS" || fail "$QS missing numbered sections"
  grep -q "## 1" "$OM" || fail "$OM missing numbered sections"
done

# 3b) Ensure EN/TR section skeleton for Quickstart/Ops Manual matches
# We compare H2 headings only ("## "), ignoring the actual language.
info "Checking EN/TR section skeleton (H2 headings)"
extract_h2() {
  # Normalize numbered headings by extracting only the section number.
  # Example: "## 1) System requirements" -> "## 1)"
  sed -n 's/^## \([0-9]\+\).*$/## \1)/p' "$1"
}

EN_QS_H2=$(extract_h2 docs/new/en/guides/quickstart.md)
TR_QS_H2=$(extract_h2 docs/new/tr/guides/quickstart.md)
[[ "$EN_QS_H2" == "$TR_QS_H2" ]] || fail "Quickstart EN/TR H2 skeleton mismatch"

EN_OM_H2=$(extract_h2 docs/new/en/guides/ops-manual.md)
TR_OM_H2=$(extract_h2 docs/new/tr/guides/ops-manual.md)
[[ "$EN_OM_H2" == "$TR_OM_H2" ]] || fail "Ops-manual EN/TR H2 skeleton mismatch"

# 4) Env example existence check
info "Checking .env.example references"
[[ -f ".env.example" ]] || fail "Missing root .env.example"
[[ -f "backend/.env.example" ]] || fail "Missing backend/.env.example"
[[ -f "frontend/.env.example" ]] || fail "Missing frontend/.env.example"
[[ -f "frontend-player/.env.example" ]] || fail "Missing frontend-player/.env.example"

# 5) Relative link check (repo-internal only)
# We only validate markdown links that are relative and point to .md files.
info "Checking relative markdown links"
MD_FILES=$(find docs/new -type f -name '*.md' | sort)

while IFS= read -r file; do
  dir=$(dirname "$file")
  # Extract links: [text](path)
  # Keep only relative links not starting with http(s), /, #
  while IFS= read -r link; do
    path=$(echo "$link" | sed -E 's/.*\(([^)]+)\).*/\1/' | cut -d'#' -f1)
    [[ -z "$path" ]] && continue
    [[ "$path" =~ ^https?:// ]] && continue
    [[ "$path" =~ ^/ ]] && continue
    [[ "$path" =~ ^# ]] && continue

    # only validate markdown/doc targets
    if [[ "$path" == *.md ]]; then
      target="$dir/$path"
      target=$(python3 -c "import os; print(os.path.normpath('$target'))")
      [[ -f "$target" ]] || fail "Broken link in $file -> $path (resolved: $target)"
    fi
  done < <(grep -oE '\[[^\]]+\]\([^)]+\)' "$file" || true)

done <<< "$MD_FILES"

# 6) Lightweight command validations (no side effects)
# Keep these checks portable: CI runners will have them, but local environments may not.
info "Checking tooling availability (non-heavy)"
python3 --version >/dev/null 2>&1 || fail "python3 missing"
yarn --version >/dev/null 2>&1 || fail "yarn missing"

if command -v docker >/dev/null 2>&1; then
  docker --version >/dev/null 2>&1 || fail "docker present but not working"
else
  info "docker not found (skipping)"
fi

if command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1; then
  (docker-compose version >/dev/null 2>&1 || docker compose version >/dev/null 2>&1) || info "docker compose not available (skipping)"
else
  info "docker compose not found (skipping)"
fi

info "Docs smoke checks passed"
