# Sık Hatalar (TR)

Bu rehber, birden fazla admin menüsünde tekrar eden **platform-geneli** hataları standardize eder.

**Kapsam sınırı:**
- Bu dosya, operatörün ilk müdahale playbook’una ihtiyaç duyduğu tekrar eden (cross-menu) hataları içerir.
- Menüye özel ince detaylar ilgili menü sayfasında kalır; burada sadece ortak hata tipi ve hızlı müdahale vardır.

---

## 1) Admin login — Network Error

- **Belirtiler (UI):** Login spinner; “Network Error”; token oluşmuyor.
- **Muhtemel Nedenler:**
  - backend base URL yanlış
  - ingress’te `/api` routing uyumsuz
  - CORS blok
  - TLS / mixed-content blok
  - auth endpoint 5xx
- **Çözüm Adımları:**
  1) Frontend’in `REACT_APP_BACKEND_URL` kullandığını ve `/api/*` çağırdığını doğrula.
  2) DevTools → Network’te fail eden request’i ve status’u kaydet.
  3) Request URL’in environment ile uyumlu olduğunu doğrula (preview/stage/prod).
  4) Backend health/version: `GET /api/v1/version`.
  5) CORS/mixed-content ise origin/TLS konfigünü düzelt.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: Login başarılı, redirect olur; token kaydedilir.
  - Logs: backend `/api/auth/login` 200.
  - Audit Log: (opsiyonel) login event’i varsa görünür.
  - DB: user mevcut ve aktif.
- **Escalation Paketi:**
  - `POST /api/auth/login` → status + response body
  - Console error + network HAR snippet
  - Log keywords: `CORS`, `origin`, `auth`, `login`, `request_id`
- **İlgili Sayfalar:**
  - `/docs/new/tr/runbooks/break-glass.md`
  - `/docs/new/tr/runbooks/password-reset.md`

---

## 2) 401 Unauthorized (token missing/expired)

- **Belirtiler (UI):** Login’e düşer; “Unauthorized”; API 401.
- **Muhtemel Nedenler:**
  - token yok
  - token süresi doldu
  - Authorization header gitmiyor
  - clock skew
- **Çözüm Adımları:**
  1) Tekrar login ol ve reproduce et.
  2) `Authorization: Bearer <token>` var mı bak.
  3) Storage’ı temizle; tekrar login.
  4) Backend token TTL ve saat senkronunu kontrol et.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: redirect yok.
  - Logs: re-auth sonrası 200.
  - Audit Log: (opsiyonel) auth failure loglanır.
  - DB: admin user aktif.
- **Escalation Paketi:**
  - failing endpoint + 401
  - Log keywords: `jwt`, `expired`, `authorization`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/system/admin-users.md`

---

## 3) 403 Forbidden (role/scope/tenant context)

- **Belirtiler (UI):** “Forbidden”; menü gizli; aksiyon blok.
- **Muhtemel Nedenler:**
  - rol yetkisi eksik
  - feature/capability enabled değil
  - owner-only enforcement
  - tenant context yanlış
- **Çözüm Adımları:**
  1) Hangi rolle login olunduğunu doğrula.
  2) Menünün owner-only/feature-gated olup olmadığını kontrol et.
  3) Platform owner ile doğrulama yap.
  4) Tenant context header/selection doğrula.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: doğru rolle erişim olur.
  - Logs: owner ile aynı endpoint 200.
  - Audit Log: permission değişimleri (varsa).
  - DB: role/capability set.
- **Escalation Paketi:**
  - endpoint + 403
  - Log keywords: `permission`, `forbidden`, `ownerOnly`, `tenant_id`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/roles-permissions.md`

---

## 4) 404 Not Found (UI → Backend route gap)

- **Belirtiler (UI):** Tab boş; “Not found”; Network 404.
- **Muhtemel Nedenler:**
  - backend route yok
  - `/api` prefix eksik
  - version mismatch (`/v1` vs `/v2`)
- **Çözüm Adımları:**
  1) DevTools’ta fail eden path’i aynen kaydet.
  2) Backend routes içinde path’i ara.
  3) Ingress’in `/api` prefix istediğini doğrula.
  4) Backend gap register’a ekle.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: tab açılır.
  - Logs: route 200.
  - Audit Log: (mutation ise) event var.
  - DB: data var.
- **Escalation Paketi:**
  - method/path + 404
  - Log keywords: `404`, `Not Found`
- **İlgili Sayfalar:**
  - `/docs/new/tr/runbooks/backend-gap-register.md`

---

## 5) 422 Validation failed (form/import)

- **Belirtiler (UI):** Submit fail; API 422.
- **Muhtemel Nedenler:**
  - schema mismatch (field/type)
  - required field eksik
  - enum value yanlış
- **Çözüm Adımları:**
  1) 422 body detail’i incele.
  2) UI payload ile backend schema’yı karşılaştır.
  3) field/type hizala.
  4) eksik UI validation ekle.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: submit success.
  - Logs: 200/201.
  - Audit Log: mutation event.
  - DB: record oluşur.
- **Escalation Paketi:**
  - method/path + 422 + response detail
  - Log keywords: `validation`, `pydantic`, `422`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/system/api-keys.md`

---

## 6) 500 Internal Server Error

- **Belirtiler (UI):** generic error; API 500.
- **Muhtemel Nedenler:**
  - unhandled exception
  - DB connection sorunu
  - None/null handling bug
  - serialization hatası
- **Çözüm Adımları:**
  1) request_id al.
  2) backend log’da stack trace bul.
  3) route + payload tespit et.
  4) fix + test.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: aksiyon success.
  - Logs: exception yok; 200.
  - Audit Log: success event.
  - DB: state tutarlı.
- **Escalation Paketi:**
  - method/path + request_id
  - Log keywords: `Traceback`, `Exception`, `request_id`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/system/logs.md`

---

## 7) Timeout / Gateway timeout (upstream/provider)

- **Belirtiler (UI):** spinner uzun; 504/timeout.
- **Muhtemel Nedenler:**
  - upstream provider yavaş
  - uzun sorgu
  - job/worker blok
- **Çözüm Adımları:**
  1) daha dar filtre/zaman aralığı ile dene.
  2) backend log’da slow query ara.
  3) provider status kontrol.
  4) uygun timeout/retry uygula.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: SLA içinde döner.
  - Logs: latency düşer.
  - Audit Log: (mutation ise) event var.
  - DB: partial write yok.
- **Escalation Paketi:**
  - method/path + süre + status
  - Log keywords: `timeout`, `gateway`, `latency`
- **İlgili Sayfalar:**
  - `/docs/new/tr/guides/performance-guardrails.md`

---

## 8) CORS / mixed content

- **Belirtiler (UI):** Console CORS; request blocked.
- **Muhtemel Nedenler:**
  - backend CORS origins eksik
  - http/https mismatch
- **Çözüm Adımları:**
  1) frontend HTTPS mi doğrula.
  2) backend URL HTTPS mi.
  3) backend CORS origins ekle.
  4) re-deploy + test.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: request success.
  - Logs: backend’e hit.
  - Audit Log: n/a.
  - DB: n/a.
- **Escalation Paketi:**
  - console error
  - failing URL
  - Log keywords: `CORS`, `origin`, `blocked`
- **İlgili Sayfalar:**
  - `/docs/new/tr/guides/deployment.md`

---

## 9) Stale cache / propagation delay (visibility/flags/games)

---

## 10) Export CSV no-op (request yok / download yok)

- **Belirtiler (UI):** “Export CSV” tıklanır, hiçbir şey olmaz; download başlamaz.
- **Muhtemel Nedenler:**
  - FE: butonda `onClick` yok veya handler hata alıp sessizce yutuluyor
  - FE: `responseType: 'blob'` yok; tarayıcı download tetikleyemiyor
  - BE: export endpoint yok (404) veya path yanlış (`/v1` vs `/api/v1`)
- **Çözüm Adımları:**
  1) DevTools → Network (All) + “Preserve log”: export’a tıkla.
     - **Request yoksa**: FE handler bağlama sorunu.
     - Request **404/5xx** ise: backend route gap.
  2) FE: export çağrısını `responseType: 'blob'` ile yap; `URL.createObjectURL(blob)` + `<a download>` ile indirmeyi tetikle.
  3) BE: `Content-Type: text/csv; charset=utf-8` ve `Content-Disposition: attachment; filename="..."` döndür.
- **Doğrulama:**
  - Network’te export endpoint 200.
  - Tarayıcı `.csv` dosyasını indirir.

- **Belirtiler (UI):** save oldu ama UI eski; görünürlük güncellenmez.
- **Muhtemel Nedenler:**
  - cache TTL
  - async pipeline gecikmesi
  - servisler arası propagation
- **Çözüm Adımları:**
  1) hard refresh.
  2) endpoint re-fetch.
  3) cache invalidation kontrol.
  4) Logs ile doğrula.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: yeni state görünür.
  - Logs: invalidation log.
  - Audit Log: change event.
  - DB: record update.
- **Escalation Paketi:**
  - method/path + timestamp
  - Log keywords: `cache`, `invalidate`, `ttl`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/system/feature-flags.md`

---

## 10) Feature flag no-op / not persisted

- **Belirtiler (UI):** toggle OK ama refresh sonrası geri döner.
- **Muhtemel Nedenler:**
  - safe stub backend
  - persistence yok
  - tenant scope mismatch
- **Çözüm Adımları:**
  1) toggle + refresh.
  2) GET vs POST davranışı kontrol.
  3) backend implementasyonuna bak.
  4) persistence gap olarak escalate.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: toggle kalıcı.
  - Logs: state save.
  - Audit Log: event var.
  - DB: flag update.
- **Escalation Paketi:**
  - `/api/v1/flags/*`
  - Log keywords: `flags`, `toggle`, `persist`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/system/feature-flags.md`

---

## 11) Tenant context mismatch (wrong tenant ops)

- **Belirtiler (UI):** değişiklik yanlış tenant’ta; listeler boş.
- **Muhtemel Nedenler:**
  - yanlış tenant seçili
  - tenant header yok
  - query’lerde tenant_id uygulanmıyor
- **Çözüm Adımları:**
  1) seçili tenant’ı doğrula.
  2) Network’te tenant header var mı.
  3) backend query filter kontrol.
  4) retest.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: doğru tenant data.
  - Logs: tenant_id eşleşir.
  - Audit Log: tenant_id doğru.
  - DB: scope doğru.
- **Escalation Paketi:**
  - method/path + tenant_id
  - Log keywords: `tenant_id`, `scope`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/system/tenants.md`

---

## 12) Pagination/filter mismatch (empty list but exists)

- **Belirtiler (UI):** UI boş; DB’de veri var.
- **Muhtemel Nedenler:**
  - backend query param’ları ignore
  - yanlış default filter
  - pagination off-by-one
- **Çözüm Adımları:**
  1) filter kaldırıp dene.
  2) request query param kontrol.
  3) backend param handling doğrula.
  4) pagination fix.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: liste dolar.
  - Logs: param handling.
  - Audit Log: n/a.
  - DB: n/a.
- **Escalation Paketi:**
  - request URL + params
  - Log keywords: `page`, `limit`, `filter`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/system/reports.md`

---

## 13) Import job stuck / job status not updating

- **Belirtiler (UI):** import sürekli in-progress; status güncellenmez.
- **Muhtemel Nedenler:**
  - worker çalışmıyor
  - job state persist edilmiyor
  - polling endpoint yok
- **Çözüm Adımları:**
  1) job_id al.
  2) job status endpoint kontrol.
  3) worker/queue doğrula.
  4) gerekiyorsa worker restart.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: done/failed’e geçer.
  - Logs: job işlendi.
  - Audit Log: import event.
  - DB: job row update.
- **Escalation Paketi:**
  - method/path + job_id
  - Log keywords: `import`, `job`, `worker`, `queue`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/core/games.md`

---

## 14) Report empty / timezone mismatch

- **Belirtiler (UI):** report 0; finance veri bekler.
- **Muhtemel Nedenler:**
  - timezone mismatch
  - date window yanlış
  - aggregation delay
- **Çözüm Adımları:**
  1) timezone beklentisini doğrula.
  2) date window genişlet.
  3) raw transaction ile karşılaştır.
  4) timezone normalization fix.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: sayılar tutarlı.
  - Logs: aggregation job çalıştı.
  - Audit Log: export event.
  - DB: transaction var.
- **Escalation Paketi:**
  - report query + timezone
  - Log keywords: `timezone`, `aggregation`, `report`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/system/reports.md`

---

## 15) Withdrawals stuck / approval queue backlog

- **Belirtiler (UI):** withdrawals pending; kuyruk büyür.
- **Muhtemel Nedenler:**
  - approval workflow işlemiyor
  - payout provider sorunu
  - risk hold
- **Çözüm Adımları:**
  1) Approval Queue kontrol.
  2) payout provider status.
  3) Logs’ta payout error.
  4) abuse dalgasında Kill Switch.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: withdrawal status değişir.
  - Logs: payout success.
  - Audit Log: approval kaydı.
  - DB: withdrawal status update.
- **Escalation Paketi:**
  - withdrawal_id + endpoint
  - Log keywords: `withdrawal`, `payout`, `provider`, `approval`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/core/withdrawals.md`
  - `/docs/new/tr/admin/risk-compliance/approval-queue.md`

---

## 16) KYC document processing issues (unreadable/duplicate)

- **Belirtiler (UI):** doküman açılmaz; duplicate; review fail.
- **Muhtemel Nedenler:**
  - bozuk upload
  - duplicate doc id
  - OCR/extraction fail
- **Çözüm Adımları:**
  1) re-upload iste.
  2) storage link kontrol.
  3) hash ile dedupe.
  4) processing tekrar çalıştır.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: doküman render.
  - Logs: processing success.
  - Audit Log: review recorded.
  - DB: doc row tutarlı.
- **Escalation Paketi:**
  - doc_id + endpoint
  - Log keywords: `kyc`, `document`, `ocr`, `duplicate`
- **İlgili Sayfalar:**
  - `/docs/new/tr/admin/operations/kyc-verification.md`

---

## 17) Lockfile / yarn drift (CI)

- **Belirtiler (UI/CI):** preview deploy blok; CI lint/install fail.
- **Muhtemel Nedenler:**
  - branch’ler arası yarn.lock drift
  - dependency version mismatch
- **Çözüm Adımları:**
  1) yarn kullan (npm değil).
  2) lockfile commit edildi mi kontrol.
  3) CI yeniden çalıştır.
  4) gerekiyorsa lockfile’ı tutarlı yeniden üret.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: preview deploy success.
  - Logs: CI yeşil.
  - Audit Log: n/a.
  - DB: n/a.
- **Escalation Paketi:**
  - CI job link + error log
  - keywords: `yarn.lock`, `install`, `eslint`
- **İlgili Sayfalar:**
  - `/docs/new/tr/guides/deployment.md`

---

## 18) Migrations / head mismatch

- **Belirtiler (UI/API):** deploy sonrası 500; migration fail.
- **Muhtemel Nedenler:**
  - migration eksik
  - head revision yanlış
  - environment drift
- **Çözüm Adımları:**
  1) migration status kontrol.
  2) current head tespit.
  3) eksik migration uygula.
  4) re-deploy.
- **Doğrulama (UI + Logs + Audit + DB):**
  - UI: endpoint’ler toparlar.
  - Logs: migration apply.
  - Audit Log: n/a.
  - DB: schema head ile uyumlu.
- **Escalation Paketi:**
  - migration tool output
  - keywords: `alembic`, `head`, `revision`, `migration`
- **İlgili Sayfalar:**
  - `/docs/new/tr/guides/migrations.md`
