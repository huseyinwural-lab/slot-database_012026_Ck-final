# 🚀 Hızlı Admin Invite Flow Testi

## Test Adımları (5-10 dakika)

### ✅ ADIM 1: Admin Oluştur
1. Login olun: `admin@casino.com` / `Admin123!`
2. **Admin Management** sayfasına gidin (sol menüden)
3. **"Add New Admin"** butonuna tıklayın
4. Formu doldurun:
   - **Full Name:** `Test Invited User`
   - **Email:** `test-invite-$(date +%s)@casino.com` (veya benzersiz bir email)
   - **Role:** `SUPPORT` (veya başka bir rol)
   - **Password Mode:** ⚠️ **"Invite Link / First Login Password"** SEÇİN (önemli!)
5. **"Create"** butonuna tıklayın

**Beklenen:** "Copy Invite Link" modalı açılmalı ✅

---

### ✅ ADIM 2: Invite Linkini Kopyala
1. Modalda **"Copy Link"** butonuna tıklayın
2. **"Invite link copied!"** toast mesajını görmelisiniz
3. Linki bir yere yapıştırın (örnek: notepad)

**Link formatı:** `https://paywallet-epic.preview.emergentagent.com/accept-invite?token=ey...`

---

### ✅ ADIM 3: Accept Invite Sayfasını Aç
1. **YENİ browser sekmesi** veya **incognito mode** açın
2. Kopyaladığınız linki adres çubuğuna yapıştırın
3. Enter'a basın

**Beklenen:**
- Sayfa yüklenmeli ✅
- Email otomatik doldurulmuş olmalı (read-only)
- Password ve Confirm Password alanları görünmeli

---

### ✅ ADIM 4: Şifre Belirle
1. **Password:** `NewPassword123!`
2. **Confirm Password:** `NewPassword123!`
3. **"Set Password & Activate"** butonuna tıklayın

**Beklenen:**
- Form başarıyla gönderilmeli
- `/login` sayfasına yönlendirilmelisiniz
- **"Account activated! Please login."** toast mesajı görünmeli

---

### ✅ ADIM 5: Yeni Şifre ile Login
1. Login sayfasında:
   - **Email:** Yeni oluşturduğunuz email (örn: `test-invite-XXXXX@casino.com`)
   - **Password:** `NewPassword123!`
2. **"Sign In"** butonuna tıklayın

**Beklenen:**
- Login başarılı olmalı ✅
- Dashboard'a yönlendirilmelisiniz
- Kullanıcı adı header'da görünmeli

---

## ✅ Test Başarılı mı?

Eğer tüm adımlar sorunsuz tamamlandıysa: **✅ BAŞARILI!**

Eğer herhangi bir adımda sorun yaşadıysanız:
- Ekran görüntüsü alın
- Hangi adımda hata olduğunu belirtin
- Hata mesajını paylaşın

---

## 🔍 Opsiyonel: Veritabanı Kontrolü (SQL)

Backend terminalinde aşağıdaki komutu çalıştırarak kullanıcının durumunu kontrol edebilirsiniz:

```bash
# PostgreSQL veya SQLite kullanıyorsanız
python3 /app/backend/check_live_db.py
```

---

## 📊 Test Sonucu

- [ ] ✅ PASS - Her şey çalıştı
- [ ] ⚠️ PARTIAL - Bazı sorunlar var
- [ ] ❌ FAIL - Çalışmadı

**Notlar:**
_________________________________________________________________
