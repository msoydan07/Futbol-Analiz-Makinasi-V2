# 22 Kasım 2026 — İki lig tek M4 şut deneyi (araştırma)

## Sonuç / mühendislik kararı
**ANA MAKİNEYE ALINMADI.** Mevcut M4 modeline geçmiş kaleyi bulan şut artığı eklenmesi, 2026/27 iki lig testinde Brier ve log-loss'u az iyileştirdi, fakat MS1/MSX/MS2 en olası seçenek isabeti 77/162'den 76/162'ye düştü; %95 blok-bootstrap aralığı sıfırı kapsadı. Fark lige göre ters yönlü. Bu nedenle yeni veri indirilmeyecek, ana M4/C3, v4 kalibrasyonu, raporlar, eski tahmin SHA'ları değişmeyecek.

## Veri ve yöntem
- Kaynak: `data/quad_accepted_263/extended_history.csv`, ENG1 ve GER1; 2025/26 686 maç, 2026/27 162 maç. Dört Footiqo XLSX dosyası veri denetimi için sağlandı; model deneyi repo içindeki mevcut skor+şut kayıtlarıyla çalıştı.
- Donmuş M4 kilidi: yarı ömür 360 gün, shared ridge 4, venue ridge 48. Mevcut `m4_integrated.py` aynen kullanıldı.
- Şut sinyali: önceden mevcut `exp_263_batch.py::shot_signal` fonksiyonu; **kaleyi bulan şut**, yalnız maç tarihinden önceki maçlar. Önceden hesaplanan M4 gol beklentisine log-artık düzeltmesi uygulanır; yeni bağımsız ML modeli değil.
- Katsayı adayları 0, 0.1, 0.2, 0.3, 0.5. Yalnız 2025/26 tarihsel geliştirme parçasındaki 362 maçla log-loss üzerinden seçim: **0.5**. 2026/27 sonuçları seçimde kullanılmadı.
- 2026/27: 162 maç (ENG1 90, GER1 72); 116 maçta şut düzeltmesi kullanılabilir; diğer 46 maçta aynı M4 tahmini korunur. Aynı gün sonuçları girdi yapılmaz.
- Bu sonuç **M4'ün ham MS1/MSX/MS2 dağılımının** karşılaştırmasıdır; aktif v4 MS kalibrasyonu ile C3 tabanlı KG ve 2.5 Alt/Üst kararını veya yedi tercihten ana seçimi birebir ölçmez.

| Kapsam | Ölçüt | M4 mevcut | M4+şut |
|---|---|---:|---:|
| İki lig, 162 | MS Brier ↓ | 0.61900568 | **0.61701887** |
| İki lig, 162 | MS log-loss ↓ | 1.03064006 | **1.02833104** |
| İki lig, 162 | MS en yüksek olasılık isabeti | **77/162** | 76/162 |
| ENG1, 90 | Brier ↓ | **0.62497585** | 0.62764402 |
| ENG1, 90 | MS isabet | **41/90** | 40/90 |
| GER1, 72 | Brier ↓ | 0.61154298 | **0.60373742** |
| GER1, 72 | MS isabet | 36/72 | 36/72 |

33 ayrı maç günü üzerinden 1200 tekrar blok-bootstrap, **M4−M4+şut** (pozitif şut daha iyi): MS Brier %95 CI **[-0.00642656, +0.00853334]**; MS log-loss %95 CI **[-0.00884802, +0.01099704]**. Her ikisi sıfırı içeriyor.

Sınırlılık: 2026/27 daha önceki araştırmalarda görülmüş tarihsel dönemdir; bağımsız kör ileri pilot değildir. M4+şut araştırma deneyi **aktif M4/C3 ve v4 birleşik seçicinin yerine geçmez.**

## Tek CI koşusu
[Başarılı test kaydı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44966617519)

[Salt araştırma kodu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/m4-shot-ablation-20261122/experiments/263/m4_shot_two_league_ablation_20261122.py)
