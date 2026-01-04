# Mimari Ana Planı & Sözleşme

Bu doküman, Tenant/Admin Mimarisi için "Tek Doğru Kaynak" olarak hizmet eder.

## 0) Hazırlık & Sözleşmeler

### Tenant / Admin / Rol / İzin Sözleşmesi
*   **Tenant Kimliği:** `X-Tenant-ID` başlığı üzerinden iletilir.
*   **Admin Bağlamı:** JWT `sub` -> `AdminUser` -> `tenant_id` + `tenant_role` üzerinden çözülür.
*   **Özellik Bayrakları:** Backend `ensure_tenant_feature(flag)` kullanır. Frontend `RequireFeature` HOC kullanır.

### API Sözleşmesi & Hata Standartları
Tüm API hataları bu JSON formatını takip etmelidir:```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "The requested player was not found.",
  "details": { "id": "123" },
  "timestamp": "2023-10-27T10:00:00Z"
}
```*   **401:** Yetkisiz (Geçersiz/Eksik Token)
*   **403:** Yasak (Geçerli Token, Yetersiz İzin/Rol)
*   **404:** Kaynak Bulunamadı (Tenant kapsamlı)
*   **422:** Doğrulama Hatası (Pydantic standardı)

## 1) Onboarding & Kimlik

*   **Giriş:** JWT tabanlı (Access + Refresh stratejisi).
*   **Davet Akışı:** Admin Oluşturma -> Davet Token'ı -> E-posta Bağlantısı -> Şifre Belirleme -> Aktif.
*   **Güvenlik:** Giriş uç noktalarında rate limiting.

## 2) Bağlam & RBAC

*   **Tenant Çözümleyici:** Backend bağımlılığı `get_current_tenant_id`.
*   **RBAC:** `require_tenant_role(["finance", "operations"])`.
*   **Denetim:** Tüm yazma işlemleri `AdminActivityLog` içine loglanmalıdır.

## 3) Uygulama İskeleti (Tenant UI)

*   **Global Durum:** `CapabilitiesContext`, `tenant_role` ve `features` değerlerini tutar.
*   **Yerleşim:** Sidebar görünürlüğü `isOwner` ve `features` tarafından kontrol edilir.

## 4) Tenant Modülleri (Uygulanan)

*   4.1 Dashboard
*   4.2 Oyuncular (Liste, Detay, KYC, Bakiye)
*   4.3 Oyunlar (Katalog, Konfigürasyon, RTP)
*   4.4 Bonuslar (Kurallar, Tetikleyici)
*   4.5 Raporlar (Gelir)
*   4.6 Finans (İşlemler, Ödeme Onayı)

## 5) Tenant Admin Yönetimi

*   Alt admin oluştur/davet et.
*   Rol Ataması (Finans, Ops, Destek).
*   İzin Matrisi (Şimdilik salt okunur görünüm).

## 6) API Anahtarları & Entegrasyonlar

*   Kapsamlarla API Anahtarı CRUD.
*   Anahtar başına IP Allowlist.

## 7) Ayarlar & Güvenlik

*   Tenant Ayarları (Marka, Dil/Bölge).
*   Güvenlik Sıkılaştırma (Oturum zaman aşımı).

## 8) Gözlemlenebilirlik

*   Yapılandırılmış Loglama.
*   Sağlık Kontrolleri.

## 9) Yayın & Operasyonlar

*   Seed Script'leri.
*   Migrasyon stratejisi.