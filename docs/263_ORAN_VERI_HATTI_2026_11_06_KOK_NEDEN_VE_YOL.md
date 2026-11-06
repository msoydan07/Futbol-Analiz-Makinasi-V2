# Makina 2.6.3 — 6 Kasım 2026 oran hattı kök neden ve erişim planı

## Gerçek gözlem (saat 19:18 Türkiye)
T−60 GitHub çalışması `42251162453` başarıyla B/C2/C3/M4 kaydını kilitledi. Aynı çalışmanın `experiments/263/api_odds_attempts/17dacc99e11d4ce6bf17d113f20715671eb12aae.json` kanıtı: `NO_ODDSPAPI_KEY_CONFIGURED`. Başarılı GitHub Actions motoru, doğrulanmış oranı otomatik oluşturdu anlamına **gelmiyor**. Güncel oran yoksa S2 `PAS` doğru.

## İkinci bağımsız kod hatası (bu değişiklikte düzeltildi)
`odds_provider_oddspapi_263.py`, gerçek forecast takım UUID'lerini sağlayıcının insan-readable takım adlarıyla karşılaştırıyordu. Bu, geçerli anahtar olsa da gerçek API fixture eşleşmesini sistematik engelleyebilirdi. Yeni kontrol:
- İmzalı/SHA doğrulanmış `experiments/263/evidence/identity_index_263.json` takım anahtarları ve onaylı alias'lar ile UUID -> ad karşılaştırır.
- 2026–27 lig üyeliğini ve doğru ev/deplasman yönünü zorunlu tutar; fuzzy/team guessing yok.
- Türkçe `ı/İ` kaybını önler; önce resmî fikstürün UTC saati eşleşir.
- API fixtures sorgusunda `bookmakers=iddaa` filtresi açık olur.
- Bu düzeltme yalnız **gelecek** maçlardaki veri alımını etkiler. Eski ilk tahmin/karar SHA dosyaları değiştirilmez.

## Erişim engeli yazılımla aşılamaz
OddsPapi `iddaa` bağlantısı restricted/anahtar gerektiren ücretli erişimdir. Ücretsiz planda erişim bulunmadığını ve yetkisiz `iddaa` sorgusunun 403 vereceğini kendi sayfası açıkça yazıyor:
https://oddspapi.io/sportsbooks/iddaa

Sistem gizli anahtarı kendiliğinden oluşturmaz, erişim satın almaz veya bir oturumun korumasını aşmaz. Canlı API testi **anahtar + iddaa yetkisi** sağlanmadıkça yapılmış sayılamaz; sentetik testler yalnız kodun güvenliğini ölçer.

## İki kademeli gerçek çözüm
**A. Yetkili API kullanımı** (otomatik, ancak kullanıcı açıkça erişim sağladığında):
1. Kullanıcı OddsPapi iddaa erişimi için sağlayıcıya başvurur ve erişim yetkisini doğrular.
2. API key sohbet mesajına değil, GitHub repo Actions Secret `ODDSPAPI_API_KEY` içine eklenir.
3. Bir sonraki **henüz başlamamış** maçın ön-kayıt çalışmasında gerçek kaynağa bağlanıp eşleşme/karşı fiyat/tarih/SSL/SHA koşulları denetlenir.
4. Yoksa hata nedeni kayda geçer, canlı oran ve EV uydurulmaz.

**B. Ücretsiz ve uygulanabilir yedek** (insan tarafından gözlenmiş):
1. Öncelik iddaa.com; yoksa nesine.com, bilyoner.com, mackolik.com. Kullanıcı/operatör maç başlamadan gerçek sitede **aynı anda** tam karşı fiyatları (MS1/MSX/MS2; KG Var/Yok; 1.5/2.5/3.5 Alt/Üst) kontrol eder.
2. Maç kimliği, gerçek kaynak URL, gözlem UTC saati ve görülen tam karşı fiyatlar `experiments/263/market_quote_requests/` mekanizmasına yalnız doğru kaynak verisi olarak girilir. Sabah için `experiments/263/morning_quote_requests/` kullanılır.
3. Mevcut intake işlemi fiyatları doğruluk/yaş/maç öncesi kilit kurallarından geçirir. Fiyatlar **insan gözlemi**, bağımsız kodla bookmaker teyidi değildir; kanıt sınıfı açık kalır.
4. Güncel kaynak bulunamazsa sabah fiyatı yalnız **KOŞULLU**, ikisi de yoksa **S2 PAS**. S1 açıklayıcı olasılık uyarısı, model tahmini ve SHA kaydı korunur.

## Denetim ve yapılmayacaklar
- Bu belgenin ve kodun kabulü **gerçek API erişimi var** demek değildir.
- Dinamik sitelere erişimi garanti edemeyen scraper, eski aggregator ekran görüntüsü, farklı zamanlı bookmaker oranlarını birleştirme veya maç başladıktan sonra oranı geçmişe dönük tahmine yapıştırma YOK.
- İlk yarı korner, Modül 0, model parametresi veya eski maç kayıtları değişmez.
- Dört modelin matematiği değil, yalnız oran kaynağı girişindeki kimlik eşleşmesi düzeltilmiştir.
