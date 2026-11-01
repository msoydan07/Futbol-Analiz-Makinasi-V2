# 2.6.3 Pazar güvenilirlik kapısı — sadece offline deney

**Durum:** Kod ve yazılım kontrolleri hazır, ana motorda aktif DEĞİL. **Tarih:** 1 Kasım 2026.

## İşleyiş

- `analysis_math_core.py` ile k=5, w=0.5 formüllü C2 ve kilitli C3 **ayrı** tutulur. Skor matrisinden çıkan yüzdeler, modelin gerçek maçlarda güvenilir olduğunun kanıtı değildir.
- `quality_gate_263.py` aynı maçın offline `build_analysis(...)` JSON sonucunu, aynı CSV'den okunmuş geçmiş satırları ve **değiştirilmemiş** `evidence/acceptance_263.json` kabul kaydını çapraz denetler.
- Tam kabul JSON'u için SHA-256 = `68f7cc5ff1918d70324b56f5182fa7c922b7c7d5dfb1fc40a300f34a28c51fef`. Geçmiş CSV kabul snapshot'ı = `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- Ana maç-sonu pazarları, varsa **C2 hesaplandı ama tarihsel olarak doğrulanmadı** etiketini taşır; C3 yalnız `experimental_audit` bölümündedir. C2 eksikse C3 otomatik ikame edilmez.
- İlk yarı MS 1X2 geçmiş karşılaştırmada olumlu: `DENEYSEL_RETROSPEKTIF_SINYAL`, **TERFİ YOK**.
- İlk yarı 0.5/1.5/2.5 gol çizgileri ve maç-sonu 7.5/8.5/9.5/10.5 korner çizgileri için yeni sayım modeli lig referansını geçemedi: yalnız geçmiş lig frekansı, Laplace `(olay+1)/(maç+2)` (as-of, gün hariç, yeterli veri varsa). **Bunlar takıma/maça özel pazar tahmini değildir.**
- İlk yarı KG/doğru skor, ev/deplasman takım kornerleri ve en çok korner takımı **kanıt eksikliği nedeniyle otomatik öneriye çıkmaz**; ilk yarı korner 2.6.3 kapsamı dışında.
- Bütün `can_recommend=false`, `calibrated=false`. Gerçek fikstür kontrolü, ilk 11, odds, EV, pilot, maç öncesi kayıt ve sonuç değerlendirme **YAPILMIYOR**.
- `fixture_verified` veya `is_real_match_forecast=true` ise kod reddeder. Bu bir canlı maç motoru değildir.

### Kullanım

Aşağıdaki analiz dosyası gerçek fikstür değil **offline matematik çıktısı** olmalıdır:

```bash
python experiments/263/quality_gate_263.py \
  --history /path/to/historical_results.csv \
  --analysis /path/to/offline_analysis.json \
  --evidence experiments/263/evidence/acceptance_263.json \
  --out /path/to/quality_audit.json \
  --markdown /path/to/quality_audit.md
```

Yerel yazılım testi (sonuç tahmin başarısı testi değildir):

```bash
cd experiments/263
python -m unittest test_quality_gate_263.py -v
```

**Sınırlamalar:** 2026/27 test örneklemi önceden incelenmişti; gelecek maçlara dair bağımsız kanıt yok. Lig referanslarının sezonlar arası karışımı iki sezonluk eldeki veri havuzuna göre as-of yapılır; bu takım gücünü veya güveni ölçmez. Veri snapshot'ı değişirse kaynak ve sonuç kanıtı ayrı sürümlenmeden eski etiket yeni başarı kanıtı sayılmaz. Bu kalite katmanı yayımlanmadan önce dış resmî fikstür, veri kesimi (TSİ/UTC) ve gerçek veri alım kapısı ayrı doğrulanacaktır.