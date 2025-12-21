#!/usr/bin/env bash
set -euo pipefail

# Generate a STG-SecHeaders-01 proof file from the template.
#
# Usage (from repo root):
#   ./scripts/gen_secheaders_proof.sh
#   DATE=2025-12-21 NAMESPACE=casino-admin-staging DEPLOY=frontend-admin STAGING_DOMAIN=headers-ops-ready.preview.emergentagent.com ./scripts/gen_secheaders_proof.sh
#
# Notes:
# - This script fills ONLY the Metadata/Target headers from the template.
# - Operator/Reviewer default to <fill-me>; set OPERATOR/REVIEWER env if you want them pre-filled.
# - After generation, operator should review the file, adjust Operator if desired, then commit.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="${REPO_ROOT}/docs/ops/proofs/secheaders/STG-SecHeaders-01.template.md"

if [[ ! -f "${TEMPLATE}" ]]; then
  echo "Template not found: ${TEMPLATE}" >&2
  exit 1
fi

DATE="${DATE:-$(date -u +%Y-%m-%d)}"
OUT="${REPO_ROOT}/docs/ops/proofs/secheaders/${DATE}.md"
TIME_UTC_VAL="${TIME_UTC:-$(date -u +%H:%M:%S)} UTC"

# Allow operator to override via env, otherwise best-effort defaults.
KUBECONTEXT_VAL="${KUBECONTEXT:-$(kubectl config current-context 2>/dev/null || echo '<fill-me>')}"
NAMESPACE_VAL="${NAMESPACE:-<fill-me>}"
DEPLOY_VAL="${DEPLOY:-<fill-me>}"
STAGING_DOMAIN_VAL="${STAGING_DOMAIN:-<fill-me>}"
OPERATOR_VAL="${OPERATOR:-<fill-me>}"
REVIEWER_VAL="${REVIEWER:-<fill-me>}"

mkdir -p "${REPO_ROOT}/docs/ops/proofs/secheaders"

echo "Generating STG-SecHeaders-01 proof from template:"
echo "  Template   : ${TEMPLATE}"
echo "  Output file: ${OUT}"
echo "  Date       : ${DATE}"
echo "  Time (UTC) : ${TIME_UTC_VAL}"
echo "  kubecontext: ${KUBECONTEXT_VAL}"
echo "  namespace  : ${NAMESPACE_VAL}"
echo "  deployment : ${DEPLOY_VAL}"
echo "  domain     : ${STAGING_DOMAIN_VAL}"

# Substitute header placeholders; body (verification outputs, PASS checkboxes, etc.) is left unchanged.
sed \
  -e "s|- Date (YYYY-MM-DD): <fill-me>|- Date (YYYY-MM-DD): ${DATE}|" \
  -e "s|- Time (UTC): <fill-me>|- Time (UTC): ${TIME_UTC_VAL}|" \
  -e "s|- Operator: <fill-me>|- Operator: ${OPERATOR_VAL}|" \
  -e "s|- Reviewer (optional): <fill-me>|- Reviewer (optional): ${REVIEWER_VAL}|" \
  -e "s|- kubecontext: <fill-me>|- kubecontext: ${KUBECONTEXT_VAL}|" \
  -e "s|- namespace: <fill-me>|- namespace: ${NAMESPACE_VAL}|" \
  -e "s|- deployment: <fill-me>|- deployment: ${DEPLOY_VAL}|" \
  -e "s|- domain: <fill-me> (STAGING_DOMAIN)|- domain: ${STAGING_DOMAIN_VAL} (STAGING_DOMAIN)|" \
  "${TEMPLATE}" > "${OUT}"

echo "Done. Please review ${OUT}, update Operator with your real name or leave blank as per policy, then commit the file as the proof artifact."
