# 2.6.3 — İddaa sağlayıcı API bağlantısı: devreye alma kapısı

4 Kasım 2026. OddsPapi belgeleri:
- https://oddspapi.io/sportsbooks/iddaa : **iddaa slug'i kısıtlı**. Ücretsiz pakete dahil değil; erişim sağlanmadan 403 `RESTRICTED_ACCESS` döner. Erişim için kullanıcı kendisi plan/yetki almalıdır. Bu belge ücretli planın kullanıcı tarafından alındığını iddia etmez.
- https://oddspapi.io/tr/docs/get-fixtures : futbol 10, UTC başlama, iki takım ismi, maç kimliği ve maç önü durumu.
- https://oddspapi.io/tr/docs/get-markets : dinamik market+outcome ID'leri, MS/BTTS/1.5/2.5/3.5 fulltime marketleri.
- https://oddspapi.io/tr/docs/get-odds : `bookmakerOdds.iddaa`, `markets`, `outcomes`, `players`, `price`, `updatedAt`, `fixturePath`.
- https://oddspapi.io/tr/legal/terms : fiyat doğruluğunun garanti edilmediği; kullanılmadan önce kontrol gerektirir.

## Güvenli üretim mantığı
`experiments/263/odds_provider_oddspapi_263.py` yalnız **GitHub Actions secret `ODDSPAPI_API_KEY`** ile sabit API hostuna `/fixtures`, `/markets`, `/odds?bookmakers=iddaa` çağrılarını yapar. Geçerli anahtar yoksa **NO_ODDSPAPI_KEY_CONFIGURED**, sağlayıcı 403 ise **ODDSPAPI_IDDAA_RESTRICTED_403**. Bu durumda SHA mühürlü dörtlü tahmin/baseline/ilk PAS korunur; **oran/EV uydurulmaz**.

Sağlayıcı maçından tam resmî **ev/deplasman isimleri + başlama UTC** birebir eşleşmeli (fuzzy isim benzerliği kullanılmaz); iki olası maç varsa fiyat alınmaz. İçinde iddaa kaynağı, açık bookmaker fixturePath (iddaa.com), active pazar ve tam karşı fiyatları olmalı. Üç gol çizgisi, KG ve MS için pazar kimlikleri **sağlayıcının kendi /markets listesinden** çözülür. Yalnız mevcut olan pazarlar işlenir; diğer pazarlar PAS. Sağlayıcı event güncellemesi 30 dakikadan eskiyse, T−60 tahmin 10 dakikadan eskiyse veya maç başlamışsa fiyat alınmaz.

## Güvence ayrımı
Bu veriler *API sağlayıcısı tarafından iddaa adına bildirilen fiyatlar*dır; kaynak yerel iddaa sayfasında **bağımsız doğrulandı iddiası yoktur**. Şema: `AGGREGATOR_API_NOT_DIRECT_BOOKMAKER_VERIFIED`, piyasa durumu `ODDSPAPI_AGGREGATOR_SOURCED_NOT_DIRECT_BOOKMAKER_VERIFIED`. `odds_provider_oddspapi_263.py` API response SHA, iddaa sayfa URL, bookmaker slug, API fixture id ve UTC gözlem zamanı kaydeder. Testte kullanılan bütün fiyatlar **sentetik**; gerçek API erişimi ve canlı fiyat görülmeden otomatik oran entegrasyonu **etkin/doğrulanmış** sayılmaz.

**Dondurulmuş modeller yeniden eğitilmez.** Kod başarıyla test edilir, API SECRET ile gerçek kaynak erişimi kullanıcı tarafından sağlanınca ilk gerçek maçta ayrıca T−60 doğrulaması yapılır. Yüksek EV otomatik bahis talimatı değildir; resmî pilot geçerli sayılmak için kaynak ve commit zaman denetimini geçmelidir.
