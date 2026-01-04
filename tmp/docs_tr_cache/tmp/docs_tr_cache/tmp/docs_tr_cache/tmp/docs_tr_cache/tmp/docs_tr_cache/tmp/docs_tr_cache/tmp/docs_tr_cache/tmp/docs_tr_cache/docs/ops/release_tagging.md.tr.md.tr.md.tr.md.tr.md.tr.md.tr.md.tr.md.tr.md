# Sürüm Etiketleme Standardı (P3-REL-001)

## Amaç
- Deterministik dağıtımlar için Docker imaj etiketlerini standartlaştırmak.
- Staging/prod ortamlarında **`latest` kullanmayın**.

## Etiket formatı
Kullanın:```
vX.Y.Z-<gitsha>
```Örnekler:
- `v1.4.0-8f2c1ab`
- `v0.3.2-a1b2c3d`

Notlar:
- `gitsha`, commit SHA’sının **kısa** hali olmalıdır (7–12 karakter).
- Sürüm, repo kök dizinindeki `VERSION` içinde saklanır.

## Compose dağıtımı (örnek)
Build almak veya `latest` kullanmak yerine, imajları sabitleyin:```yaml
services:
  backend:
    image: registry.example.com/casino/backend:v1.4.0-8f2c1ab
  frontend-admin:
    image: registry.example.com/casino/frontend-admin:v1.4.0-8f2c1ab
  frontend-player:
    image: registry.example.com/casino/frontend-player:v1.4.0-8f2c1ab
```## Kubernetes dağıtımı (kısa örnek)
Deployment’ınızda imaj etiketini sabitleyin:```yaml
spec:
  template:
    spec:
      containers:
        - name: backend
          image: registry.example.com/casino/backend:v1.4.0-8f2c1ab
```## Çalışan sürümü doğrulama
- Backend: `GET /api/version`
- Backend logları: `event=service.boot` içinde `version`, `git_sha`, `build_time` yer alır
- Admin UI: Ayarlar → Hakkında/Sürüm kartı `version` ve `git_sha` değerlerini gösterir

## Politika
- ✅ İzin verilen: sabitlenmiş sürüm etiketleri `vX.Y.Z-<gitsha>`
- ❌ Staging/prod ortamlarında yasak: `latest`, sabitlenmemiş etiketler