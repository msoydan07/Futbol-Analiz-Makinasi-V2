# 8 Kasım 2026 — 10 lig sabah fikstür ön-denetimi

Kullanıcının sabit kararı: Cuma/Cumartesi/Pazar MAÇ SABAHI dört model B/C2/C3/M4 ve The Odds API üzerinden Pinnacle h2h oranı, kaynak gözlem zamanı ve SHA kaydı. T−60 fiyatı beklenmez.

- Yeni experiments/263/sabah_10league_manifest_preflight_263.py, o gün Türkiye saatinde resmî siteyi her lig için bir kere okur. Her lig için kanonik takım, kesin UTC KO, kaynak erişim durumu ve gerekirse engel gerekçesi ayrıdır.
- Yanıtı boş veya JS ile okunamayan site, o ligde maç yok şeklinde değerlendirilmez. Eksik futbol maçı sessizce silinmez; resmî sayfa tüm ligi kapsıyor iddiası yapılmaz.
- Aday manifesti, yalnızca kaynak kanıtı alınmış maçları içerir ve kullanıcı/new100 pilot isteği yerine GEÇMEZ. Yeni100 resmi canlı named-gate, SHA, pilot ve model kalibrasyonu bağımsız kalır.
- Yeni GitHub workflow, manuel istek veya güncel gün için yeni preflight request dosyası eklenmesiyle read-only rapor hazırlar. Pilot defterini değiştirmez, Pinnacle API kredisi harcamaz.
- 7 sentetik test o gün/10 lig kapsama, kanonik eşleşme, saat, kaynak eksikliği, tekrar/ambigü ve pilot girişinden ayrımı denetler.

AÇIK KALAN: İngiltere Championship (ENG2), Portekiz Primeira Liga (POR1), Belçika Pro League (BEL1) canlı resmî HTML/API ayrıştırması için kaynak saha kabulü yapılmadı. 10 ligdeki bütün maçların tek canlı sabah koşusunda 4-model + Pinnacle SHA mührü yapıldığı henüz kanıtlanmadı. Main ve mevcut 44 araştırma maçı değişmez.
