# Nihai Canlıya Geçiş Sonrası Program Sırası (90 Gün)

**Hedef:** Üretim stabilitesini korumak, finansal akışların doğrulanabilirliğini artırmak, güvenlik ve uyumluluğu güçlendirmek, operasyonel maliyetleri azaltmak ve gelir üreten ürün fonksiyonlarını ölçeklemek.

---

## A) GÜVENİLİRLİK İZİ (SRE / Ops)

### 0–14 Gün (P0)
1.  **SLO/SLI Tanımı ve Gösterge Paneli Entegrasyonu**
    *   Metrikler: API kullanılabilirliği, p95 gecikme, webhook başarı oranı, payout SLA.
    *   Hedef: Otomatik haftalık rapor üretimi.
2.  **Olay Yönetimi Standardı**
    *   Şiddet seviyelerini, eskalasyon rotalarını, postmortem şablonlarını tanımlayın.
    *   "1 sayfalık" olay playbook'u oluşturun.
3.  **Cron/Zamanlayıcı Standardizasyonu**
    *   `detect_stuck_finance_jobs.py` ve `daily_reconciliation_report.py` için:
        *   Zamanlama (cron/systemd/k8s cronjob).
        *   Log saklama politikaları.
        *   Hata uyarı mekanizması.

### 15–90 Gün (P1)
*   **Otomatik Kapasite Raporlaması:** DB pool kullanımı, CPU, kuyruk birikimi trendleri.
*   **Chaos-Lite Testleri:** Prod benzeri bir ortamda webhook çoğaltma/başarısızlık senaryolarının periyodik testi.

---

## B) GÜVENLİK & UYUMLULUK İZİ

### 0–14 Gün (P0)
1.  **Muafiyet Kaydı Kapatma Planı**
    *   Eksik/test secret'lar için:
        *   Rota: Tedarik/Rotasyon.
        *   Sahip + Son Tarih.
    *   "Muafiyet Açık" SLA: Maksimum 30 gün.
2.  **Secret Yönetimi**
    *   Merkezi yönetim (Vault/SSM/K8s secrets).
    *   Rotasyon prosedürleri + Denetim logları.
3.  **Erişim Kontrolü Gözden Geçirmesi**
    *   Prod admin erişimi: En az ayrıcalık, MFA, loglanan erişim.

### 15–90 Gün (P1)
*   **OWASP ASVS Lite Kontrol Listesi:** + Yılda 2 penetrasyon testi planı.
*   **PCI Yaklaşımı:** Boşluk analizi (kart/PSP kapsamı genişlerse).

---

## C) FİNANS / MUTABAKAT OLGUNLUK İZİ

### 0–14 Gün (P0)
1.  **Aksiyon Alınabilir Mutabakat Çıktıları**
    *   `daily_reconciliation_report.py` dosyasını iyileştirin:
        *   Risk sınıflandırması (LOW/MED/HIGH).
        *   Aksiyon önerileri (yeniden dene, manuel inceleme, eskale et).
    *   Sonuç: Ops ekibi rapora dayanarak işleri kapatabilir.
2.  **Manuel Override Prosedürü**
    *   Takılmış payout/withdraw durumları için:
        *   Kim onaylar?
        *   Hangi kayıtlar tutulur?
        *   Hangi loglar eklenir?

### 15–90 Gün (P1)
*   **Haftalık "Defter vs Cüzdan" Mutabakatı:** Tam tarama.
*   **Settlement Raporlaması:** PSP vs Internal fark analizi.

---

## D) ÜRÜN & BÜYÜME İZİ

### 0–14 Gün (P0)
1.  **Gerçek Kullanıcı Akışı Metrikleri**
    *   Onboarding hunisi.
    *   Deposit dönüşümü.
    *   Withdrawal tamamlanma süresi.
2.  **Ops UI İyileştirmeleri**
    *   Payout/Withdraw kuyruk ekranları:
        *   Hızlı filtreler.
        *   Takılmış rozetleri.
        *   "Retry-safe" aksiyon butonları (yalnızca idempotent).

### 15–90 Gün (P1)
*   **A/B Test Altyapısı:** Basit feature flag'ler.
*   **Kampanya/Bonus Motoru İyileştirmeleri:** Gelir odaklı.

---

## Yönetim Modeli (Haftalık Ritim)
*   **Haftalık (30 dk):** Ops sağlık değerlendirmesi (SLO + olaylar + mutabakat riskleri).
*   **İki Haftada Bir:** Güvenlik değerlendirmesi (muafiyet + erişim).
*   **Aylık:** Ürün KPI değerlendirmesi (dönüşüm + elde tutma).

---

## Acil Aksiyon Seti (İlk 2 Hafta)
1.  [ ] SLO/SLI'ları tanımlayın ve gösterge paneline ekleyin.
2.  [ ] Script'leri cron'a bağlayın + hata uyarıları ekleyin.
3.  [ ] Muafiyet Kaydı'ndaki secret'lar için rotasyon/tamamlama ticket'ları açın.
4.  [ ] Mutabakat Raporu'nu risk sınıfları ve aksiyon önerileriyle güncelleyin.
5.  [ ] Manuel Override Prosedürü'nü yazın ve runbook'a ekleyin.
6.  [ ] Ops kuyruğu için "stuck badge" + filtreler backlog kalemlerini planlayın.