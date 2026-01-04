# Operasyonel Sözlük

## Finansal Terimler

### Defter Durumları
*   **Kullanılabilir Bakiye:** Kullanıcının bahis yapabileceği veya çekebileceği fonlar.
*   **Bloke Bakiye:** Bekleyen para çekme işlemleri için kilitlenen fonlar. Bahis için kullanılamaz.
*   **Defter Yakımı:** Sağlayıcı tarafından bir ödeme `Paid` olarak doğrulandığında `Held Balance` içinden fonların nihai olarak kaldırılması.
*   **Mutabakat:** Bir PSP işlem sonucunun, bizim dahili Defter durumumuzla eşleştirilmesi süreci.

### İşlem Durumları
*   **Oluşturuldu:** İlk kayıt (Yatırma).
*   **Sağlayıcı Bekleniyor:** Kullanıcı PSP’ye yönlendirildi, webhook/geri dönüş bekleniyor.
*   **Talep Edildi:** Kullanıcı para çekme talep etti, fonlar Bloke.
*   **Onaylandı:** Para çekme Admin tarafından onaylandı, Ödeme için hazır.
*   **Ödeme Gönderildi:** Ödeme talebi PSP’ye (örn. Adyen) gönderildi, sonuç bekleniyor.
*   **Ödendi:** PSP başarıyı doğruladı. Fonlar Defter’den "Yakılır".
*   **Ödeme Başarısız:** PSP reddetti/başarısız oldu. Admin işlemi (Yeniden Dene/Reddet) yapılana kadar fonlar Bloke kalır.

## Teknik Terimler

### İdempotans
Bir işlemin (örn. Webhook, Ödeme Yeniden Deneme) sonucu, ilk uygulamanın ötesinde değiştirmeden birden fazla kez uygulanabilmesi özelliği. Çifte harcamayı önlemek için kritiktir.

### Webhook İmzası
PSP (Stripe/Adyen) tarafından header’larda gönderilen kriptografik bir hash. Payload’un hash’ini bizim Secret’ımızı kullanarak hesaplarız. Eşleşirse istek otentiktir. **Prod’da bunu asla atlamayın.**

### Canary
Dağıtımdan hemen sonra, tüm kullanıcılara trafiği açmadan önce "Para Döngüsü"nün çalıştığını doğrulamak için yürütülen belirli bir test kullanıcı/işlem akışı.

### Smoke Test
Servisin çalıştığını doğrulamak için hızlı, tahribatsız bir kontrol seti (Health, Login, Config). Tam iş mantığını doğrulamaz (bunun için Canary vardır).