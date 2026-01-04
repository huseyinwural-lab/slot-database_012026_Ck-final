# 🧪 Admin Invite Flow - Manuel Test Checklist

**Test Tarihi:** _____________  
**Test Eden:** _____________  
**Environment:** □ Staging  □ Production

---

## ✅ Test Senaryosu: Admin Davet Akışı E2E

### 📋 Ön Koşullar
- [ ] Backend servis çalışıyor (`/api/health` OK)
- [ ] Frontend erişilebilir
- [ ] PostgreSQL bağlantısı aktif (Docker: postgres servisi healthy)
- [ ] Test admin hesabı hazır: `admin@casino.com` / `Admin123!`

---

## 🔍 Test Adımları

### **ADIM 1: Davet Oluşturma**
**Eylem:** AdminManagement sayfasında yeni admin oluştur

**Checklist:**
- [ ] `/admin-management` sayfasını aç
- [ ] "Add New Admin" butonuna tıkla
- [ ] Formu doldur:
  - Email: `test-invite-{TIMESTAMP}@casino.com`
  - Name: `Test Invited Admin`
  - Role: `SUPPORT` (veya başka bir role)
  - Password Mode: **INVITE** (radio button seç)
- [ ] "Create Admin" butonuna tıkla
- [ ] "Copy Invite Link" modalı otomatik açıldı

**Beklenen Sonuç:**
- ✅ Modal açıldı ve invite link gösteriliyor
- ✅ Link formatı: `{FRONTEND_URL}/accept-invite?token=ey...`

**Kanıt Türü:** Ekran görüntüsü (modal + link visible)

**SONUÇ:** □ PASS  □ FAIL  
**Notlar:** _______________________________________

---

### **ADIM 2: Invite Link Kopyalama**
**Eylem:** Modaldan invite linkini kopyala

**Checklist:**
- [ ] "Copy Link" butonuna tıkla
- [ ] Toast bildirimi: "Invite link copied!"
- [ ] Clipboard'a kopyalanan linki bir yere yapıştır (doğrulama için)

**Beklenen Sonuç:**
- ✅ Link başarıyla kopyalandı
- ✅ Toast göründü

**Kanıt Türü:** Ekran görüntüsü (toast message)

**SONUÇ:** □ PASS  □ FAIL  
**Notlar:** _______________________________________

---

### **ADIM 3: Veritabanı Kontrol (İlk Durum)**
**Eylem:** PostgreSQL'de yeni oluşturulan admin'in durumunu kontrol et

**Komut:**
```bash
# Backend container içinde (örnek)
psql "$DATABASE_URL" -c "SELECT email, status, invite_token, invite_expires_at FROM adminuser WHERE email='test-invite-XXXXXX@casino.com'"
```

**Beklenen Sonuç:**
```json
{
  "email": "test-invite-XXXXXX@casino.com",
  "status": "INVITED",
  "invite_token": "ey...JWT_TOKEN...",
  "invite_expires_at": "2025-XX-XXT...Z"
}
```

**Checklist:**
- [ ] `status` = `"INVITED"`
- [ ] `invite_token` var (JWT formatında)
- [ ] `invite_expires_at` gelecekte bir tarih

**Kanıt Türü:** Terminal çıktısı (token'ı `***MASKED***` ile maskele)

**SONUÇ:** □ PASS  □ FAIL  
**Notlar:** _______________________________________

---

### **ADIM 4: Accept Invite Sayfası Açma**
**Eylem:** Yeni browser tab/incognito'da invite linkini aç

**Checklist:**
- [ ] Yeni tarayıcı sekmesi (veya incognito) aç
- [ ] Kopyalanan invite linkini adres çubuğuna yapıştır
- [ ] Sayfa yüklendi: `/accept-invite?token=...`

**Beklenen Sonuç:**
- ✅ Sayfa başarıyla yüklendi
- ✅ Form gösteriliyor: Email (read-only), Password, Confirm Password
- ✅ Email otomatik doldurulmuş: `test-invite-XXXXXX@casino.com`

**Kanıt Türü:** Ekran görüntüsü (Accept Invite sayfası)

**SONUÇ:** □ PASS  □ FAIL  
**Notlar:** _______________________________________

---

### **ADIM 5: Şifre Belirleme**
**Eylem:** Yeni şifre belirle ve formu gönder

**Checklist:**
- [ ] Password alanı: `NewPassword123!`
- [ ] Confirm Password alanı: `NewPassword123!`
- [ ] "Set Password & Activate" butonuna tıkla

**Beklenen Sonuç:**
- ✅ Form başarıyla gönderildi
- ✅ Yönlendirme: `/login` sayfasına otomatik geçiş
- ✅ Toast mesajı: "Account activated! Please login."

**Kanıt Türü:** Ekran görüntüsü (login page + toast)

**SONUÇ:** □ PASS  □ FAIL  
**Notlar:** _______________________________________

---

### **ADIM 6: Backend Accept-Invite Endpoint Testi (CURL)**
**Eylem:** API doğrudan curl ile test et

**Komut:**
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

curl -X POST "$API_URL/api/v1/auth/accept-invite" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "ey...GERÇEK_JWT_TOKEN...",
    "new_password": "NewPassword123!"
  }'
```

**Beklenen Sonuç:**
```json
{
  "message": "Account activated successfully",
  "email": "test-invite-XXXXXX@casino.com"
}
```

**Checklist:**
- [ ] HTTP Status: `200 OK`
- [ ] Response JSON'da `message` var
- [ ] Response JSON'da `email` doğru

**Kanıt Türü:** Terminal çıktısı

**SONUÇ:** □ PASS  □ FAIL  
**Notlar:** _______________________________________

---

### **ADIM 7: Login İşlemi**
**Eylem:** Yeni belirlenen şifre ile giriş yap

**Checklist:**
- [ ] Email: `test-invite-XXXXXX@casino.com`
- [ ] Password: `NewPassword123!`
- [ ] "Login" butonuna tıkla

**Beklenen Sonuç:**
- ✅ Login başarılı
- ✅ Dashboard'a yönlendirildi
- ✅ Toast: "Login successful!"
- ✅ Kullanıcı adı header'da görünüyor

**Kanıt Türü:** Ekran görüntüsü (dashboard after login)

**SONUÇ:** □ PASS  □ FAIL  
**Notlar:** _______________________________________

---

### **ADIM 8: Veritabanı Kontrol (Final Durum)**
**Eylem:** PostgreSQL'de admin'in güncellenmiş durumunu kontrol et

**Komut:**
```bash
psql "$DATABASE_URL" -c "SELECT email, status, invite_token, invite_expires_at, hashed_password FROM adminuser WHERE email='test-invite-XXXXXX@casino.com'"
```

**Beklenen Sonuç:**
```json
{
  "email": "test-invite-XXXXXX@casino.com",
  "status": "ACTIVE",
  "password_hash": "$2b$...",
  "invite_token": null,
  "invite_expires_at": null
}
```

**Checklist:**
- [ ] `status` = `"ACTIVE"`
- [ ] `invite_token` = `null` veya field yok
- [ ] `invite_expires_at` = `null` veya field yok
- [ ] `password_hash` var (bcrypt formatında)

**Kanıt Türü:** Terminal çıktısı

**SONUÇ:** □ PASS  □ FAIL  
**Notlar:** _______________________________________

---

## 🚨 Negatif Test Senaryoları (Opsiyonel)

### **TEST A: Expired Token**
- [ ] Token süresi dolmuş bir link ile test et
- [ ] Beklenen: `400 Bad Request` - "Invalid or expired token"

**SONUÇ:** □ PASS  □ FAIL  □ SKIPPED

---

### **TEST B: Invalid Token**
- [ ] Geçersiz/manipüle edilmiş token ile test et
- [ ] Beklenen: `400 Bad Request` - "Invalid token"

**SONUÇ:** □ PASS  □ FAIL  □ SKIPPED

---

### **TEST C: Şifre Doğrulama**
- [ ] Password ve Confirm Password eşleşmiyor
- [ ] Beklenen: Frontend validation hatası

**SONUÇ:** □ PASS  □ FAIL  □ SKIPPED

---

## 📊 Genel Test Özeti

**Toplam Test:** 8 (Ana) + 3 (Negatif)  
**PASS:** _____ / 8  
**FAIL:** _____ / 8  
**Kritik Blocker:** □ Var  □ Yok

**Genel Değerlendirme:**
- [ ] ✅ Feature production-ready
- [ ] ⚠️ Minor issue var (detay ekle)
- [ ] ❌ Major bug var (blocker)

**Ek Notlar:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

**İmza:** _____________  **Tarih:** _____________