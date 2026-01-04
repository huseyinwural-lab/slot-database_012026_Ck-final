# Geri Alma Çalıştırma Kılavuzu (P3-REL-004)

## Amaç
Uygulamayı ~15 dakika içinde **daha önce bilinen iyi bir imaj etiketine** geri almak.

## Varsayımlar
- Dağıtımlar etiketlere sabitlenmiştir: `vX.Y.Z-<gitsha>` (`latest` yok).
- VT geçiş stratejisi ayrı olarak belgelenmiştir (bkz. `docs/ops/migrations.md`).

## Compose ile geri alma (örnek)
1) Önceki etiketi belirleyin (örnek): `v1.3.9-7ac0f2b`
2) Compose'u önceki etiketi kullanacak şekilde güncelleyin:```yaml
services:
  backend:
    image: registry.example.com/casino/backend:v1.3.9-7ac0f2b
  frontend-admin:
    image: registry.example.com/casino/frontend-admin:v1.3.9-7ac0f2b
  frontend-player:
    image: registry.example.com/casino/frontend-player:v1.3.9-7ac0f2b
```3) Yeniden dağıtın:```bash
docker compose -f docker-compose.prod.yml up -d
```4) Doğrulayın:
- `curl -fsS http://127.0.0.1:8001/api/ready`
- `curl -fsS http://127.0.0.1:8001/api/version`
- `event=service.boot` için açılış günlüklerini kontrol edin

## Kubernetes geri alma (kısa örnek)
Seçenek A: Rollout undo```bash
kubectl rollout undo deploy/backend
```Seçenek B: Önceki imaj etiketine sabitleyin```bash
kubectl set image deploy/backend backend=registry.example.com/casino/backend:v1.3.9-7ac0f2b
kubectl rollout status deploy/backend
```## Yapılandırma/env uyumluluğu notları
- Yeni sürüm **zorunlu** env değişkenleri getirdiyse, eski sürümün bunlara hâlâ sahip olduğundan emin olun (ya da bunları kaldırın/geri alın).
- Geçişler yalnızca ileri yönlüyse, VT geri alma yedekten geri yükleme gerektirebilir.