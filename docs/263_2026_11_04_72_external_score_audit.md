# 2.6.3 — 30 Ekim–1 Kasım 2026: 72 maç dış kaynak skor kontrolü

**Kontrol tarihi:** 2026-11-04. **Dal:** experiment/263-toplu-karsilastirma.

## Kapsam ve sonuç

`data/staged_263/2026_10_30_11_01_previous_88_web_score_refs.json` dosyasındaki 88 kaydın BEL1 ve POR1 dışındaki 72 kaydı lig lig dış sonuç sayfalarıyla karşılaştırıldı. 72 kaydın takım eşleşmeleri, maç günleri ve ev/deplasman skorları aşağıdaki kaynaklardaki maç haftası sonuçlarıyla uyuşuyor. **Skor uyuşmazlığı: 0/72.** Bu işlem skor ve tarih doğrulamasıdır; takım kimliği evrensel ID, oyuncu istatistikleri, anlık API verileri, tarihsel veri bütünlüğü, insan kaynak kabulü veya maç öncesi tahmin üretimi için ayrı kabul yerine geçmez.

| Lig | Adet | Dış kaynak | Kanıt düzeyi |
|---|---:|---|---|
| ENG1 | 9 | https://www.rte.ie/sport/results/soccer/premier-league/36781/results/?page=1 | Haber sonucu |
| ENG2 | 12 | https://www.rte.ie/sport/results/soccer/championship/38070/results/ + https://www.efl.com/news/2026/october/30/brereton-diaz-goal-gives-sheffield-united-win-over-wrexham/ | Haber + EFL |
| GER1 | 9 | https://datencenter.dfb.de/competitions/bundesliga/seasons/2026-2027 | Resmî DFB |
| ESP1 | 9 | https://rfef.es/es/competiciones/primera-division | Resmî RFEF |
| FRA1 | 8 | https://www.football.fr/football/ligue-1/resultats/9eme-journee.html | Bağımsız sonuç tablosu |
| ITA1 | 8 | https://en.legaseriea.it/serie-a/index | Resmî Lega Serie A (son maç özetleri) |
| NED1 | 9 | https://eredivisie.nl/nieuws/terugblik-speelronde-11/ + https://www.soccernews.nl/news/dit-zijn-alle-uitslagen-in-speelronde-11-van-de-eredivisie/ | Resmî lig özeti + haber sonuçları |
| TUR1 | 8 | https://beinsports.com.tr/lig/super-lig/fikstur | Yayıncı fikstürü |

## Olağan dışı tamamlanma durumu

**NED1, SC Cambuur 4–0 Go Ahead Eagles, 31.10.2026**, fixture_id `e775098b-7465-52ab-92e6-534adabea6bf`. Maç yaklaşık 81. dakikada tatil edildi; resmî karar 4–0 skorunu kesin sonuç kabul etti. **Normal tamamlanmış 90+ dakika karşılaşması değildir.** https://eredivisie.nl/nieuws/sc-cambuur-go-ahead-eagles-definitief-gestaakt/ ve https://www.knvb.nl/nieuws/organisatie/berichten/72372/cambuur-go-ahead-eagles-definitief-gestaakt. Mevcut `extended_history.csv` kaydı kaynak satırı 96 ve şut/korner alanları içeriyor; istatistikler eksik maç süresini yansıtıyor olabilir. Model eğitimi ve 90 dakika oran tahmini için ayrı EXCEPTION/ABANDONED_AWARDED_RESULTS politikası onaylanana dek **normal maç gibi kullanmayın**. Kaynak CSV değiştirilmedi.

## Sınırlar, karar

Bu belgenin **72 eşleşme** kapsamı, önceki BEL1 (9) + POR1 (7) çalışmalarını tekrar test etmez. O 16 kayıt için daha önce bir dış eşleşme bildirildi ancak bu belgenin 72-maç kontrolü içine dahil değildir. Veri paketi otomatik olarak `data/quad_accepted_263/` içine taşınmadı; `HUMAN_VERIFIED_SOURCE_ACCEPTANCE` üretilmedi. **Kaynak kabulü, özel maç durumu ve veri zaman kesiti ayrı onay gerektirir.** Resmî 100-maç pilotu ve üretim sistemi değiştirilmedi.
