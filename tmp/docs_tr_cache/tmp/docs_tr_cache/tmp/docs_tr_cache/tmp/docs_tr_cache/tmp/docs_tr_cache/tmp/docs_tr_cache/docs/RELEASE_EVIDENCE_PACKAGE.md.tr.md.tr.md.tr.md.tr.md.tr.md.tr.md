# 📦 Release Evidence Package - PR-1 & PR-2

**Release Version:** v1.0.0 (Production Hardening + Admin Invite Flow)  
**Release Date:** _____________  
**Prepared By:** _____________

---

## 🎯 Release Scope

### PR-1: Production Hardening & Operational Maturity
- ✅ CORS Allowlist
- ✅ Server-side Pagination (Players, Transactions, Games, Tenants)
- ✅ PostgreSQL Schema & Migrations (Alembic baseline)
- ✅ Request Logging (Correlation IDs)
- ✅ Health Probes (`/api/health`, `/api/readiness`)
- ✅ Rate Limiting (Login endpoint)
- ✅ Tenant Feature Enforcement (Backend guards)
- ✅ Documentation (Backup/Restore, Prod Checklist)

### PR-2: Admin Invite Flow UX Enhancement
- ✅ Copy Invite Link Modal
- ✅ Public Accept Invite Page

---

## 🔍 Kanıt Paketleri

### 1️⃣ Health & Readiness Probes

#### **Health Check (Liveness)**
**Komut:**
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
curl -X GET "$API_URL/api/health"
```

**Beklenen Çıktı:**
```json
{
  "status": "healthy"
}
```

**Çıktı:**
```
[BURAYA CURL ÇIKTISINI YAPIŞTIRIN]
```

**Durum:** □ PASS  □ FAIL  
**Tarih/Saat:** _____________

---

#### **Readiness Check (Dependencies)**
**Komut:**
```bash
curl -X GET "$API_URL/api/readiness"
```

**Beklenen Çıktı:**
```json
{
  "status": "ready",
  "database": "connected"
}
```

**Çıktı:**
```
[BURAYA CURL ÇIKTISINI YAPIŞTIRIN]
```

**Durum:** □ PASS  □ FAIL  
**Tarih/Saat:** _____________

---

### 2️⃣ Admin Invite Flow E2E Ekran Görüntüleri

#### **Screenshot 1: Copy Invite Link Modal**
**Açıklama:** Admin oluşturulduktan sonra açılan modal
- Dosya: `invite_modal_YYYYMMDD.png`
- Durum: □ Eklendi

---

#### **Screenshot 2: Accept Invite Page**
**Açıklama:** Public invite acceptance form
- Dosya: `accept_invite_page_YYYYMMDD.png`
- Durum: □ Eklendi

---

#### **Screenshot 3: Success Toast & Login Redirect**
**Açıklama:** Başarılı aktivasyon sonrası login sayfası
- Dosya: `invite_success_toast_YYYYMMDD.png`
- Durum: □ Eklendi

---

#### **Screenshot 4: Dashboard After Login**
**Açıklama:** Yeni admin ile başarılı login
- Dosya: `new_admin_dashboard_YYYYMMDD.png`
- Durum: □ Eklendi

---

### 3️⃣ Database State Evidence

#### **Durum 1: INVITED (Token Var)**
**Komut:**
```bash
# PostgreSQL (SQLModel) – örnek sorgu (tablo/kolon isimlerini şemaya göre uyarlayın)
psql "$DATABASE_URL" -c "SELECT email, status, invite_token, invite_expires_at FROM adminuser WHERE email='test-invite-XXXXX@casino.com'" 
```

**Çıktı:**
```
[BURAYA MASKELENMIŞ ÇIKTIYI YAPIŞTIRIN]
```

**Kontroller:**
- [ ] `status` = `"INVITED"`
- [ ] `invite_token` var (masked)
- [ ] `invite_expires_at` var

**Durum:** □ PASS  □ FAIL

---

#### **Durum 2: ACTIVE (Token Temizlendi)**
**Komut:**
```bash
# PostgreSQL (SQLModel) – örnek sorgu (tablo/kolon isimlerini şemaya göre uyarlayın)
psql "$DATABASE_URL" -c "SELECT email, status, invite_token, invite_expires_at, hashed_password FROM adminuser WHERE email='test-invite-XXXXX@casino.com'"
```

**Çıktı:**
```
[BURAYA MASKELENMIŞ ÇIKTIYI YAPIŞTIRIN]
```

**Kontroller:**
- [ ] `status` = `"ACTIVE"`
- [ ] `invite_token` = `null` veya yok
- [ ] `invite_expires_at` = `null` veya yok
- [ ] `password_hash` var (masked)

**Durum:** □ PASS  □ FAIL

---

### 4️⃣ Pagination & Performance Evidence

#### **Players List Endpoint**
**Komut:**
```bash
TOKEN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@casino.com","password":"Admin123!"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

curl -X GET "$API_URL/api/v1/players?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Beklenen Format:**
```json
{
  "items": [...],
  "meta": {
    "page": 1,
    "page_size": 10,
    "total": 150,
    "pages": 15
  }
}
```

**Çıktı:**
```
[BURAYA İLK 20 SATIRI YAPIŞTIRIN]
```

**Kontroller:**
- [ ] `items` array var
- [ ] `meta` object var
- [ ] `meta.page`, `meta.total` doğru

**Durum:** □ PASS  □ FAIL

---

### 5️⃣ Rate Limiting Evidence

#### **Login Rate Limit Test**
**Komut:**
```bash
for i in {1..6}; do
  echo "Request $i:"
  curl -s -w "\nHTTP Status: %{http_code}\n" \
    -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
  echo "---"
done
```

**Beklenen:**
- İlk 5 istek: `401 Unauthorized` (wrong credentials)
- 6. istek: `429 Too Many Requests`

**Çıktı:**
```
[BURAYA ÇIKTIYI YAPIŞTIRIN]
```

**Kontroller:**
- [ ] 6. istekte `429` geldi
- [ ] Response: "Rate limit exceeded"

**Durum:** □ PASS  □ FAIL

---

### 6️⃣ CORS Validation

#### **CORS Headers Check**
**Komut:**
```bash
curl -I -X OPTIONS "$API_URL/api/v1/players" \
  -H "Origin: https://unauthorized-domain.com" \
  -H "Access-Control-Request-Method: GET"
```

**Beklenen:**
- Authorized origin: `Access-Control-Allow-Origin` header var
- Unauthorized origin: Header yok veya specific origin

**Çıktı:**
```
[BURAYA HEADERS ÇIKTISINI YAPIŞTIRIN]
```

**Kontroller:**
- [ ] CORS policy aktif
- [ ] Unauthorized origin reddedildi

**Durum:** □ PASS  □ FAIL

---

### 7️⃣ Tenant Feature Enforcement

#### **Feature Guard Test (can_manage_admins=false)**
**Komut:**
```bash
# Tenant'ta can_manage_admins=false olan bir user ile login ol
# (Test için manuel olarak DB'de bir tenant'ın feature'ını false yap)

curl -X POST "$API_URL/api/v1/admins" \
  -H "Authorization: Bearer $TOKEN_WITH_NO_ADMIN_FEATURE" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","name":"Test","role":"SUPPORT","tenant_id":"..."}'
```

**Beklenen:**
```json
{
  "detail": "Your tenant does not have permission to manage admins"
}
```

**Çıktı:**
```
[BURAYA ÇIKTIYI YAPIŞTIRIN]
```

**Kontroller:**
- [ ] HTTP Status: `403 Forbidden`
- [ ] Detail message uygun

**Durum:** □ PASS  □ FAIL  □ SKIPPED

---

## 📋 Deployment Checklist (PROD_CHECKLIST.md'den)

- [ ] Environment variables set (DATABASE_URL, JWT_SECRET, CORS_ORIGINS)
- [ ] PostgreSQL schema ready (Alebmic baseline applied)
- [ ] Health checks responding
- [ ] Rate limiting active
- [ ] CORS allowlist configured
- [ ] Backup procedure documented
- [ ] Monitoring/logging active (correlation IDs in logs)

---

## ✅ Final Approval

**PR-1 Status:** □ APPROVED  □ NEEDS WORK  
**PR-2 Status:** □ APPROVED  □ NEEDS WORK

**Blocker Issues:** _____________________________________________

**Deploy to Production:** □ APPROVED  □ HOLD

**Approver:** _____________  **Signature:** _____________  **Date:** _____________

---

## 📎 Ek Dosyalar

- [ ] `/app/docs/INVITE_FLOW_TEST_CHECKLIST.md` (completed)
- [ ] Ekran görüntüleri (4 adet)
- [ ] Curl output logs
- [ ] Database state dumps (masked)