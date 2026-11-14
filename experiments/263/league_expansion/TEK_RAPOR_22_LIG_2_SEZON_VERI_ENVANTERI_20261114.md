# 22 lig × 2 sezon — tek veri havuzu durum ve eksik kayıt raporu

**14 Kasım 2026 | Maç kesim tarihi 13 Kasım 2026 | Dal: `research/263-13-lig-22-havuz-20261113`**

Bu rapor yeni modellere geçmek için değil, **veri havuzunun mevcut durumunu ve kapanmayan eksikleri** tek yerde görmek içindir. 2026/27 hâlâ devam ediyor: “tam sezon” değil, **kesim gününe kadar oynanmış maçlar** hedeflenmiştir. Ana M4, eski mühürler ve xG dosyası değiştirilmedi.

## Sonuç — 44 lig-sezon hücresinin durumu

| Ölçü | Kaynağa dayalı sonuç |
|---|---:|
| **Lig hedefi** | **22 = 13 analiz + 9 eğitim** |
| **Sezon hücreleri** | **44 = 22 × 2** |
| 2025/26 için en az bir kalıcı skor arşivi olan lig | **22/22** |
| 2026/27 için kalıcı GitHub skor arşivi olan lig | **17/22** |
| 2026/27 için yalnız veri okuma erişimi, kalıcı arşiv yok | **5/22** |
| **GitHub'da veri bulunan hücre** | **39/44** |
| Ana 10 ligin donmuş mevcut skor arşivi | **4.617** |
| Ayrı 12 liglik araştırma arşivi | **4.842** (önceki 4.505 + İspanya 337) |
| **İki arşivdeki tekil kaynak-maç kimliği toplamı** | **9.459** |
| Bunların 2025/26 kaydı | **7.778** |
| Bunların 2026/27 kaydı | **1.681** |
| 2026/27 yalnız anlık API'de erişilen ek maç sonucu | **633**, **9.459'a dahil değil** |
| Yeni araştırma kayıtlarından onaylanan model eğitim satırı | **0** |
| Kullanıcının manuel gireceği eksik xG | **1.855** |

**9.459 sayısının sınırı:** İlk 4.617 maç ana 10 ligden, diğer 4.842 maç tamamen farklı 12 ligden geliyor. Lig grupları ayrık; bu nedenle iki kaynak grubunun toplamı alınabilir. Ancak eski HOLD, hükmen/terk edilmiş sonuç, lisans ve “maç öncesinde erişilebilir miydi?” kontrolleri nedeniyle bu sayı **9.459 temiz eğitim örneği** demek değildir.

## Her lig için iki sezonun gerçek kayıt sayısı

2025/26 sütunu tamamlanmış eski sezonun kaynak-kimlik sayısıdır. 2026/27 sütunundaki **API** ifadesi, sonuçları okunmuş ancak lisans gereği ham kayıtları herkese açık GitHub'a aktarılamamış ligleri gösterir. **2026/27'nin bütün maçlarının 13 Kasım'a dek eksiksiz olduğu henüz onaylanmadı.**

| Lig | Hedef | 2025/26 kalıcı | 2026/27 kalıcı / sadece API | Denetim notu |
|---|---|---:|---:|---|
| ENG1 · Premier League | Analiz | 380 | 100 | 380 geçmiş sezon sonuç kaydı; ana 10 lig arşivi 10 Kasım kaynak dondurması |
| ENG2 · Championship | Analiz | 552 | 180 | 552 geçmiş sezon sonuç kaydı; ana 10 lig arşivi 10 Kasım kaynak dondurması |
| GER1 · Bundesliga | Analiz | 306 | 81 | 306 geçmiş sezon sonuç kaydı; ana 10 lig arşivi 10 Kasım kaynak dondurması |
| ESP1 · La Liga | Analiz | 380 | 119 | 380 geçmiş sezon sonuç kaydı; ana 10 lig arşivi 10 Kasım kaynak dondurması |
| ITA1 · Serie A | Analiz | 380 | 110 | 380 geçmiş sezon sonuç kaydı; ana 10 lig arşivi 10 Kasım kaynak dondurması |
| FRA1 · Ligue 1 | Analiz | 306 | 90 | 306 geçmiş sezon sonuç kaydı; ana 10 lig arşivi 10 Kasım kaynak dondurması |
| NED1 · Eredivisie | Analiz | 306 | 108 | 306 geçmiş sezon sonuç kaydı; ana 10 lig arşivi 10 Kasım kaynak dondurması |
| TUR1 · Süper Lig | Analiz | 306 | 99 | 306 geçmiş sezon sonuç kaydı; ana 10 lig arşivi 10 Kasım kaynak dondurması |
| POR1 · Primeira Liga | Analiz | 306 | 98 | 306 geçmiş sezon sonuç kaydı; ana 10 lig arşivi 10 Kasım kaynak dondurması |
| BEL1 · Pro League | Analiz | 311 | 99 | 311 maç; ayrı şampiyonluk/alt grup ve istisna son kontrolü açık |
| SCO1 · Premiership | Analiz | 234 | 42 | 228 Premiership etap maçı + 6 ayrı geçiş/eleme |
| DNK1 · Superliga | Analiz | 192 | **— (API: 84)** | 192 geçmiş maç; güncel 84 yalnız API erişimi |
| CHE1 · Super League | Analiz | 228 | 57 | 228 geçmiş maç; güncel araştırma kaydı var |
| ENG3 · League One | Eğitim | 569 | 158 | 552 normal + 5 play-off + 12 eski kaynak-kimlik fazlalığı (HOLD) |
| ENG4 · League Two | Eğitim | 557 | 164 | 552 normal + 4 play-off + 1 eski fazlalık (HOLD) |
| ENG5 · National League | Eğitim | 560 | **— (API: 190)** | 551 oynanmış normal + 2 play-off + 7 eski fark; terk/hükmen ayrıldı |
| GER2 · 2. Bundesliga | Eğitim | 306 | 99 | 306 normal sezon kaydı |
| ESP2 · Segunda | Eğitim | 468 | **— (API: 141)** | 462 normal + 6 play-off; 41 mükerrer birleştirildi, 2 tarih düzeltildi |
| ITA2 · Serie B | Eğitim | 391 | **— (API: 110)** | 380 normal + 10 play-off/play-out + 1 eski fazlalık (HOLD) |
| FRA2 · Ligue 2 | Eğitim | 309 | **— (API: 108)** | 305 oynanmış normal +1 play-off +2 baraj +1 hatalı tamamlanmış 0-0 (HOLD) |
| GRE1 · Super League | Eğitim | 236 | 35 | 182 normal +54 ikinci aşama |
| AUT1 · Bundesliga | Eğitim | 195 | 42 | 192 lig etabı +3 ilave eleme |

**Toplam: 2025/26 7778; 2026/27 kalıcı 1681; birlikte 9459.** Beş ligdeki 633 canlı kaynak sonucu bu toplama eklenmedi.

## Bu turda kapattığımız önemli geçmiş sezon açığı: İspanya Segunda 2025/26

**İspanya Segunda'nın önce 131 kalıcı maçı vardı. Artık 462 normal sezon + 6 play-off kaydı var.** Bunun nasıl sağlandığı:

- Football Charts'ın 2025/26 CC BY 4.0 tarihsel yayımlanmış kaynak tablosundaki **509** `Spain / La Liga2 / spain2` sonuç satırı incelendi.
- Deportivo La Coruña'nın iki adla yazılmasından kaynaklanan **41 aynı tarih–takım–skor tekrarını** birleştirdik.
- 22 takımın her biri için **42 normal sezon maçı ve 462 benzersiz ev/deplasman eşleşmesinin tamamı** doğrulandı. **6 yükselme play-off** maçı ayrıca işaretlendi.
- Eski 131 maç aynı kimlik ve skorla çakıştığından tekrar eklenmedi.
- **331 yeni normal sezon + 6 play-off = 337 yeni maç** yalnız araştırma arşivine eklendi. **331/331 yeni normal sezon maçının skorları bağımsız ikinci kaynakla** karşılaştırıldı; play-off sonuçları ayrı maç çizelgesinde karşılık buldu.
- İlk kaynakta yanlış tarihlenen Cádiz–Almería **8 Şubat 2026**, Sporting Gijón–Leganés **2 Mart 2026** olarak ayrı düzeltilmiş arşive alındı; orijinaller korunuyor. Resmî kaynaklar: [Cádiz–Almería](https://www.laliga.com/en-GB/match/temporada-2025-2026-laliga-hypermotion-cadiz-cf-ud-almeria-25), [Sporting–Leganés](https://www.laliga.com/en-GB/match/temporada-2025-2026-laliga-hypermotion-real-sporting-cd-leganes-28).

Bu **sonuç doğrulamasıdır**, geçmiş maç önü özelliklerine eğitim izni verildiği anlamına gelmez.

## Veri toplama işinin bitmesine engel olan somut eksikler

**1 — 2026/27 sezonundaki beş kaynak hakkı.** National League **190**, Segunda **141**, Serie B **110**, Ligue 2 **108**, Danimarka **84**: toplam **633** maç sonucu Football Charts'ın canlı araştırma API'sinden okundu. Ancak **canlı API hakları**, eski CC BY tarihsel veri setinin haklarıyla aynı değil; büyük ham sonuç alıntılarını herkesin görebildiği GitHub'a yeniden yayımlayamıyoruz. Bunları gerçekten kalıcı olarak toplayabilmek için kullanım izni veren özgün veri veya yazılı izin gerekiyor. Hakları belirsiz başka bir derlemedeki 632 satır da aktarılmadı.

**2 — 13 Kasım 2026'ya kadar güncellik kapanışı.** Ana on ligin 4.617 sonuçlu kaynak dosyası **10 Kasım 2026** tarihinde dondurulmuş. 10–13 Kasım günlerinde yeni oynanmış karşılaşma bulunup bulunmadığı her lig için son kaynakla ayrıca kapatılmadı. Genişlemenin yedi güncel ligi de eşit tarihli kaynakla son karşılaştırma bekliyor. Yani **kayıt var ≠ kesim tarihine kadar kesin eksiksiz**.

**3 — Eski kimlik fazlalıkları, ertelenme ve hükmen maçlar.** İngiltere League One'da **12**, League Two'da **1**, National League'de **7**, İtalya Serie B'de **1** eski kaynak kimliği normal sezon + tanımlı play-off sayısının üzerinde duruyor. Bunları ayrı HOLD veya kaynak uzlaşmazlığı olarak araştırmak gerekiyor. Fransa Ligue 2'de Bastia–Red Star'ın **5 Aralık 2025 tarihli tamamlanmamış 0-0** sonucu ayrıca HOLD; tamamlanmış maç etiketi olarak kullanılamaz. Belçika Pro League 2025/26 **311** kayıt için play-off/istisna sayım kapanışı yapılmalı. Önceki **296 kaynak kalite HOLD** kaydı eğitim havuzuna katılmadı.

**4 — Doğru rekabet aşaması.** İskoçya 228 Premiership etap maçı ve 6 ayrı eleme/geçişi; Yunanistan 182 normal + 54 ikinci aşamayı; Avusturya 192 etap + 3 ek elemeyi; İspanya Segunda 462 normal + 6 yükselme play-off'unu; İtalya Serie B 380 normal + 10 play-off/play-out'u ayrı tutuyor. Ek aşama kayıtlarını normal sezon formuna karıştırmayacağız.

**5 — Kullanıcının xG dosyası ve sonradan yapılacak eğitim güvenliği.** 2025/26 için **1.765**, 2026/27 için **90**, toplam **1.855** eksik xG çifti bekliyor. Kullanıcının özel Excel dosyası değiştirilmedi. Kaynak lisansı ve tarihsel maç önü özelliklerine ait gerçek erişim zaman damgaları yeni eğitim onayı için ayrıca gerekli; burada geriye dönük kanıt uydurulmadı.

## Son karar: Bitirdik mi?

**Kaynak bulma:** 2025/26 için 22/22 ligde kayıt; 2026/27 için 17/22 kalıcı, 5/22 erişilebilir ancak kalıcı hakkı bekliyor. **Eksiksiz iki sezonluk arşiv: henüz HAYIR.** Mevcut 9.459 kayıt kalite/hak/tarih kontrolü olmadan tamamen kullanılabilir kabul edilemez.

**Sıradaki yalnızca veri işleri:** (1) Beş güncel ligin kalıcı lisanslı kaynakları, (2) 22 ligde 13 Kasım kesim tarihine kadar oynanan maçların son envanteri, (3) legacy fazlalık ve hükmen sonuç istisnalarının kapanışı, (4) manuel xG girişinin ayrıca tamamlanması. **Model geliştirmeye ve yeni pilotlara geçilmiyor.**

## Kanıtlar ve tekrarı önleme

- Ana on lig 4.617 sonuç: `data/results_only_263/2026-11-10_completed_4617_scores_only.csv` (kaynak SHA `637b8597...`), `data/results_only_263/4617_research_input_provenance.json`.
- İlk 4.505 araştırma kimliği / 26 ayrı sabit dosya: `experiments/263/league_expansion/4505_rights_provenance_and_pre_kickoff_asof_source_gate_20261114.json`.
- İspanya 462+6 ve 41 mükerrer kaydı: `experiments/263/league_expansion/ccby_footballcharts_esp2_2025_26_original_source/esp2_2025_26_462_regular_41_duplicate_alias_6_playoff_131_old_identity_20261114.json`; yeni 331/331 ve iki tarih: `experiments/263/league_expansion/ccby_footballcharts_esp2_2025_26_original_source/esp2_2025_26_target_only_32_unresolved_alias_and_two_official_dates_20261114.json`.
- Ana 10 + diğer 12 lig, **44 hücrenin toplu okuma sayımı**: `experiments/263/league_expansion/22x2_full_production_plus_research_inventory_diagnostic_20261114.json`, ilgili GitHub Actions başarılı.
- Beş ligin yalnız canlı API kapsamı ve hakları: `experiments/263/league_expansion/current_2026_27_five_leagues_footballcharts_personal_research_API_rights_probe_20261114.json`.
- xG eski kontrolü: `experiments/263/league_expansion/manual_xg_1855_excel_readonly_snapshot_20261114.json`.
- Döngü önleme kaydı: `experiments/263/league_expansion/historical_loop_prevention_new_archive_3122_20261114.json`.
- Eski bütün başarılı maç sonucu denetimleri tekrar çalıştırılmadı; bu rapor veri-kimlik ve yeni kaynak kapsamı kapanışıdır.

**Son durum: 44/44 lig-sezon için sonuç kaynağına erişim veya kalıcı skor bulunuyor, fakat yalnız 39/44'ü GitHub'da kalıcıdır; doğrulanmış tamlık, hak ve eski HOLD eksikleri bitmediği için “veri toplama tamamen bitti” beyanı yapılmıyor.**
