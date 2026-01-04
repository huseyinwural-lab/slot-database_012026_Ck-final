# Migrasyon Stratejisi (P3-DB-001)

## Karar
Staging/prod için **yalnızca ileri yönlü** migrasyonlar.

## Gerekçe
- Geri alma işlemleri zaman açısından kritiktir; güvenilir biçimde tersine çevrilebilir migrasyonları garanti etmek zordur.
- Yalnızca ileri yönlü + hotfix, kesinti süresini en aza indirir ve kısmi geri dönüş riskini azaltır.

## Operasyonel kural
- Dağıtımlar `vX.Y.Z-<gitsha>` sürümüne sabitlenir.
- Geri alma gerekiyorsa ve DB şeması önceki imajla uyumsuzsa:
  1) Uyumluluğu geri kazandıran **ileri yönlü bir hotfix** sürümünü tercih edin.
  2) Hızlıca mümkün değilse, DB’yi yedekten bilinen son iyi noktaya geri yükleyin (bkz. yedek dokümanları).

## Kontrol listesi
- Dağıtımdan önce: `/api/ready` doğrulayın ve migrasyon penceresini planlayın.
- Dağıtımdan sonra: `/api/version`, `event=service.boot` ve smoke testlerini doğrulayın.