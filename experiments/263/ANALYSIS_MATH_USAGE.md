# 2.6.3 — Yalnız matematik/analiz motoru mimarisi

Bu klasör **deneyseldir**. Gerçek maç seçmez, canlı tahmin kaydetmez, oran/EV/pilot yapmaz, çalışan Model B'yi değiştirmez. Kanonik C2 (`k=5,w=.5`), sabit C3 rakip-gücü adayı, ortak maç sonu skor dağılımı, ayrı ilk-yarı gol ve maç-sonu korner sayım modelleri içerir.

**Bağımlılık:** Aynı klasörde mevcut, dondurulmuş `exp_263_batch.py` olmalı. Orijinal dosya **değiştirilmez**. Python 3.11+, `numpy`, `scipy`.

Test: `python -m unittest -v test_analysis_math_core.py` (yalnız matematik/yazılım testi). Gerçek performans karşılaştırması değildir.

Salt-okunur analiz örnek komutu (yalnızca offline/mühendislik; takım ID'leri kullanır):

```
python analysis_math_core.py --history /path/to/historical_results.csv --league ENG1 --season 2026-2027 --previous-season 2025-2026 --target-date 2026-11-02 --home-id CANONICAL_HOME_ID --away-id CANONICAL_AWAY_ID --out /tmp/math_audit.json
```

Yukarıdaki örnek **doğrulanmış fikstür değildir** ve oyuncu/kadro/veri tazeliği kontrolü içermez. Hedef maç adı verilmiş olmasını gerçek maç tahmini veya maç önü kayıt kabul etmeyin.

Kararlar ve kalite ayrımı: `ANALIZ_MIMARISI_KARARLARI.md`.
