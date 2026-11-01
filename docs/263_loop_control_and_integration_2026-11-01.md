# 2.6.3 — DÖNGÜ KONTROLÜ ve birleşik offline analiz raporu

Tarih: 2026-11-01. **Deney dalında, üretim motorundan izole.**

## Tekrarlanmayan, önceden tamamlanmış işler

- 4.413 maç / 10 lig / iki sezon veri snapshot'ının ilk denetimi;
- C0/C1/C2/C3 rakip gücü ve gol deneylerinin geçmiş performans karşılaştırmaları;
- önceki xG, Elo, recency adayları; bunlar aynen korunur ve yeniden koşulmadı;
- ilk yarı MS / gol çizgileri / korner tarihsel kabul karşılaştırması;
- ilk C3 ileri dönem kayıt kodu: **kullanıcı isteğiyle beklemede**, bu akışa bağlanmadı;
- 2.6.3 matematik çekirdeğinin önceden bulunan sekiz, kalite katmanının on dört yazılım testi.

## GitHub dosya denetimiyle bulunan gerçek eksik

Deney dalında `analysis_math_core.py`, `acceptance_263.py`, karar belgeleri ve `QUALITY_GATE_USAGE.md` vardı; **`quality_gate_263.py`, `test_quality_gate_263.py` ve kilitli kabul JSON'u depoda yoktu**. Bu eksik tamamlanmadan matematik → pazar kalite zinciri çalıştırılamıyordu.

## Bu tek işte tamamlananlar

1. Orijinal `quality_gate_263.py` ve testleri, **kodlarını ve kabul sonuçlarını değiştirmeden**, deney dalına aktarıldı.
2. SHA-256 sabitlenmiş `evidence/acceptance_263.json` depoya eklendi. Beklenen SHA-256: `68f7cc5ff1918d70324b56f5182fa7c922b7c7d5dfb1fc40a300f34a28c51fef`.
3. `integrated_offline_report.py` modülü 2.6.3 matematik çekirdeğini kalite kapısına ve **17 bölüm uyum tablosuna** bağlar; tek ve çoklu offline vakaları destekler.
4. Kaynak CSV SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1` değilse üretim amaçlı CLI işlemi reddeder; aynı gün veya sonraki veri hesaplanmaz.
5. `test_integrated_offline_report.py` ile on bir yeni bütünlük testi yazıldı; **sekiz eski matematik + on dört eski kalite + on bir yeni birleşik = 33 test** en son toplu çalıştırmada geçti. Bir parametre ismi uyumsuzluğu ilk denemede bulunup düzeltildikten sonra bütün grup yeniden çalıştırıldı; model parametresi veya performans verisi değiştirilmedi.
6. **Yeni futbol performans deneyi, GitHub Actions koşusu, gerçek maç kaydı, oran/EV, pilot, C3 terfisi, ana motor değişikliği yapılmadı.**

## Kullanım — offline kod/bütünlük incelemesi

Deney dalında örnek kayıtlar kullanılabilir ama gerçek maçın resmî fikstürü doğrulanmış değildir. `--cases` dosyası yalnızca aşağıdaki alanlardan oluşan JSON dizisidir:

```
[{"league":"<lig_id>","season":"2026-2027","previous_season":"2025-2026",
  "target_date":"YYYY-MM-DD","home_id":"<canonical_id>","away_id":"<canonical_id>"}]
```

İşlem varsayımsaldır; bu örnek metin **doğrulanmış maç tarihi/kimliği değildir**. 20 vakadan fazlası engellenir; tekrarlanan vaka ve geçmişte tanınmayan takım reddedilir.

```bash
python -m pip install numpy scipy
cd experiments/263
python -m unittest discover -p 'test_*.py' -v
python integrated_offline_report.py \
  --history /path/to/historical_results.csv \
  --evidence evidence/acceptance_263.json \
  --cases /path/to/hypothetical_cases.json \
  --out-json /tmp/offline_audit.json \
  --out-markdown /tmp/offline_audit.md
```

Bu CLI gerçek maç tahmini, bahis önerisi veya pilot başlatmaz. Bütün öneri/terfi alanları kapalıdır. 2.6.3 şablonunun 17 bölümünü **TAMAMLANDI** diye göstermez; hangi alanlarda resmî veri, kalibrasyon, takım bağlamı, xG, kadro ve oran eksik olduğunu açıkça belirtir.

## Açık kalan sıradaki tek teknik iş

**Offline veri/kaynak → matematik → kalite → tam şablon girişleri** arasındaki gerçek kaynak/güncellik/oyuncu bilgisi sınırlamasını mühendislik olarak çözmek. Yalnızca gerekli yeni testleri planlayıp toplu yapmak; eski 1X2/xG/Elo/korner geçmiş deneylerini yeniden koşmamak. **Gerçek maç tahmin kaydı, pilot ve oran/EV daha sonra.**