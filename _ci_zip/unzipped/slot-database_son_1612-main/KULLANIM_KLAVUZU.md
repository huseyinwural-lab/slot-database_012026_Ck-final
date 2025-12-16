# Casino Yönetim Paneli - Kapsamlı Kullanım Kılavuzu

Bu belge, Casino Yönetim Paneli'nin tüm modüllerini ve özelliklerini detaylı bir şekilde açıklayan kapsamlı bir rehberdir.

## İçindekiler
1. [Giriş ve Genel Bakış](#1-giriş-ve-genel-bakış)
2. [Dashboard (Kontrol Paneli)](#2-dashboard-kontrol-paneli)
3. [Oyuncu Yönetimi](#3-oyuncu-yönetimi)
4. [Finans Yönetimi](#4-finans-yönetimi)
5. [Oyun Yönetimi](#5-oyun-yönetimi)
6. [Bonus ve Kampanyalar](#6-bonus-ve-kampanyalar)
7. [Risk ve Sahtecilik Yönetimi](#7-risk-ve-sahtecilik-yönetimi)
8. [CRM ve İletişim](#8-crm-ve-iletişim)
9. [İçerik Yönetimi (CMS)](#9-içerik-yönetimi-cms)
10. [Destek Masası](#10-destek-masası)
11. [Affiliate (Ortaklık) Yönetimi](#11-affiliate-ortaklık-yönetimi)
12. [Sorumlu Oyunculuk (RG)](#12-sorumlu-oyunculuk-rg)
13. [Yönetici ve Güvenlik Yönetimi](#13-yönetici-ve-güvenlik-yönetimi)
14. [Özellik Bayrakları ve A/B Testleri](#14-özellik-bayrakları-ve-ab-testleri)
15. [Simülasyon Laboratuvarı](#15-simülasyon-laboratuvarı)
16. [Ayarlar Paneli (Multi-Tenant)](#16-ayarlar-paneli-multi-tenant)

---

## 1. Giriş ve Genel Bakış
Bu panel, modern bir online casino operasyonunun tüm yönlerini yönetmek için tasarlanmış, çok markalı (multi-tenant) ve modüler bir yapıdır.

**Temel Özellikler:**
*   **Rol Bazlı Erişim:** Kullanıcılar sadece yetkili oldukları modülleri görebilir.
*   **Multi-Tenant:** Tek panelden birden fazla marka (Brand) yönetilebilir.
*   **Gerçek Zamanlı Veri:** Dashboard ve raporlar anlık verilerle beslenir.

---

## 2. Dashboard (Kontrol Paneli)
Giriş yaptıktan sonra karşılaşılan ana ekrandır. Operasyonun genel sağlığını gösterir.
*   **KPI Kartları:** Günlük Yatırım, Çekim, GGR (Gross Gaming Revenue), NGR (Net Gaming Revenue), Aktif Oyuncu sayısı.
*   **Grafikler:** Saatlik/Günlük gelir trendleri.
*   **Canlı Akış:** Son kayıt olan oyuncular, son büyük kazançlar, son yatırımlar.
*   **Acil Durumlar:** Bekleyen riskli çekimler veya onay bekleyen yüksek tutarlı işlemler.

---

## 3. Oyuncu Yönetimi
Oyuncuların tüm yaşam döngüsünün yönetildiği bölümdür.
*   **Oyuncu Listesi:** Gelişmiş filtreleme (ID, Email, Kullanıcı Adı, IP, Kayıt Tarihi) ile oyuncu arama.
*   **Oyuncu Profili:**
    *   **Genel:** Bakiye, sadakat puanı, VIP seviyesi.
    *   **Cüzdan:** Gerçek para ve bonus bakiyesi detayları.
    *   **Oyun Geçmişi:** Oynadığı oyunlar, bahis/kazanç detayları.
    *   **İşlem Geçmişi:** Tüm yatırım ve çekimler.
    *   **KYC:** Kimlik doğrulama belgeleri ve durumları.
    *   **Notlar:** Müşteri temsilcisi notları.

---

## 4. Finans Yönetimi
Para giriş çıkışlarının kontrol edildiği merkezdir.
*   **Yatırım Talepleri:** Bekleyen, onaylanan ve reddedilen yatırımlar. Manuel onay gerektiren yöntemler için işlem butonları.
*   **Çekim Talepleri:** Oyuncu çekim talepleri. Risk skoru yüksek işlemler otomatik olarak "İnceleme" durumuna düşer.
*   **Raporlar:** Ödeme sağlayıcı bazlı raporlar, günlük kasa raporu.

---

## 5. Oyun Yönetimi
Casino lobisinin yönetildiği alandır.
*   **Oyun Listesi:** Tüm oyunlar, sağlayıcılar, RTP oranları.
*   **Oyun Düzenleme:** Oyunun adı, kategorisi, görselleri ve aktiflik durumu.
*   **Oyun İstemcisi (Client) Yönetimi:** HTML5 ve Unity WebGL oyun istemcilerinin yüklenmesi ve güncellenmesi. Client upload ekranında girilen **launch_url** ve **min_version** alanları, ilgili `client_variants[client_type]` kaydına yazılır; daha önce manual import sırasında üretilmiş default değerler bu alanlarla override edilir.
*   **Yeni Üye Bonusları:** "Yeni Üye Manuel Bonus" kartı üzerinden, allowed_game_ids / spin_count / fixed_bet_amount / total_budget_cap / validity_days parametreleriyle yeni oyuncular için otomatik bonus kurgulayabilirsiniz. Bu bonus, kullanıcı ilk kayıt olduğunda veya ilk giriş yaptığında otomatik atanır ve aynı kullanıcıya birden fazla kez verilmez.
*   **Kategori Yönetimi:** "Popüler", "Yeni", "Slotlar" gibi lobi kategorilerini düzenleme.

---

## 6. Bonus ve Kampanyalar
Oyuncu teşviklerinin yönetildiği modüldür.
*   **Bonus Tanımlama:** Hoşgeldin, Yatırım, Kayıp (Cashback) bonusları oluşturma.
*   **Kurallar:** Çevrim şartı (Wagering), maksimum kazanç, geçerli oyunlar.
*   **Turnuvalar:** Liderlik tablolu turnuvalar oluşturma.

---

## 7. Risk ve Sahtecilik Yönetimi
Şüpheli aktivitelerin tespit edildiği güvenlik merkezidir.
*   **Kurallar:** "Aynı IP'den 5 üzeri hesap", "Hızlı ardışık çekim denemeleri" gibi kurallar tanımlama.
*   **Vaka Yönetimi (Case Management):** Sistem tarafından işaretlenen şüpheli oyuncuların incelendiği arayüz.
*   **Kara Liste:** Yasaklı IP, E-posta veya Cihaz listeleri.

---

## 8. CRM ve İletişim
Oyuncularla iletişim kurulan modüldür.
*   **Segmentasyon:** "Son 30 gün aktif olmayanlar", "VIP kullanıcılar" gibi dinamik gruplar oluşturma.
*   **Kampanyalar:** E-posta, SMS veya Push bildirim kampanyaları oluşturma ve zamanlama.
*   **Şablonlar:** Hazır mesaj şablonları yönetimi.

---

## 9. İçerik Yönetimi (CMS)
Web sitesinin içeriğinin yönetildiği alandır.
*   **Sayfalar:** "Hakkımızda", "SSS", "Kurallar" gibi statik sayfaların düzenlenmesi.
*   **Bannerlar:** Ana sayfa slider ve promosyon görsellerinin yönetimi.
*   **Duyurular:** Site içi kayan yazı veya pop-up duyurular.

---

## 10. Destek Masası
Müşteri şikayet ve taleplerinin yönetildiği alandır.
*   **Biletler (Tickets):** E-posta veya form üzerinden gelen talepler.
*   **Canlı Destek:** (Entegrasyon varsa) Canlı sohbet kayıtları.
*   **Hazır Cevaplar:** Sık sorulan sorular için hızlı cevap şablonları.

---

## 11. Affiliate (Ortaklık) Yönetimi
Trafik sağlayan iş ortaklarının yönetimi.
*   **Affiliate Listesi:** Ortakların hesapları ve onay süreçleri.
*   **Komisyon Planları:** CPA, RevShare (Gelir Paylaşımı) veya Hibrit modeller.
*   **Raporlar:** Hangi ortaktan ne kadar trafik ve oyuncu geldiği, hakedişler.

---

## 12. Sorumlu Oyunculuk (RG)
Yasal uyumluluk ve oyuncu koruma modülü.
*   **Limitler:** Oyuncuların kendilerine koyduğu yatırım/kayıp limitlerinin takibi.
*   **Kendini Dışlama (Self-Exclusion):** Hesabını süreli/süresiz kapatan oyuncular.
*   **Uyarılar:** Riskli oyun davranışı sergileyen oyuncular için otomatik uyarılar.

---

## 13. Yönetici ve Güvenlik Yönetimi (YENİ)
Panelin güvenliğini ve yönetici erişimlerini kontrol eden gelişmiş modül.
*   **Admin Kullanıcılar:** Yönetici hesapları oluşturma, düzenleme ve dondurma.
*   **Roller ve İzinler:** "Finans Ekibi", "Destek Ekibi" gibi roller tanımlama.
*   **Aktivite Logu (Audit Log):** Hangi yöneticinin ne zaman, hangi işlemi yaptığını (öncesi/sonrası değerlerle) gösteren detaylı log.
*   **İzin Matrisi:** Tüm rollerin tüm modüllerdeki yetkilerini (Okuma/Yazma/Onay/Export) tek ekranda görme ve düzenleme.
*   **IP ve Cihaz Kısıtlamaları:**
    *   **IP Whitelist:** Sadece belirli IP'lerden yönetici girişine izin verme.
    *   **Cihaz Onayı:** Yeni bir cihazdan giriş yapıldığında yönetici onayı isteme.
*   **Giriş Geçmişi:** Başarılı ve başarısız tüm yönetici giriş denemeleri.

---

## 14. Özellik Bayrakları ve A/B Testleri (YENİ)
Yazılım özelliklerinin (Feature Flags) ve deneylerin yönetildiği teknik modül.
*   **Feature Flags:** Yeni bir özelliği (örn: Yeni Ödeme Sayfası) kod değişikliği yapmadan açıp kapatma veya sadece belirli bir kitleye (örn: Beta kullanıcıları) açma.
*   **A/B Testleri (Experiments):** Bir özelliğin farklı versiyonlarını (Varyant A vs Varyant B) test etme ve hangisinin daha başarılı olduğunu (Dönüşüm oranı, Gelir vb.) ölçme.
*   **Segmentler:** Bayrakların uygulanacağı hedef kitleleri (örn: "Türkiye'deki iOS kullanıcıları") tanımlama.
*   **Kill Switch:** Acil durumlarda tüm yeni özellikleri tek tuşla kapatma yeteneği.

---

## 15. Simülasyon Laboratuvarı (YENİ)
Operasyonel kararların etkisini önceden test etmek için kullanılan gelişmiş simülasyon aracı.
*   **Oyun Matematiği (Game Math):** Bir slot oyununu 1 milyon kez simüle ederek gerçek RTP, Volatilite ve Maksimum Kazanç değerlerini doğrulama.
*   **Bonus Simülatörü:** Bir bonus kampanyasının karlılığını test etme. (Örn: %100 bonus verirsek kasa ne kadar kaybeder/kazanır?)
*   **Portföy Simülatörü:** Oyunların lobideki yerini değiştirmenin veya RTP oranlarıyla oynamanın genel ciroya etkisini tahmin etme.
*   **Risk Senaryoları:** Yeni bir sahtecilik kuralının kaç masum kullanıcıyı (False Positive) etkileyeceğini test etme.

---

## 16. Ayarlar Paneli (Multi-Tenant) (YENİ)
Sistemin genel yapılandırmasının yapıldığı çok markalı yönetim merkezi.
*   **Markalar (Brands):** Yeni bir casino markası (Tenant) oluşturma, domain ve dil ayarlarını yapma.
*   **Para Birimleri:** Sistemde geçerli para birimlerini ve kur oranlarını yönetme.
*   **Ülke Kuralları (Geoblocking):** Hangi ülkeden oyuncu kabul edileceğini, hangi oyunların hangi ülkede yasaklı olduğunu belirleme.
*   **API Anahtarları:** Dış sistem entegrasyonları için güvenli API anahtarları üretme.
*   **Platform Varsayılanları:** Oturum süreleri, varsayılan dil gibi sistem geneli ayarlar.

---
*Bu doküman 2025-12 Dönemi geliştirmeleri baz alınarak hazırlanmıştır.*
