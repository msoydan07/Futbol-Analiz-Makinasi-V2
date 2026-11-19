# 2.6.3 — 10 lig resmî maç arası kaynak envanteri (19 Kasım 2026)

Bu tablo lig/kurumun yayımladığı normal maç haftası başlangıcını gösterir. **Arada ertelenmiş tek maç olmadığına ilişkin tam resmî sonuç listesi değildir.** Bu sayfalar, kaynağın tam sezonluk olmaması hâlinde `official_full_season_gap_guard_263.py` tarafından canlı onay olarak kabul edilmez.

| Lig | Son arşiv | Gelecek normal lig haftası | Resmî kaynak |
|---|---|---|---|
| ENG1 | 8 Kasım | 21 Kasım | https://www.premierleague.com/en/news/4689113/when-are-the-international-breaks-for-202627 |
| ENG2 | 7 Kasım | 21 Kasım | https://www.efl.com/news/2026/november/19/how-to-watch-and-follow-the-efl-this-weekend/ |
| GER1 | 8 Kasım | 20 Kasım | https://www.bundesliga.com/en/bundesliga/matchday/2026-2027/10 |
| ESP1 | 8 Kasım | 20 Kasım | https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-13 |
| ITA1 | 8 Kasım | 21 Kasım | https://www.legaseriea.it/serie-a/news/le-designazioni-arbitrali-della-12a |
| FRA1 | 8 Kasım | 20 Kasım | https://ligue1.com/fr/articles/l1_article_5839- |
| NED1 | 8 Kasım | 21 Kasım | https://www.knvb.nl/downloads/bestand/30384/programmavriendenloterijeredivisiekeukenkampioendivisie20tm23november2026 |
| TUR1 | 8 Kasım | 21 Kasım | https://www.tff.org/default.aspx?ftxtID=2966&pageID=600 |
| POR1 | 8 Kasım | 27 Kasım | https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada |
| BEL1 | 8 Kasım | 20 Kasım | https://www.proleague.be/jpl-kalender |

Önceki **10 günlük sabit süre** kontrolü 19 Kasım itibarıyla 10/10 teknik blok riski taşır; bu, 10/10 eksik sonuç olduğu anlamına gelmez. 21 Kasım Portekiz kupa maçları POR1 lig sonuçları olarak sayılmaz. Normal hafta takvimi kanıtı, tam sonuç/fikstür kapsaması iddiası ve canlı geçmiş veri kabulü birbirinden ayrıdır.

## Yeni uygulanan araştırma katmanı ve testler

- `experiments/263/official_full_season_gap_guard_263.py`: Önceden mevcut resmî HTML çekme/parçalama kodunu yeniden kullanır; yalnız bütün 2026/27 çift yönlü lig fikstürünü (18 takımda 306, 20 takımda 380, Championship 24 takımda 552 maç) içeren kaynağı kabul eder. Bir haftalık sayfa ile “ara boş” kanıtı verilemez. Çelişki veya aradaki tarihli fikstür varsa hata/inceleme; nihai sonuç bu modülde uydurulmaz. `production_forecast_allowed=False`.
- `experiments/263/public_provider_2627_gap_audit_263.py`: Var olan Football-Data 2026/27 10 lig CSV kaynağını salt okunur ikincil şahitle kıyaslar. Son kabul tarihinden sonra tamamlanmış lig maçı varsa bildirir; kaynak 4.618 snapshot'ın sezon ilerlemesinden gerideyse, skor tutarsızsa veya kaynak kirliyse hata verir. **Federasyon resmî onayı değildir; canlı karar kapısı açmaz.**
- Eredivisie için gerçek resmî KNVB alan adı `private_4618_matchday_preflight_263.py` izin listesine eklendi. Eski 4.413, 4.618 gizli skor, ana M4 ve SHA mühürleri değiştirilmedi.
- `experiments/263/test_private_4618_matchday_preflight_263.py` (16), `test_official_full_season_gap_guard_263.py` (9), `test_public_provider_2627_gap_audit_263.py` (8): **33/33 yerel sentetik kontrol geçti**. CI otomatik sınama dosyası güncellendi, GitHub çalışmasının başarı sonucu ayrıca teyit edilmedi.

**Açık kalan kritik iş:** Gerçek lig sayfalarından 10/10 tam sezonsal fikstür ve sonuç kapsamının alınması ve onaylı as-of veri kaynağının gerçek `iddaa_pdf_one_step_263.py` üzerinden orandan bağımsız sabah karar motoruna bağlanması. Bu iki aşama tamamlanmadı; yalnız test geçmesi maç sabahında garantili tahmin anlamına gelmez.
