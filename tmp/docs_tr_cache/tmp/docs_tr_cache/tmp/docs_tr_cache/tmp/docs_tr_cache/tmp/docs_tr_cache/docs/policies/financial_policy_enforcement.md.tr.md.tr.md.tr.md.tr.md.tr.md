# Finansal Politika Uygulaması

## Para Çekme Yeniden Deneme Politikası (TENANT-POLICY-002)

PSP’lere spam yapılmasını önlemek ve riski azaltmak için sistem, aşağıdaki endpoint üzerinden para çekme yeniden deneme girişimlerine limitler uygular:
`POST /api/v1/finance-actions/withdrawals/{tx_id}/retry`

### Hata Kodları

| Hata Kodu | HTTP Durumu | Mesaj | Nerede | Düzeltme |
| :--- | :--- | :--- | :--- | :--- |
| `LIMIT_EXCEEDED` | 400 | İşlem limiti aşıldı | `/api/v1/payments/*` | İşlem tutarını azaltın veya limitleri artırmak için destek ile iletişime geçin. |
| `TENANT_PAYOUT_RETRY_LIMIT_EXCEEDED` | 422 | Maksimum ödeme yeniden deneme sayısı aşıldı | `/api/v1/finance-actions/withdrawals/{tx_id}/retry` | Otomatik yeniden denemeyin. Başarısızlık nedenini araştırın veya yeni bir para çekme işlemi oluşturun. |
| `TENANT_PAYOUT_COOLDOWN_ACTIVE` | 429 | Ödeme bekleme süresi aktif | `/api/v1/finance-actions/withdrawals/{tx_id}/retry` | Yeniden denemeden önce bekleme süresinin (varsayılan 60 sn) dolmasını bekleyin. |
| `IDEMPOTENCY_KEY_REQUIRED` | 400 | Idempotency-Key başlığı eksik | Kritik finansal aksiyonlar | İsteğe `Idempotency-Key: <uuid>` başlığını ekleyin. |
| `IDEMPOTENCY_KEY_REUSE_CONFLICT` | 409 | Idempotency Key farklı parametrelerle yeniden kullanıldı | Kritik finansal aksiyonlar | Yeni istek için yeni bir anahtar üretin veya aynı anahtar için aynı parametrelerle yeniden deneyin. |
| `ILLEGAL_TRANSACTION_STATE_TRANSITION` | 400 | Geçersiz durum geçişi | İşlem Durumu Durum Makinesi | Aksiyonu denemeden önce mevcut işlem durumunu doğrulayın. |

### Denetim Olayları

Engelleyici olaylar, aşağıdaki aksiyon ile denetim izine kaydedilir:
-   **`FIN_PAYOUT_RETRY_BLOCKED`**: `reason` ("limit_exceeded" veya "cooldown_active") ve mevcut sayaç/zamanlayıcı gibi ayrıntıları içerir.