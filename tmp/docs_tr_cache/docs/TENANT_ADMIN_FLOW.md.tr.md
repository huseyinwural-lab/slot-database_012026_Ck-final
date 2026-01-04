# 🏢 Kiracı (Tenant) ve Admin Yönetimi Akışı

## 📊 Mevcut Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                         SUPER ADMIN                         │
│                    (Default Casino - Owner)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Yönetir
                              ▼
        ┌──────────────────────────────────────────┐
        │            TENANT'LAR (Kiracılar)        │
        └──────────────────────────────────────────┘
                 │                    │
        ┌────────┴────────┐   ┌──────┴────────┐
        ▼                 ▼   ▼               ▼
    ┌─────────┐      ┌─────────┐      ┌─────────┐
    │ Tenant 1│      │ Tenant 2│      │ Tenant 3│
    │ (Owner) │      │ (Renter)│      │ (Renter)│
    └─────────┘      └─────────┘      └─────────┘
        │                 │                 │
        │ Her tenant'ın   │                 │
        │ kendi adminleri │                 │
        ▼                 ▼                 ▼
    ┌────────┐       ┌────────┐       ┌────────┐
    │Admin 1 │       │Admin 4 │       │Admin 6 │
    │Admin 2 │       │Admin 5 │       │Admin 7 │
    │Admin 3 │       │        │       │        │
    └────────┘       └────────┘       └────────┘
```

---

## 🔑 Anahtar Kavramlar

### **1. Tenant (Kiracı) Nedir?**
- Casino operasyonunun **ayrı bir müşterisi** veya **departmanı**
- Her tenant'ın **kendi verileri** var (oyuncular, oyunlar, işlemler)
- Her tenant'ın **farklı yetkileri** olabilir (feature flags)

### **2. Tenant Türleri**
- **Owner (Sahip):** Tüm yetkilere sahip ana tenant
- **Renter (Kiracı):** Sınırlı yetkilerle çalışan alt tenant

### **3. Admin ve Tenant İlişkisi**
Her admin **bir tenant'a ait**tir:
- Admin sadece kendi tenant'ının verilerini görebilir
- Admin tenant'ın yetkilerine bağlıdır (feature flags)

---

## 📋 Doğru Akış: Kiracıya Admin Ekleme

### **SENARYO 1: Super Admin → Yeni Kiracı + Admin Oluşturur**

```
┌─────────────────────────────────────────────────────────────┐
│  ADIM 1: Super Admin Yeni Kiracı Oluşturur                 │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
    Tenants sayfasına git
         │
         ▼
    "Create Tenant" formu doldur
         │
         ├─ Name: "Yeni Casino X"
         ├─ Type: Renter
         └─ Features:
             ├─ can_use_game_robot: ON
             ├─ can_edit_configs: OFF
             ├─ can_manage_bonus: ON
             └─ can_view_reports: ON
         │
         ▼
    "Create Tenant" butonuna tıkla
         │
         ▼
    ✅ Kiracı oluşturuldu (ID: tenant_xyz123)

┌─────────────────────────────────────────────────────────────┐
│  ADIM 2: Bu Kiracı için Admin Oluştur                      │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
    Admin Management sayfasına git
         │
         ▼
    "Add New Admin" formu doldur
         │
         ├─ Full Name: "Ali Yılmaz"
         ├─ Email: "ali@yenicasino.com"
         ├─ Role: MANAGER
         ├─ **Tenant: "Yeni Casino X"** ⬅️ ÖNEMLİ!
         └─ Password Mode: Invite Link
         │
         ▼
    "Create" butonuna tıkla
         │
         ▼
    ✅ Admin oluşturuldu
    ✅ Invite link modalı açıldı
         │
         ▼
    Invite linkini kopyala ve Ali'ye gönder
```

---

### **SENARYO 2: Kiracı Admini → Kendi Tenant'ına Admin Ekler**

```
┌─────────────────────────────────────────────────────────────┐
│  Ali (Yeni Casino X'in admini) login oldu                  │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
    Ali sadece "Yeni Casino X" tenant'ını görebilir
         │
         ▼
    Admin Management'a gider
         │
         ▼
    "Add New Admin" butonuna tıklar
         │
         ▼
    Form açılır - **Tenant otomatik seçili: "Yeni Casino X"**
    (Ali başka tenant seçemez)
         │
         ├─ Full Name: "Ayşe Demir"
         ├─ Email: "ayse@yenicasino.com"
         ├─ Role: SUPPORT
         └─ Password Mode: Invite Link
         │
         ▼
    ✅ Ayşe "Yeni Casino X" tenant'ına eklenmiş oldu
```

---

## 🔧 Teknik Detaylar

### **Backend: Admin Oluşturma**
```python
# /app/backend/app/routes/admin.py

@router.post("/users")
async def create_admin(payload: CreateAdminRequest, current_admin: AdminUser):
    # Eğer payload'da tenant_id yoksa, current admin'in tenant'ını kullan
    tenant_id = payload.tenant_id or current_admin.tenant_id
    
    # Super admin başka tenant'a admin ekleyebilir
    # Normal admin sadece kendi tenant'ına admin ekleyebilir
    if current_admin.role != "Super Admin":
        if tenant_id != current_admin.tenant_id:
            raise HTTPException(403, "Cannot create admin for another tenant")
    
    user = AdminUser(
        ...
        tenant_id=tenant_id,
        ...
    )
    
    await db.admins.insert_one(user.model_dump())
    return {"user": user, "invite_token": invite_token}
```

### **Frontend: Tenant Dropdown**
```jsx
// Super Admin ise: Tüm tenant'ları göster
// Normal Admin ise: Sadece kendi tenant'ını göster (disabled dropdown)

<Select
  value={newUser.tenant_id}
  onValueChange={(val) => setNewUser({ ...newUser, tenant_id: val })}
  disabled={currentUser.role !== 'Super Admin'}
>
  {tenants.map(t => (
    <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
  ))}
</Select>
```

---

## 📊 Örnek Veri Yapısı

### **Tenant Koleksiyonu (tenants)**
```json
{
  "id": "tenant_xyz123",
  "name": "Yeni Casino X",
  "type": "renter",
  "features": {
    "can_use_game_robot": true,
    "can_edit_configs": false,
    "can_manage_bonus": true,
    "can_view_reports": true
  },
  "created_at": "2025-12-12T10:00:00Z"
}
```

### **Admin Koleksiyonu (admins)**
```json
{
  "id": "admin_abc456",
  "username": "ali",
  "email": "ali@yenicasino.com",
  "full_name": "Ali Yılmaz",
  "role": "MANAGER",
  "tenant_id": "tenant_xyz123",  ⬅️ Bu tenant'a bağlı
  "status": "active",
  "created_at": "2025-12-12T10:05:00Z"
}
```

---

## 🎯 Kullanım Senaryoları

### **Senaryo A: Multi-Casino Operatörü**
```
Owner Tenant: "Ana Casino Grubu"
  ├─ Super Admin: ceo@anacasino.com
  │
Renter Tenant 1: "İstanbul Casino"
  ├─ Admin: istanbul@anacasino.com
  ├─ Manager: istanbulmanager@anacasino.com
  │
Renter Tenant 2: "Ankara Casino"
  ├─ Admin: ankara@anacasino.com
  └─ Support: ankarasupport@anacasino.com
```

**Avantaj:** Her casino kendi verilerini görür, birbirine karışmaz.

---

### **Senaryo B: Tek Casino - Departman Bazlı**
```
Owner Tenant: "Mega Casino"
  │
Renter Tenant 1: "VIP Departmanı"
  ├─ Admin: vip@megacasino.com
  │
Renter Tenant 2: "Bonus Departmanı"
  └─ Admin: bonus@megacasino.com
```

**Avantaj:** Departmanlar sadece kendi modüllerine erişir.

---

## ❓ SSS (Sık Sorulan Sorular)

### **S: Kiracı olmadan admin oluşturabilir miyim?**
**C:** Hayır. Her admin mutlaka bir tenant'a ait olmalıdır.

### **S: Bir admin birden fazla tenant'a ait olabilir mi?**
**C:** Hayır. Her admin sadece bir tenant'a aittir.

### **S: Super Admin hangi tenant'a aittir?**
**C:** Super Admin genellikle "Owner" tenant'a aittir ve tüm tenant'ları yönetebilir.

### **S: Kiracı kendi feature'larını değiştirebilir mi?**
**C:** Hayır. Sadece Super Admin (Owner tenant) kiracıların feature'larını değiştirebilir.

### **S: Invite linki tenant'a özel mi?**
**C:** Evet! Invite link ile oluşturulan admin otomatik olarak belirtilen tenant'a atanır.

---

## ✅ Kontrol Listesi: Doğru Kurulum

- [ ] Tenant'lar oluşturuldu
- [ ] Her tenant'ın feature'ları ayarlandı
- [ ] Super Admin var (Owner tenant'ta)
- [ ] Admin oluştururken tenant seçimi yapılıyor
- [ ] Normal adminler sadece kendi tenant'larında admin oluşturabiliyor
- [ ] Invite link doğru tenant'a yöneliyor
- [ ] Her admin login olduğunda sadece kendi tenant'ının verilerini görüyor

---

## 🚀 Sonraki Adımlar

1. **UI'da Tenant Dropdown Ekle** (Admin oluşturma formuna)
2. **Backend'de Yetki Kontrolü** (Normal admin başka tenant'a admin ekleyemesin)
3. **Admin Listesinde Tenant Göster** (Hangi admin hangi tenant'a ait)
4. **Tenant Filtreleme** (Sadece belirli tenant'ın adminlerini göster)
