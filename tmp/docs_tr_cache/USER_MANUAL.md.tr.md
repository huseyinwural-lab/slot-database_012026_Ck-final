# Casino Yönetim Paneli - Kapsamlı Kullanım Kılavuzu

Bu doküman, Casino Yönetim Paneli’nin tüm modüllerini ve özelliklerini ayrıntılandıran kapsamlı bir rehberdir.

## İçindekiler
1. [Giriş ve Genel Bakış](#1-introduction-and-overview)
2. [Gösterge Paneli](#2-dashboard)
3. [Oyuncu Yönetimi](#3-player-management)
4. [Finans Yönetimi](#4-finance-management)
5. [Oyun Yönetimi](#5-game-management)
6. [Bonus ve Kampanyalar](#6-bonus-and-campaigns)
7. [Risk ve Dolandırıcılık Yönetimi](#7-risk-and-fraud-management)
8. [CRM ve İletişim](#8-crm-and-communication)
9. [İçerik Yönetimi (CMS)](#9-content-management-cms)
10. [Destek Masası](#10-support-desk)
11. [Affiliate Yönetimi](#11-affiliate-management)
12. [Sorumlu Oyun (RG)](#12-responsible-gaming-rg)
13. [Admin ve Güvenlik Yönetimi](#13-admin-and-security-management)
14. [Özellik Bayrakları ve A/B Testi](#14-feature-flags-and-ab-testing)
15. [Simülasyon Laboratuvarı](#15-simulation-lab)
16. [Ayarlar Paneli (Multi-Tenant)](#16-settings-panel-multi-tenant)

---

## 1. Giriş ve Genel Bakış
Bu panel, modern bir çevrimiçi casino operasyonunun tüm yönlerini yönetmek üzere tasarlanmış, multi-tenant ve modüler bir yapıdır.

**Temel Özellikler:**
*   **Rol Tabanlı Erişim:** Kullanıcılar yalnızca yetkili oldukları modülleri görebilir.
*   **Multi-Tenant:** Birden fazla marka tek bir panelden yönetilebilir.
*   **Gerçek Zamanlı Veri:** Gösterge panelleri ve raporlar anlık verilerle beslenir.

---

## 2. Gösterge Paneli
Giriş yaptıktan sonra karşılaşılan ana ekran. Operasyonun genel sağlığını gösterir.
*   **KPI Kartları:** Günlük Yatırma, Çekme, GGR (Brüt Oyun Geliri), NGR (Net Oyun Geliri), Aktif Oyuncu sayısı.
*   **Grafikler:** Saatlik/Günlük gelir trendleri.
*   **Canlı Akış:** Son kayıt olan oyuncular, son büyük kazançlar, son yatırmalar.
*   **Acil Durumlar:** Onay bekleyen riskli çekimler veya yüksek tutarlı işlemler.

---

## 3. Oyuncu Yönetimi
Oyuncuların tüm yaşam döngüsünün yönetildiği bölüm.
*   **Oyuncu Listesi:** Gelişmiş filtreleme ile oyuncu arama (ID, Email, Kullanıcı Adı, IP, Kayıt Tarihi).
*   **Oyuncu Profili:**
    *   **Genel:** Bakiye, sadakat puanları, VIP seviyesi.
    *   **Cüzdan:** Gerçek para ve bonus bakiyesi detayları.
    *   **Oyun Geçmişi:** Oynanan oyunlar, bahis/kazanç detayları.
    *   **İşlem Geçmişi:** Tüm yatırma ve çekme işlemleri.
    *   **KYC:** Kimlik doğrulama dokümanları ve durumları.
    *   **Notlar:** Müşteri temsilcisi notları.

---

## 4. Finans Yönetimi
Para giriş ve çıkışlarının kontrol edildiği merkez.
*   **Yatırma Talepleri:** Bekleyen, onaylanan ve reddedilen yatırmalar. Manuel onay gerektiren yöntemler için aksiyon butonları.
*   **Çekim Talepleri:** Oyuncu çekim talepleri. Yüksek risk skorlu işlemler otomatik olarak "İnceleme" durumuna düşer.
*   **Raporlar:** Ödeme sağlayıcılarına göre raporlar, günlük nakit raporu.

---

## 5. Oyun Yönetimi
Casino lobisinin yönetildiği alan.
*   **Oyun Listesi:** Tüm oyunlar, sağlayıcılar, RTP oranları.
*   **Oyun Düzenleme:** Oyun adı, kategori, görseller ve aktiflik durumunun düzenlenmesi.
*   **Kategori Yönetimi:** "Popüler", "Yeni", "Slotlar" gibi lobi kategorilerinin düzenlenmesi.

---

## 6. Bonus ve Kampanyalar
Oyuncu teşviklerinin yönetildiği modül.
*   **Bonus Tanımları:** Hoş Geldin, Yatırma, Kayıp (Cashback) bonusları oluşturma.
*   **Kurallar:** Çevirme (wagering) gereksinimleri, maksimum kazanç, uygun oyunlar.
*   **Turnuvalar:** Liderlik tabloları ile turnuvalar oluşturma.

---

## 7. Risk ve Dolandırıcılık Yönetimi
Şüpheli aktivitelerin tespit edildiği güvenlik merkezi.
*   **Kurallar:** "Aynı IP’den 5’ten fazla hesap", "Hızlı ardışık çekim denemeleri" gibi kuralların tanımlanması.
*   **Vaka Yönetimi:** Sistem tarafından işaretlenen şüpheli oyuncuların incelendiği arayüz.
*   **Kara Liste:** Yasaklı IP, Email veya Cihaz listeleri.

---

## 8. CRM ve İletişim
Oyuncularla iletişim kurmaya yönelik modül.
*   **Segmentasyon:** "Son 30 gündür aktif değil", "VIP kullanıcılar" gibi dinamik gruplar oluşturma.
*   **Kampanyalar:** Email, SMS veya Push bildirim kampanyaları oluşturma ve zamanlama.
*   **Şablonlar:** Hazır mesaj şablonlarının yönetimi.

---

## 9. İçerik Yönetimi (CMS)
Web sitesi içeriğinin yönetildiği alan.
*   **Sayfalar:** "Hakkımızda", "SSS", "Kurallar" gibi statik sayfaların düzenlenmesi.
*   **Bannerlar:** Ana sayfa slider’ları ve promosyon görsellerinin yönetimi.
*   **Duyurular:** Site içi ticker veya pop-up duyuruları.

---

## 10. Destek Masası
Müşteri şikayet ve taleplerinin yönetildiği alan.
*   **Ticket’lar:** Email veya form üzerinden gelen talepler.
*   **Canlı Destek:** (Entegre ise) Canlı sohbet kayıtları.
*   **Hazır Yanıtlar:** Sık sorulan sorular için hızlı yanıt şablonları.

---

## 11. Affiliate Yönetimi
Trafik sağlayan iş ortaklarının yönetimi.
*   **Affiliate Listesi:** Partner hesapları ve onay süreçleri.
*   **Komisyon Planları:** CPA, RevShare (Gelir Paylaşımı) veya Hibrit modeller.
*   **Raporlar:** Hangi partnerin ne kadar trafik ve oyuncu getirdiği, kazançlar.

---

## 12. Sorumlu Oyun (RG)
Yasal uyumluluk ve oyuncu koruma modülü.
*   **Limitler:** Oyuncuların kendilerinin belirlediği yatırma/kayıp limitlerinin takibi.
*   **Kendi Kendini Dışlama:** Hesaplarını geçici/kalıcı olarak kapatan oyuncular.
*   **Uyarılar:** Riskli oyun davranışı sergileyen oyuncular için otomatik uyarılar.

---

## 13. Admin ve Güvenlik Yönetimi (YENİ)
Panel güvenliği ve admin erişimini kontrol eden gelişmiş modül.
*   **Admin Kullanıcıları:** Admin hesaplarını oluşturma, düzenleme ve dondurma.
*   **Roller ve Yetkiler:** "Finans Ekibi", "Destek Ekibi" gibi rollerin tanımlanması.
*   **Denetim Kaydı (Audit Log):** Hangi adminin ne zaman hangi işlemi yaptığını gösteren detaylı kayıt (önce/sonra değerleri ile).
*   **Yetki Matrisi:** Tüm modüllerdeki tüm rollerin yetkilerini (Okuma/Yazma/Onay/Export) tek ekranda görüntüleme ve düzenleme.
*   **IP ve Cihaz Kısıtlamaları:**
    *   **IP Whitelist:** Admin girişine yalnızca belirli IP’lerden izin verme.
    *   **Cihaz Onayı:** Yeni bir cihazdan giriş yapıldığında admin onayı gerektirme.
*   **Giriş Geçmişi:** Tüm başarılı ve başarısız admin giriş denemeleri.

---

## 14. Özellik Bayrakları ve A/B Testi (YENİ)
Yazılım özelliklerinin ve deneylerin yönetildiği teknik modül.
*   **Özellik Bayrakları:** Kod değişikliği olmadan yeni bir özelliği (örn. Yeni Ödeme Sayfası) açma/kapama veya yalnızca belirli bir kitle için etkinleştirme (örn. Beta kullanıcıları).
*   **A/B Testi (Deneyler)::** Bir özelliğin farklı versiyonlarını (Varyant A vs Varyant B) test etme ve hangisinin daha başarılı olduğunu ölçme (Dönüşüm oranı, Gelir, vb.).
*   **Segmentler:** Bayraklar için hedef kitlelerin tanımlanması (örn. "Türkiye’deki iOS kullanıcıları").
*   **Kill Switch:** Acil durumlarda tek bir butonla tüm yeni özellikleri kapatabilme.

---

## 15. Simülasyon Laboratuvarı (YENİ)
Operasyonel kararların etkisini önceden test etmek için kullanılan gelişmiş simülasyon aracı.
*   **Oyun Matematiği:** Bir slot oyununu 1 milyon kez simüle ederek gerçek RTP, Volatilite ve Maksimum Kazanç değerlerini doğrulama.
*   **Bonus Simülatörü:** Bir bonus kampanyasının kârlılığını test etme. (örn. %100 bonus verirsek, kasa ne kadar kaybeder/kazanır?)
*   **Portföy Simülatörü:** Lobide oyunların konumlarını veya RTP oranlarını değiştirmenin genel ciro üzerindeki etkisini tahmin etme.
*   **Risk Senaryoları:** Yeni bir dolandırıcılık kuralının kaç masum kullanıcıyı (False Positives) etkileyeceğini test etme.

---

## 16. Ayarlar Paneli (Multi-Tenant) (YENİ)
Genel sistem yapılandırmasının yapıldığı çok markalı yönetim merkezi.
*   **Markalar:** Yeni bir casino markası (Tenant) oluşturma, domain ve dil ayarlama.
*   **Para Birimleri:** Sistemde geçerli para birimlerini ve döviz kurlarını yönetme.
*   **Ülke Kuralları (Geoblocking)::** Hangi ülkelerden oyuncu kabul edileceğini, hangi oyunun hangi ülkede yasaklı olduğunu belirleme.
*   **API Keys:** Harici sistem entegrasyonları için güvenli API anahtarları üretme.
*   **Platform Varsayılanları:** Oturum zaman aşımı, varsayılan dil gibi sistem genelindeki ayarlar.

---
*Bu doküman Aralık 2025 geliştirme dönemi esas alınarak hazırlanmıştır.*