# STG-SecHeaders-01 — Staging Security Headers (CSP Report-Only + Low HSTS)

Amaç: **admin UI (frontend-admin nginx)** üzerinde **CSP (Report-Only)** ve **HSTS (low max-age)** başlıklarını staging’de güvenli şekilde açmak.

Bu dosya **yalnızca** uygulama / doğrulama / rollback komut setini içerir.

---

## 1) Ön koşullar

Gereken hedefler:
- `kubecontext` (staging cluster context)
- `namespace`
- `frontend-admin` Deployment adı (env set edilecek obje)

### kubecontext nasıl seçilir?
```bash
kubectl config get-contexts
kubectl config use-context <staging-context>
```

### Namespace nasıl bulunur?
Sisteminizde admin UI’nin olduğu namespace’i bulun:
```bash
kubectl get ns
# veya isimle filtreleyin (örnek)
kubectl get ns | egrep -i "stg|stage|casino|admin|frontend"
```

### Deployment adı nasıl bulunur?
Namespace’i belirledikten sonra:
```bash
kubectl -n "<namespace>" get deploy
# veya filtreleyin (örnek)
kubectl -n "<namespace>" get deploy | egrep -i "frontend|admin|ui"
```

---

## 2) Uygulama

### Minimum komut seti (copy/paste)
```bash
# 0) hedefleri doldur
export NS="<namespace>"
export DEPLOY="<frontend-admin-deployment-name>"
export STAGING_DOMAIN="<fill-me>"

# 1) configmap + patch uygula
kubectl -n "$NS" apply -f k8s/frontend-admin-security-headers-configmap.yaml
kubectl -n "$NS" apply -f k8s/frontend-admin-security-headers.patch.yaml

# 2) report-only aktif et
kubectl -n "$NS" set env deploy/"$DEPLOY" SECURITY_HEADERS_MODE=report-only

# 3) rollout
kubectl -n "$NS" rollout restart deploy/"$DEPLOY"
kubectl -n "$NS" rollout status deploy/"$DEPLOY" --timeout=180s
```

Notlar:
- `SECURITY_HEADERS_MODE` geçerli değerler: `off | report-only | enforce`
- Bu task için hedef: **`report-only`**
- Patch içinde `metadata.name: frontend-admin` placeholder olabilir. Sizdeki deployment adı farklıysa:
  - Ya patch’i kendi deployment adınıza uyarlayın,
  - Ya da mevcut release/kustomize overlay akışınıza göre uygulayın.

---

## 3) Doğrulama

### 3.1 Header doğrulama (curl)
```bash
curl -I "https://${STAGING_DOMAIN}/" | egrep -i "content-security-policy|strict-transport-security"

# proof için dosyaya yazdır
curl -I "https://${STAGING_DOMAIN}/" | egrep -i "content-security-policy|strict-transport-security" | tee secheaders-proof.txt
```
Beklenen:
- `Content-Security-Policy-Report-Only` header’ı görünür
- `Strict-Transport-Security` header’ı görünür (staging için düşük max-age, örn. `max-age=300`)

### 3.1.1 Proof Recording (repo’ya kanıt)
Operatör kanıtı **repo’ya** şu standart formatla kaydeder:

1) Template’i kopyala:
```bash
cp docs/ops/proofs/secheaders/STG-SecHeaders-01.template.md \
  docs/ops/proofs/secheaders/$(date -u +%F).md
```

2) Template içindeki `Metadata/Target` alanlarını doldur.

3) `secheaders-proof.txt` içeriğini (curl çıktısı) ilgili bölüme **aynen** yapıştır.

4) Pod log kontrol komutunun çıktısını (selector script) ilgili bölüme yapıştır.

PASS kriteri (kanıt dosyasında açıkça işaretlenmeli):
- `Content-Security-Policy-Report-Only` mevcut
- `Strict-Transport-Security` mevcut
- Pod log’larında `mode=report-only` seçimi görülüyor

### 3.2 Pod log kontrolü (selector script çalıştı mı?)
Selector script, container start’ında mode seçip şunu loglar:
- `[security-headers] mode=... -> /etc/nginx/snippets/security_headers_active.conf`

Kısa kontrol:
```bash
# Pod’ları bulun
kubectl -n "$NS" get pods -l app=frontend-admin

# Bir pod seçip loglarda security-headers satırını arayın
kubectl -n "$NS" logs deploy/"$DEPLOY" --tail=200 | egrep -i "security-headers|snippets"
```

---

## 4) Rollback (≤ 5 dk)

Rollback hedefi: Security headers’ı kapat (`SECURITY_HEADERS_MODE=off`) ve pod’ları yeniden başlat.

```bash
kubectl -n "$NS" set env deploy/"$DEPLOY" SECURITY_HEADERS_MODE=off
kubectl -n "$NS" rollout restart deploy/"$DEPLOY"
kubectl -n "$NS" rollout status deploy/"$DEPLOY" --timeout=180s
```

---

## 5) Sık hata / çözüm

### 5.1 `curl` 404 değil ama header yok → yanlış Service/Ingress
Semptom:
- Sayfa geliyor (200/304 vb.) ama CSP/HSTS yok.

Muhtemel neden:
- İstek admin UI nginx’e değil başka bir route/service’e gidiyor.

Çözüm:
- Doğru domain/ingress’i doğrulayın.
- Gerekirse `/` yerine admin UI’nin kesin endpoint’ini test edin.

### 5.2 `nginx reload` yok → pod restart gerekir
Semptom:
- ConfigMap apply edildi ama header değişmiyor.

Neden:
- Nginx config/snippet seçimi container start aşamasında yapılıyor.

Çözüm:
- `kubectl rollout restart deploy/...` çalıştırın ve `rollout status` bekleyin.

### 5.3 ConfigMap mount permission / RO-RW ayrımı
Semptom:
- Pod loglarında script hata veriyor (copy/cp permission), header aktifleşmiyor.

Neden:
- `snippets-src` RO olmalı, aktif snippet hedefi (`/etc/nginx/snippets`) RW olmalı.

Çözüm:
- Patch’teki iki mount’un ayrı olduğunu doğrulayın:
  - `snippets-src` (ConfigMap, readOnly)
  - `snippets` (emptyDir, writable)
