# Ledger Enforce Rollback Tetikleyicileri ve Karar Matrisi

Bu doküman, `ledger_enforce_balance` ve `webhook_signature_enforced` rollout'u
sırasında hangi sinyallerin rollback veya ek aksiyon gerektirdiğini özetler.

## 1. Tetikleyiciler

| ID  | Sinyal                                      | Açıklama                                             |
|-----|---------------------------------------------|------------------------------------------------------|
| T1  | 400 INSUFFICIENT_FUNDS artışı              | Normalden yüksek, beklenmeyen funds hataları         |
| T2  | Webhook 401 (WEBHOOK_SIGNATURE_INVALID)    | İmza hatalarında spike                               |
| T3  | ledger_balance_mismatch spike              | Player vs WalletBalance farklarında ani artış        |

## 2. Karar Matrisi

Aşağıdaki tablo, her tetikleyici için önerilen aksiyonları özetler.

| Tetikleyici | Şiddet seviyesi          | Önerilen aksiyonlar                                                                 |
|-------------|--------------------------|--------------------------------------------------------------------------------------|
| T1          | Hafif artış              | İzle, log'ları incele; belirli tenant/oyuncu bazlı mı bak.                         |
| T1          | Sürekli/yüksek artış    | Enforce rollback düşün; OPS-01 backfill'i tenant scoped tekrar et; iş kurallarını gözden geçir. |
| T2          | Hafif artış              | Secrets/env kontrolü yap; signature entegrasyonunda konfig hatası var mı bak.      |
| T2          | Sürekli/yüksek artış    | `WEBHOOK_SIGNATURE_ENFORCED=False` ile geçici rollback; PSP ile secret rotasyonu planla. |
| T3          | Hafif artış              | Backfill dry-run tekrar; belirli tenant'larda WB ile Player farkını analiz et.     |
| T3          | Sürekli/yüksek artış    | Enforce rollout'u durdur; backfill stratejisini gözden geçir; ops/engineering incelemesi başlat. |

## 3. Örnek Aksiyon Akışları

### 3.1 T1 (400 INSUFFICIENT_FUNDS) spike

1. Log'ları inceleyin:
   - Hangi tenant'lar / oyuncular etkileniyor?
   - Funds gerçekten yetersiz mi, yoksa backfill hatası mı?
2. Gerekirse ilgili tenant için backfill'i tekrar koşun:

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --tenant-id <tenant_uuid> \
  --batch-size 1000 \
  --dry-run
```

3. Sorun yaygınsa:
   - `ledger_enforce_balance=False` ile geçici rollback yapın.

### 3.2 T2 (Webhook 401) spike

1. HTTP log'larından 401 hata oranını ve error mesajlarını kontrol edin.
2. `webhook_secret_*` env değerlerinin doğru olduğundan emin olun.
3. Sorun geniş kapsamlıysa:

```bash
WEBHOOK_SIGNATURE_ENFORCED=False
```

4. PSP ile secret rotasyonu ve test ortamında doğrulama sonrası enforce'i yeniden açın.

### 3.3 T3 (ledger_balance_mismatch) spike

1. Mismatch telemetrisini tenant/oyuncu bazlı breakdown ile inceleyin.
2. Belirli tenant'larda Player vs WalletBalance farkını manuel/raporla analiz edin.
3. Gerekirse:
   - İlgili tenant için backfill'i force ile yeniden çalıştırın (önce dry-run).
   - Enforce rollout'unu durdurun, root cause analizi tamamlanana kadar yeni tenant'larda açmayın.

## 4. Özet

- **İzle**: Hafif ve kısa süreli spike'larda, öncelikle log/metric analizi yapın.
- **Tekrar backfill**: Belirli tenant/oyuncu sorunları için hedefli backfill kullanın.
- **Enforce kapat**: Yaygın ve kalıcı sorunlarda `ledger_enforce_balance` ve/veya
  `webhook_signature_enforced` flag'lerini rollback ederek sistemi güvenli moda alın.
