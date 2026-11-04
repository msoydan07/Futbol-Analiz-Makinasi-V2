# 2.6.3 — 6 Kasım 10 lig güncel veri, tek seferlik ön kabul

**Başlangıç bulgusu:** `data/staged_263/extended_history.csv` gerçek 4.413 kayıtlı geçmişin üzerine 88 tamamlanmış maç ekleyen, `2026-11-03` tarih kesimli **4.501 satır** içeriyor (beklenen dosya SHA `279cb00096da270f6987ae9e518fbe7248c17c993c34508499a971cae76ca4e8`). `refresh_audit.json` bunun tüm 10 ligi kapsadığını ve **HUMAN REVIEW YAPILMADIĞINI** açıkça kaydetti. 88 ekstra maç için dağılım: ENG1=9, ENG2=12, GER1=9, ESP1=9, ITA1=8, FRA1=8, NED1=9, TUR1=8, POR1=7, BEL1=9. Bu sonuçları tekrar üretmek yerine yeni kaynakla çapraz denetliyoruz.

## Bu aşamanın yaptığı

1. On ayrı `football-data.co.uk/mmz4281/2627/*.csv` **doğrudan GitHub Actions çalışırken** indirilir; URL, zaman, HTTP yanıtı, dosya SHA ve boyut **on ayrı makine alındısı** olarak saklanır. Kaynağın ilan ettiği 'son güncelleme' bilgisi tek başına futbol skor doğruluğunu kanıtlamaz. Resmi ulusal lig/federasyonlarla ikinci teyit ayrı sorumluluktur.
2. Kaydedilmiş SHA ile **orijinal 4.413 satırın** ayrı GitHub artifact'inden indirilip korunduğu kanıtlanır. `season_refresh_263.py` mevcut alias, lig üyeliği, tamamlanmış gol, tarih, kaynak satır sırası, skor tutarlılığı ve duplicate kontrollerini **değiştirilmeden** kullanır. Tüm 10 CSV tek pakette başarıyla işlenmeden çıktı kabul edilmez.
3. Daha önce hazırlanan **4.501 satırlık** stage dosyasının her maç kimliği ve her saha değeri birebir korunmalı. Sağlayıcı geçmiş skoru/satırı değiştirmişse sessiz 'düzeltme' olmaz, `BLOCKED` ve insani uzlaştırma yapılır.
4. Yalnızca `2026-11-05` gününden **önce bitmiş** maç sonuçları, 6 Kasım ilk pilot günü için son 10 gün tazelik kontrolü. Skorsuz gelecek maçlar sonuç sayılmaz.
5. Başarı halinde çıktılar GitHub Actions artifact'te `extended_history.csv`, `refresh_audit.json`, `preflight_report.json` olarak tutulur. **Bunlar HENÜZ** `data/quad_accepted_263` değildir. Gerçek kaynak skorlarının bağımsız doğrulaması, gerçek reviewer ve zaman alanları yokken `HUMAN_VERIFIED_SOURCE_ACCEPTANCE` kaydı uydurulmaz.

## Güvenlik sınırı / pilot engeli

`forward_quad.py` bugün hâlâ *insan tarafından kaynak onaylı* `data/quad_accepted_263/extended_history.csv` ve `data/quad_accepted_263/source_acceptance.json` dosyalarını bekliyor. Bu denetim **engel kaldırma değil, engeli çözmek için kanıt paketi** oluşturma aşamasıdır. Sentetik veya sonuçtan sonra türetilen tahmin yoktur.

Ayrıca 96 sabit aday maç listesinin her biri için ayrı **resmî maç/saat doğrulaması** ve GitHub'a kickoff öncesi SHA'lı model kilidi gerekir. Bir GitHub testinin yeşil olması bu şartları otomatik sağlamaz.

**Kesin sonuç:** Bu aşamadan sonra gerçek kaynak doğrulama paketi kabul edilebilirse ileri pilotu çalıştırabiliriz; sorun varsa tüm problemi tek raporda görmek ve yalnız ilgili yeri düzeltmek gerekir. B/C2/C3/M4, M4 lock, 96 aday, S1/S2 ve `main` değişmez.
