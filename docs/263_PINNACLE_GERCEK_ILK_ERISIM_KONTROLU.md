# Pinnacle ücretsiz API — İlk canlı erişim denemesi

6 Kasım 2026. Kullanıcı GitHub Actions'a kendi ücretsiz API anahtarını THE_ODDS_API_KEY adıyla eklediğini bildirdi.

İlk test yalnız 3 lig ENG1/GER1/TUR1 ve yalnız h2h (MS 1/X/2) sorgular. Her istek ligdeki bütün ertesi gün maçlarını döndürebilir; en fazla 3 kredi tüketebilir (boş yanıt sıfır kredi de olabilir). İlk eksiksiz ve geçerli Pinnacle 1X2 fiyatı görüldüğünde kalan ligler sorgulanmadan durulur. 401/403/429 ilk olayda durulur. Oranlar S1/S2, bahis veya modellerde kullanılmaz; mühürlü dosyalar değiştirilmez.

Önceki tek seferlik workflow dosyasında bozulmuş içerik tespit edilip tamamen temiz içerikle değiştirildi. Yeni istek şeması: {"schema":"263_pinnacle_once_request_v1","day_turkey":"2026-11-07"}. Otomatik zamanlayıcı yok; yalnız tek yeni dosyanın GitHub push tetiklemesiyle bir kere çalışır.

Anahtar/hesap kullanım hakkı dışarı sızdırılmaz. Başarı için gerçek kaynaktan tam ve son 30 dakika içinde güncellenmiş 1X2 fiyatı gerekir. Önceki sentetik testler canlı fiyat kanıtı değildir. GitHub Actions artifact çıktısından gerçek kanıt incelenmelidir.
