# 2.6.3 — 7 Kasım 2026 resmî fikstür canlı taraması / kabul raporu

## Tekil sonuç
- Deney dalı: experiment/263-toplu-karsilastirma; kod commit bfcbef940b9d5ca1ff46a54323c61e79fb442397.
- Canlı kaynak okuma iş akışı: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42355793583
- Toplu offline kabul: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42355793727 — 66 test, 66 başarı.
- 96 tarih-listesi eski aday kohortundan bugün (7 Kasım) 44 aday: resmî sayfada açık saatiyle bulunan **18**, sayfada kesin doğrulanamayan **26**.
- Kaynak sayfası 10/10 ligden indirildi, ancak tam sayfa erişimi/kapsama 10/10 değildir.
- Bu sadece maç listesinde resmî sayfa-saat eşleşme ön kanıtıdır; **named-match identity kapısı, veri kabulü, pre-KO SHA commit ve dört model forward tahmini değildir**. Yeni forward kaydı 0, Pinnacle/API isteği 0.

## Lig bazında kanıt
| Kod | Bugünkü aday | Sayfada saatli | Engelli | Resmî kaynak / parser |
|---|---:|---:|---:|---|
| TUR1 | 4 | 3 | 1 | TFF 11. hafta programı: https://www.tff.org/default.aspx?ftxtID=2966&pageID=600 |
| ENG1 | 4 | 4 | 0 | Güncellenmiş Kasım duyurusu: https://www.premierleague.com/en/news/4725574/fixture-amendments-for-premier-league-matches-in-november |
| ENG2 | 11 | 0 | 11 | EFL resmî matches sayfası; HTML'de doğrulanmış eşleşme çıkmadı |
| GER1 | 5 | 0 | 5 | DFL products fixtures; canlı HTML okuyucu 0 yapılandırılmış kayıt döndürdü |
| ESP1 | 4 | 2 | 2 | LaLiga resmî sonuçlar sayfası, iki eşleşme bulunamadı |
| ITA1 | 4 | 4 | 0 | Lega Serie A 11. hafta hakem atamaları: https://www.legaseriea.it/serie-a/news/le-designazioni-arbitrali-della-11a |
| FRA1 | 2 | 2 | 0 | Ligue 1 J10 duyurusu: https://ligue1.com/fr/articles/l1_article_5732-mpp-les-infos-de-la-journee-l1 |
| NED1 | 3 | 3 | 0 | KNVB güncel Eredivisie resmi programı |
| POR1 | 3 | 0 | 3 | Liga Portugal ham resmi calendar sayfasında yapılandırılmış maç yok |
| BEL1 | 4 | 0 | 4 | Pro League ham resmi sayfada yapılandırılmış maç yok |

## 3 aşamalı gelişme
- İlk tarama: 5 saatli, 4 tarihli, 33 doğrulanamayan, 2 kaynak erişim hatası.
- Fransa J10 düzeltmesi: 7 saatli, 4 tarihli, 33 doğrulanamayan.
- İtalya+TFF düzeltmesi ve kesin lig sınırı: 14 saatli, 4 tarihli, 26 doğrulanamayan.
- Kasım Premier League güncellemesi: **18 saatli / 26 engelli**, 0 yalnız tarihli.

## Güvenlik ve açık işler
- TFF yazılımında Süper Lig/1. Lig kaynak tablolarının karıştığı 62-satır hatası yakalandı ve ikinci resmî tablo başlığında sert kesme kuralıyla düzeltildi. Son canlı kaynak raporu TFF için sadece 9 üst lig fikstürü ayıklıyor. 4 adaydan 3'ü sayfa ile kesin saatli eşleşti; Göztepe–Başakşehir sayfa eşleştirmesi henüz doğrulanmadı. Nedenini başka kanıt olmadan tahmin etmeyin.
- ENG1 Kasım duyurusundaki kaynakça cümlesi açıkça tüm saatleri GMT ve saat yazılmayan maçları 15:00 olarak belirtiyor; bu, geçici yıllık fikstürden daha güçlü delildir. Yine de maç günü güncel resmî kapı korunur.
- Kod yeni sezonu veya diğer haftaları kapsıyormuş gibi kabul edilmemelidir. TUR1/ITA1/FRA1/ENG1 kaynak ayrıştırıcıları 2026 Kasım başlığına bağlı sınırlı sürümlerdir. Sonraki haftalar için kaynak yenilemesi gerekir.
- ENG2/GER1/POR1/BEL1 için canlı resmî programın ham HTML/JS temsili veya ayrı resmî duyuru adaptörü, gerçek test olmadan "hazır" olarak ilan edilmemelidir.
- Kaynak sayfasında görülen 18 eşleşme eski 96 maç aday dosyasına veya ayrı 100 maç sabah pilotuna otomatik tahmin olarak eklenmedi.
- main, B/C2/C3/M4 ve DEV/M4 kilitleri, Pinnacle kredi politikası ve önceki mühürlü tahminler değiştirilmedi.
