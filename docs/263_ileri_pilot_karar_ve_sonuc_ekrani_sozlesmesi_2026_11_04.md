# 2.6.3 — İleri pilot karar sözleşmesi (DONDURULMUŞ TASLAK)
Tarih: 2026-11-04. Dal: experiment/263-toplu-karsilastirma. DURUM: Araştırma/ön kayıt; canlı karar motoruna bağlı değil.

## Değişmez ilkeler
- Eski 4.413 maç SHA256=35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1; B/C2/C3/M4 hesapları, ana dal ve 100-maç pilot kayıtları değişmez.
- 880 maç retrospektif as-of simülasyondur, gerçek zamanlı mühürlü tahmin değildir. Ekim 293 maç geliştirme sırasında incelenmiştir; bağımsız holdout sayılmaz.
- Çalıştırılmamış yeni eşikler kanıtlanmış diye sunulmaz. Tarihsel DEV skill filtresi ileri sonuç görülmeden dondurulmuş bir adaydır, ana politika değildir.

## Tahmin ve veri kapıları
1. Fikstür resmî kaynaktan doğrulanır; tek maç isteğinde Modül 0 yok. İlk 11 açıklanmaması analizi durdurmaz, T-60'da doğrulama durumu kaydedilir.
2. Analiz anı UTC, maç başlama saati ve kaynak zamanları, takım kimlikleri, veri kesimi, her modelin kullanılabilirlik ve yokluk nedeni kayıt edilir.
3. Her pazar için model ham olasılığı, kalibre olasılık, as-of lig/pazar bazı, DEV Brier/log-loss skill, örneklem büyüklüğü, belirsizlik ve varsa oran kaynağı/zamanı saklanır.
4. C2 erken sezonda kapsama dışıysa 0 tahmin uydurulmaz; diğer modellerin bağımsız değerlendirilmesi C2'nin yerine geçmiş sayılmaz.
5. Oran yoksa EV/ROI yoktur; olasılık temelli ana aday 'bahis değeri kanıtlandı' diye etiketlenmez.

## Karar ve sunum
- Önce her pazarın kendi bazına göre kalibrasyon ve geçmiş becerisi kontrol edilir; sırf en yüksek ham yüzde kazandırmaz. Bütün pazarlara aynı ilke; 1,5 Üst/3,5 Alt için keyfi ceza veya kota yok.
- Aynı maçtaki iç içe olaylar (1,5 Üst ve 2,5 Üst gibi) bağımsız ana+alternatif gibi sunulmaz. Alternatif yalnız farklı ve yeterli kanıtlı aday varsa gösterilir.
- PAS nedenleri ayrı kodlanır: FIXTURE_UNVERIFIED, NO_MODEL_COVERAGE, INSUFFICIENT_HISTORY, POOR_CALIBRATION, NO_EDGE, SOURCE_STALE, ODDS_MISSING_FOR_VALUE, CONFLICTING_EVIDENCE. ODDS_MISSING_FOR_VALUE yalnız değer temelli seçimi engeller; salt olasılık raporunu engellemez.
- Çıktı alanları: match_id, asof_utc, main_pick|null, alternative_pick|null, decision=MAIN|PAS, calibrated_probability|null, confidence_basis, odds|null, ev|null, selection_reason, pas_reasons[], source_timestamps, model_availability, correlated_market_warning, immutable_record_id.
- Güven yüzdesi ile olay olasılığı aynı metrik değildir. Ana seçim de gerçek bahis tavsiyesi olarak sunulmaz.

## Önceden belirlenen ileri değerlendirme
- 6–8 Kasım ve sonraki maçlarda kickoff öncesi hash'li, değişmez kayıtlar; sonuç sonrası eşleşme.
- Aynı maç/olay üzerinde Brier, log-loss, kalibrasyon, kapsama/PAS, ana ve alternatif gerçekleşme, pazar yoğunlaşması, lig ve dönem kırılımları; doğrulanmış eşzamanlı oran varsa EV/ROI.
- Aynı olayların as-of lig bazına karşı karşılaştırması; seçilmiş olayların skoruna ek olarak bütün uygun adayların skorunu raporla (seçim yanlılığını görünür kıl).
- Tek maç veya tek hafta ile terfi kararı yok; yeterli ileri örneklem birikene kadar deneysel etiket. Önceden kilitlenmeyen eşik değiştirilirse yeni versiyon ve yeni ileri kohort gerekir.

## Kanıt
- https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41836437930
- https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41836896944
- docs/263_880_gecmis_mac_karar_katmani_tek_muhendislik_sonucu_2026_11_04.md
