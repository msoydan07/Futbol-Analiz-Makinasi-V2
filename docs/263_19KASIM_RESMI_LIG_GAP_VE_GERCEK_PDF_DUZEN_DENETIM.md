# Futbol 2.6.3 — 19 Kasım 2026 resmî lig aralığı + eski gerçek PDF düzeni denetimi

**Araştırma durumu:** Lig puan tablosu/sonuç/hafta takvimiyle kontrol; canlı veri kabulü **DEĞİL**. Bu belge yeni pilot başlatmaz, tahmin üretmez, resmî tek mühürleri ve ana M4 kodunu değiştirmez.

## Verinin değişmez kontrolü

- Özel yalnız skor CSV: `263_4618_MATCHDAY_SCORES_RESEARCH_PRIVATE_20261119.csv` — **4.618 satır, SHA-256 `54250bb6107250d0623b74ad9c56f90731f02d10dab3bf386deefb27aae487ea`** yeniden hesaplandı.
- 2026/27 lig dağılımı: `BEL1=99, ENG1=100, ENG2=180, ESP1=119, FRA1=90, GER1=81, ITA1=110, NED1=108, POR1=98, TUR1=99`.
- Bu sayımlar **tüm 4.618 maçın değil**, yalnızca `2026-2027` lig sonuçlarının adetleridir.

## 9–19 Kasım 2026 sonuç aralığının kamusal resmî sayfa kontrolü

| Lig | Son arşiv | 2026/27 skor sayısı | Resmî çapraz kontrol | Sonuç / kanıt düzeyi |
|---|---|---:|---|---|
| ENG1 | 8 Kasım | 100 | [Premier League: uluslararası ara 9–17 Kasım, yeni lig haftası 21 Kasım](https://www.premierleague.com/en/news/4689113/when-are-the-international-breaks-for-202627); [ilk 10 hafta resmî değerlendirmesi](https://www.premierleague.com/en/news/4763141/what-we-learned-from-the-202627-season-so-far/) | Normal hafta uyumlu; tüm erteleme sonuçları bağımsız olarak satır satır teyit edilmedi |
| ENG2 | 7 Kasım | 180 | [EFL 19 Kasım: Championship millî aradan sonra bu hafta sonu dönüyor](https://www.efl.com/news/2026/november/19/how-to-watch-and-follow-the-efl-this-weekend/); [EFL maç arası politika sayfası](https://www.efl.com/supporters/faqs/fixtures/) | Normal hafta uyumlu; resmî tam 15 haftalık sonuç listesi bağımsız sayılmadı |
| GER1 | 8 Kasım | 81 | [Bundesliga resmî puan tablosunda 18 takım × 9 maç](https://www.bundesliga.com/en/bundesliga/table); [10. hafta 20 Kasım'da başlıyor](https://www.bundesliga.com/en/bundesliga/matchday/2026-2027/10) | Güçlü sayım eşleşmesi, ek sonuç işareti yok |
| ESP1 | 8 Kasım | 119 | [LaLiga resmî 12. hafta sonuçları 6–8 Kasım](https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-12); [13. hafta 20 Kasım](https://www.laliga.com/en-GB/laliga-easports/results/2026-27/gameweek-13) | Normal hafta uyumlu; 119 sayısı 12×10 olan 120'den 1 eksik, önceki haftalardan ertelenmiş maç durumu için tam resmî sezon kontrolü şart |
| ITA1 | 8 Kasım | 110 | [Serie A resmî 11. hafta 6–8 Kasım](https://www.legaseriea.it/serie-a/news/le-designazioni-arbitrali-della-11a); [12. hafta 21 Kasım](https://www.legaseriea.it/serie-a/calendario-risultati) | Hafta sayısıyla tutarlı, tam resmi sonuç satırı denetlenmedi |
| FRA1 | 8 Kasım | 90 | [Ligue 1 resmî 10. hafta değerlendirmesi](https://ligue1.com/fr/articles/l1_article_6054-j10-les-enseignements-du-week-end-ligue-1-2026-2027); [11. hafta 20 Kasım](https://ligue1.com/fr/articles/l1_article_5839-) | Hafta sayısıyla tutarlı, tam resmi sonuç satırı denetlenmedi |
| NED1 | 8 Kasım | 108 | [Eredivisie resmî puan tablosu: 18 takım × 12 maç](https://eredivisie.nl/competitie/stand/); [KNVB resmî sonuç ekranında son bitmiş maç 8 Kasım](https://www.knvb.nl/competities/eredivisie/uitslagen) | Güçlü sayım/tarih eşleşmesi; ek sonuç işareti yok |
| TUR1 | 8 Kasım | 99 | [TFF 2026/27: 18 takım × 11 maç ve yeni 12. hafta 21 Kasım](https://www.tff.org/Default.aspx?pageId=198) | Güçlü sayım eşleşmesi; ek sonuç işareti yok |
| POR1 | 8 Kasım | 98 | [Liga Portugal Betclic resmî sayfası](https://www.ligaportugal.pt/competition/618/liga-portugal-betclic/round/20262027?tab=standings); [resmî 12. hafta takvimi](https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada) | 98 sayısı tam 11 hafta 99'dan 1 eksik; ertelenmiş maç ayrı araştırılmalı; kupa karşılaşmaları lig maçı olarak eklenmeyecek |
| BEL1 | 8 Kasım | 99 | [Pro League resmî puan tablosunda 18 takım × 11 maç](https://www.proleague.be/jpl-ranking); [12. hafta maçları 20 Kasım'da başlıyor](https://www.proleague.be/jpl-kalender) | Güçlü sayım eşleşmesi; ek sonuç işareti yok |

**Sonuç:** 10 ligin normal programının millî araya denk geldiği resmî sayfalardan destekleniyor, dört ligde (GER1/NED1/TUR1/BEL1) **mevcut resmî puan tablosu ile veri sayısı birebir**. Ancak tüm 10 lig için **9–19 Kasım'da erteleme dahil hiçbir tamamlanmış maç yok** iddiası, tam resmî sezon sonuçlarında ayrı ve güncel satır taraması olmadan onaylanmaz. Özellikle ESP1 ve POR1 zaten birer maçlık eski program farkı içeriyor; bu maçların sonradan bitip bitmediği 20 Kasım öncesinde ayrıca denetlenmeli. Bu nedenle yapay 10-gün engeli de körlemesine kapatılmayacak.

## Kullanıcıya ait 11 Kasım 2026 gerçek iddaa PDF'sinin yalnız biçim testi

Kullanıcının daha önce yüklediği `iddaa Programı - iddaa Bülteni _ iddaa.com.pdf` (PDF oluşturulma 11 Kasım 2026) salt okunur olarak incelendi:

- **3 sayfa, 30 tanınabilir maç-satırı.** Bunların **28'inde 14 fiyat konumu** yakalandı; **2'sinde 13 konum** görüldü. Eksik konumdaki satırlar (Heart of Midlo…–Montrose FC (K), Real Soacha C…–Real Cartagen…) `PRICE_COLUMN_ALIGNMENT_UNRESOLVED` olarak engellenmeli; yanlış pazara kaydırma yapılmamalı.
- Bültenin 30 satırının tamamı U19, kadınlar, kupa, amatör veya aktif 10 lig kapsamı dışında. `FRANSA 1.LİG, KADINLAR` isim benzerliğine rağmen FRA1'e girmemeli.
- Bu **geçmiş tarihli** gerçek PDF, 19–21 Kasım maç sabahı testinin yerini alamaz. **Hiçbir maç tahmini veya SHA mührü oluşturulmadı.** Test PDF'nin asıl baytları özel alanda kalmıştır; GitHub'a yüklenmedi.

## Gerçekten kalan iş

1. **ESP1 ve POR1 başta olmak üzere** resmî tam sonuç/ertelenmiş maç kapsaması için seçili günün maç önü sonuç kaynaklarını tekrar doğrula; diğer liglerde de kaynağı yenile. Tamamlanmış lig maçı sonradan görünürse geçmişi append-only sürüme güncelle (4.618 dondurulmuş sürümü değiştirmeden).
2. Kullanıcının **gerçek ve yeni tarihli ilk iddaa PDF** gönderimiyle `resmî fikstür → dört model → oran bağımsız ana/alternatif/PAS → bir SHA → piyasa 5. referans → rapor` akışını çalıştır; ikinci PDF yalnız kaynaklı ilk 11/oran hareketi yorumudur. Başlangıç sonrası tahmin yok.
3. Eski 496 maçın yüzde güvenilirliği uyarısı geçerlidir; ham yüzdeyi değiştiren öneriler mevcut bağımsız test olmadan M4'e/kararlara terfi ettirilmez.

**Değişmezler:** Ana M4, 96 mühürlü pilot, otomasyonlar, geçmiş SHA, D-MARKET-006 ve D-ODDS-001 kararları **değişmedi**.
## EK KANIT — İki 2026/27 lig sayımı farkı açıklandı (19 Kasım 2026, önceki belirsizliği geçersiz kılar)

**ESP1 119/120 (Rayo Vallecano–Athletic Club, 8. hafta):** İki takımın maç sayısı 11, diğer 18 takımın 12; 10 Ekim 2026 maçındaki saha olayları nedeniyle müsabaka durdu. [Athletic Club resmî açıklaması](https://www.athletic-club.eus/en/news/2026/10/10/the-athletic-club-squad-returns-to-bilbao/) ve [LaLiga'nın 8. hafta sonuç ekranı](https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-8) müsabakanın **9 Aralık 2026** için programlandığını doğrular. **Tam maç sonucu henüz yok; mevcut 119 satıra eklenmez.**

**POR1 98/99 (Estoril Praia–Marítimo, 11. hafta):** İki takım 10, diğer 16 takım 11 maç oynamış. [Estoril Praia resmî kulüp açıklaması](https://estorilpraia.pt/blog/jogo-com-o-cs-maritimo-adiado) 8 Kasım tarihli karşılaşmanın kötü hava koşulları nedeniyle ertelendiğini doğrular. [RTP'nin Liga Portugal açıklamasına dayanan haberi](https://www.rtp.pt/noticias/1a-liga/jornada-11-da-liga-so-fecha-em-janeiro_d1778268) yeni maç tarihini **4 Ocak 2027** olarak bildiriyor. **Bu da henüz tamamlanmış sonuç değil; 98 satır doğru.**

Her iki maç, özel 4.618 skor CSV'sindeki `home_id`/`away_id` ile eşleştirildi. Günün gelmesi **otomatik sonuç ekleme yetkisi vermez**; müsabaka gerçekten tamamlandıktan sonra resmi skor doğrulanarak *yeni append-only sürüme* alınır. Önceki “ESP1/POR1 nedeni bilinmeyen eksik” notu bu iki özel maç için **GEÇERSİZ KALDI**; erteleme dışında başka maçın eksik olmadığı iddiası ise resmî tam sonuç kapsamına tabidir. Makine-okunur kaynak kaydı: [bilinen tamamlanmamış maçlar](../experiments/263/evidence/263_UNFINISHED_ESP1_POR1_MATCHES_20261119.json).

**Sonuç:** Önceden saptanan iki birer-maçlık toplam farkın ikisi de **oynanıp bitmemiş** fikstürden kaynaklanıyor. 19 Kasım itibarıyla tamamlanmış 9–19 Kasım lig maçı eksiği bulunduğuna dair eldeki kaynaklarda pozitif kanıt yok. Bu, bütün 10 ligin resmî güncel sonuç listesi için otomatik tam kapsama onayı değildir.
