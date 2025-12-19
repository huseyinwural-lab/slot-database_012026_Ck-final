# Proof — STG-SecHeaders-01 (Staging) — Security Headers Enablement

> Purpose: Standard proof artifact for **STG-SecHeaders-01** (CSP Report-Only + low HSTS) in staging.

---

## Metadata
- Date (YYYY-MM-DD): <fill-me>
- Time (UTC): <fill-me>
- Operator: <fill-me>
- Reviewer (optional): <fill-me>

## Target
- kubecontext: <fill-me>
- namespace: <fill-me>
- deployment: <fill-me>
- domain: <fill-me> (STAGING_DOMAIN)
- expected `SECURITY_HEADERS_MODE`: `report-only`

---

## Change summary
- Applied ConfigMap: `k8s/frontend-admin-security-headers-configmap.yaml`
- Applied patch/overlay: `k8s/frontend-admin-security-headers.patch.yaml`
- Ensured env:
  - `SECURITY_HEADERS_MODE=report-only`

---

## Verification

### 1) Header check (curl)
Command:
```bash
export STAGING_DOMAIN="<fill-me>"
curl -I "https://${STAGING_DOMAIN}/" | egrep -i "content-security-policy|strict-transport-security" | tee secheaders-proof.txt
```

Output (paste exact content from `secheaders-proof.txt`):
```text
<paste here>
```

### 2) Pod log check (selector script ran)
Command:
```bash
export NS="<fill-me>"
export DEPLOY="<fill-me>"
kubectl -n "$NS" logs deploy/"$DEPLOY" --tail=200 | egrep -i "\[security-headers\]|security-headers|snippets"
```

Output:
```text
<paste here>
```

---

## PASS criteria (must be explicit)
- [ ] `Content-Security-Policy-Report-Only` header is present
- [ ] `Strict-Transport-Security` header is present (staging low max-age, e.g. `max-age=300`)
- [ ] Pod logs show selector ran (e.g. `[security-headers] mode=report-only -> /etc/nginx/snippets/security_headers_active.conf`)

---

## Notes / Observations (optional)
- <fill-me>
