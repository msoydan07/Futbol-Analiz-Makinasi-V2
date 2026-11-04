# 2.6.3 — 88 önceki ek maç, 10 lig skor çapraz kontrolü (4 Kasım 2026)

**Durum:** webde gözlenen 30 Ekim–1 Kasım 2026 lig sonuçları ile 88 satırlık 2026/27 ek verinin maç, tarih, ev/deplasman ve skor eşleşmesi tek bir deftere aktarıldı. Bu, **gerçek insan kaynak kabulü değildir**. Kullanıcı adına `HUMAN_VERIFIED_SOURCE_ACCEPTANCE` imzalanmaz, `data/quad_accepted_263/` oluşturulmaz.

**Kanıt dosyası:** `data/staged_263/2026_10_30_11_01_previous_88_web_score_refs.json` — her maçın bağımsız spor sayfasında görülen skoru, ekranda listelenen maç ismi, tarih, source URL ve kaynak seviyesi.

| Lig | Önceki ek maç | Web skoru kaynağı | Kaynak düzeyi |
|---|---:|---|---|
| ENG1 | 9 | [The Guardian](https://www.theguardian.com/football/premierleague/results) | Medya |
| ENG2 | 12 | [RTÉ 31 Ekim](https://www.rte.ie/sport/results/soccer/championship/38070/results/), [EFL 30 Ekim](https://www.efl.com/news/2026/october/30/brereton-diaz-goal-gives-sheffield-united-win-over-wrexham/) | Medya + resmî EFL |
| GER1 | 9 | [DFB](https://datencenter.dfb.de/competitions/bundesliga/seasons/2026-2027) | Resmî federasyon |
| ESP1 | 9 | [LaLiga](https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-11) | Resmî lig |
| ITA1 | 8 | [Sky Sport](https://sport.sky.it/calcio/serie-a/calendario-risultati) | Yayıncı |
| FRA1 | 8 | [Stade Rennais](https://www.staderennais.com/matchs/2026-10-30-nice-vs-rennes) | Resmî kulüp / hafta sonucu |
| NED1 | 9 | [KNVB](https://www.knvb.nl/competities/eredivisie/uitslagen) / [Eredivisie](https://eredivisie.nl/nieuws/terugblik-speelronde-11/) | Federasyonun arama indeksi, lig özeti |
| TUR1 | 8 | [beIN Türkiye](https://beinsports.com.tr/lig/super-lig/fikstur) / [TFF fikstürü](https://www.tff.org/Default.aspx?pageId=198) | Yayıncı + federasyon |
| POR1 | 7 | [LiveScore](https://www.livescore.com/en/football/portugal/primeira-liga/results/) / [Liga Portugal programı](https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada) | Skor servisi + resmî fikstür |
| BEL1 | 9 | [FootyPulse](https://footypulse.org/leagues/belgium/pro-league/results) | Üçüncü taraf skor arşivi |
| **Toplam** | **88** | | |

İlk 4.413 satırın SHA'sı `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`; hazırlanmış 4.501 satırın SHA'sı `279cb00096da270f6987ae9e518fbe7248c17c993c34508499a971cae76ca4e8`; son 4.509 satırın SHA'sı `69d687965500a260cc965a1482c23c1e07f11ebcabb1adaa9441dc6a17334a14`.

Tek hedefli CI, bu **üç gerçek SHA**'lı dosyayı *yeniden indirmekten ya da veriyi tekrar modellemeye sokmaktan kaçınarak* mevcut GitHub artifactlerinden bulup şu 4 koşulu kontrol eder: (1) eski 4.413 değişmedi, (2) 4.501'in eski satırları ve 88 ek kayıt aynen duruyor, (3) bunlara eklenen 8 maç 2 Kasım tarihli, (4) 88/88 webde gözlenen skorlarla eşleşiyor. **Kaynak web sayfalarının ham SHA'ları saklanmıyor** ve skor listesi web tarayıcıdan destekli elle/AI aktarımıdır: aynı provider altyapısına dayanıyor olma veya siteye sonra müdahale edilme riski var. Bu nedenle bağımsız tüm sezon doğrulaması veya bahis avantajı iddiası yok.

**Daha önce dikkat çeken tarih uyuşmazlığı:** Ligue 1 eski Eylül TV programı Nice–Rennes'i 31 Ekim gösteriyordu; [LFP'nin 26 Ekim tarihli resmî değişiklik duyurusu](https://www.lfp.fr/article/ogc-nice-stade-rennais-avance-au-vendredi-30-octobre-a-19-h00) maçın 30 Ekim'e alındığını doğruluyor. Verinin 30 Ekim tarihi bu açıdan doğru, eski fikstürü kopyalayıp tarih değiştirmeyin.

**Sonraki zorunlu aşama:** Kullanıcı veya atanmış gerçek kaynak denetçisi tarafından kaynaklar ve 88 + 8 maçın kapsamı teyit edilirse, `source_acceptance.json` yalnız gerçek inceleyen kişi/inceleme saati/SHA ile oluşturulur. Maç öncesi model kilidi, yalnız ayrıca doğrulanmış resmî fikstür ve gerçek KO'dan önce Git commit ile yapılabilir. Önceden model hesaplanmış gibi geriye dönük dosya yok.
