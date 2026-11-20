# 2.6.3 — Bağımsız matematik alternatifleri, araştırma sonucu

**Dönemler:** 587 Ağustos-Eylül geliştirme; 293 Ekim araştırılmış değerlendirme; 39 Kasım 8 orijinal maç önü SHA (tek gün). **Hiçbiri bağımsız kör final sınaması değildir.**

**Ölçek:** MS çok sınıflı Brier (3 sınıfın toplamı), KG ve 2.5 için tek olayın ikili Brier; küçük değer iyi.

| Model | Ekim n(MS) | MS Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|---:|
| ASOF_LEAGUE_RATE | 293 | 0.645006 | 0.244834 | 0.245510 |
| B | 212 | 0.583902 | 0.249775 | 0.253301 |
| C2 | 105 | 0.623237 | 0.247246 | 0.245890 |
| C3 | 293 | 0.582332 | 0.246752 | 0.247089 |
| M4 | 293 | 0.585542 | 0.248779 | 0.249303 |
| ENSEMBLE_50_50 | 293 | 0.583318 | 0.247558 | 0.247860 |
| DC_MINUS_0.1 | 293 | 0.587933 | 0.248102 | 0.249303 |
| DC_PLUS_0.1 | 293 | 0.584528 | 0.249686 | 0.249303 |
| BIVARIATE_0.15 | 293 | 0.587399 | 0.247720 | 0.249777 |
| NB_K3 | 293 | 0.587623 | 0.261578 | 0.252715 |
| NB_K8 | 293 | 0.585726 | 0.251933 | 0.250109 |
| M4_DEV_SHRINK | 293 | 0.585542 | 0.244610 | 0.243584 |
| C3_DEV_SHRINK | 293 | 0.582332 | 0.244070 | 0.243660 |
| ENSEMBLE_50_50_DEV_SHRINK | 293 | 0.583318 | 0.244288 | 0.243601 |
| DIRECT_LOGIT_C0.5 | 293 | 0.583760 | 0.244344 | 0.240995 |

## Ekim 293 maç, aynı maç eşleştirmesi — referans eksi aday Brier

Pozitif fark aday lehine; farklı model kapsaması çift-eşleme ile sınırlandı. Gün bloklu %95 aralıklar, çoklu deneme düzeltmesi değil.

| Aday | Pazar | Ortak n | Fark | Gün bloklu %95 aralık |
|---|---|---:|---:|---|
| ASOF_LEAGUE_RATE | MS | 293 | -0.05946404 | [-0.07733908, -0.03945366] |
| ASOF_LEAGUE_RATE | KG | 293 | 0.00191753 | [-0.00816379, 0.01671104] |
| ASOF_LEAGUE_RATE | O25 | 293 | 0.00157938 | [-0.0110294, 0.01993117] |
| B | MS | 212 | -0.00591494 | [-0.01338003, 0.00283373] |
| B | KG | 212 | -0.00133932 | [-0.00894532, 0.00498813] |
| B | O25 | 212 | -0.00354008 | [-0.00973518, 0.00494002] |
| C2 | MS | 105 | -0.00975795 | [-0.0524328, 0.01213207] |
| C2 | KG | 105 | -0.01026314 | [-0.02505443, 0.00632869] |
| C2 | O25 | 105 | -0.00152903 | [-0.01719235, 0.01698218] |
| C3 | MS | 293 | 0.00320934 | [-0.00211931, 0.00902051] |
| C3 | KG | 293 | 0.0 | [0.0, 0.0] |
| C3 | O25 | 293 | 0.0 | [0.0, 0.0] |
| M4 | MS | 293 | 0.0 | [0.0, 0.0] |
| M4 | KG | 293 | -0.00202777 | [-0.00565233, 0.00059928] |
| M4 | O25 | 293 | -0.00221391 | [-0.0060607, 0.00188742] |
| ENSEMBLE_50_50 | MS | 293 | 0.00222377 | [-0.00041237, 0.00509214] |
| ENSEMBLE_50_50 | KG | 293 | -0.00080701 | [-0.00262292, 0.00049886] |
| ENSEMBLE_50_50 | O25 | 293 | -0.00077118 | [-0.00268167, 0.00129258] |
| DC_MINUS_0.1 | MS | 293 | -0.00239156 | [-0.00507058, -4.055e-05] |
| DC_MINUS_0.1 | KG | 293 | -0.0013508 | [-0.00579625, 0.00226466] |
| DC_MINUS_0.1 | O25 | 293 | -0.00221391 | [-0.0060607, 0.00188742] |
| DC_PLUS_0.1 | MS | 293 | 0.00101421 | [-0.00129321, 0.00368742] |
| DC_PLUS_0.1 | KG | 293 | -0.00293429 | [-0.00657764, -0.00038144] |
| DC_PLUS_0.1 | O25 | 293 | -0.00221391 | [-0.0060607, 0.00188742] |
| BIVARIATE_0.15 | MS | 293 | -0.00185685 | [-0.00462661, 0.0005454] |
| BIVARIATE_0.15 | KG | 293 | -0.00096817 | [-0.0053068, 0.00274479] |
| BIVARIATE_0.15 | O25 | 293 | -0.00268769 | [-0.00593519, 0.00068351] |
| NB_K3 | MS | 293 | -0.00208114 | [-0.00734488, 0.00384703] |
| NB_K3 | KG | 293 | -0.01482646 | [-0.02993406, -0.00478677] |
| NB_K3 | O25 | 293 | -0.00562585 | [-0.01004088, -0.00150809] |
| NB_K8 | MS | 293 | -0.00018444 | [-0.00244407, 0.00246261] |
| NB_K8 | KG | 293 | -0.00518173 | [-0.01145228, -0.00099592] |
| NB_K8 | O25 | 293 | -0.00301931 | [-0.00580475, 9.179e-05] |
| M4_DEV_SHRINK | MS | 293 | 0.0 | [0.0, 0.0] |
| M4_DEV_SHRINK | KG | 293 | 0.00214149 | [-0.00375776, 0.00983304] |
| M4_DEV_SHRINK | O25 | 293 | 0.00350512 | [-0.0060103, 0.01789261] |
| C3_DEV_SHRINK | MS | 293 | 0.00320934 | [-0.00211931, 0.00902051] |
| C3_DEV_SHRINK | KG | 293 | 0.00268125 | [-0.00245863, 0.01023955] |
| C3_DEV_SHRINK | O25 | 293 | 0.00342963 | [-0.00602577, 0.01728169] |
| ENSEMBLE_50_50_DEV_SHRINK | MS | 293 | 0.00222377 | [-0.00041237, 0.00509214] |
| ENSEMBLE_50_50_DEV_SHRINK | KG | 293 | 0.00246308 | [-0.00286965, 0.00986964] |
| ENSEMBLE_50_50_DEV_SHRINK | O25 | 293 | 0.00348836 | [-0.00604523, 0.01745206] |
| DIRECT_LOGIT_C0.5 | MS | 293 | 0.00178197 | [-0.01019005, 0.01020963] |
| DIRECT_LOGIT_C0.5 | KG | 293 | 0.00240742 | [-0.0056524, 0.0139534] |
| DIRECT_LOGIT_C0.5 | O25 | 293 | 0.00609394 | [-0.00981846, 0.02864494] |

## En yüksek olasılıklı tek olay kararı (MS/KG/2.5; maç başına tek karar)

| Politikа | Ekim seçilen | İabet % | Tahmini ort. % | Seçilen Brier | Kasım 8 isabet % |
|---|---:|---:|---:|---:|---:|
| M4 | 293 | 57.0 | 63.46 | 0.24309 | 61.54 |
| C3 | 293 | 58.36 | 62.25 | 0.239456 | 61.54 |
| ASOF_LEAGUE_RATE | 293 | 57.0 | 56.91 | 0.244008 | 51.28 |
| ENSEMBLE_50_50 | 293 | 57.34 | 62.78 | 0.240763 | 61.54 |
| M4_DEV_SHRINK | 293 | 59.39 | 60.22 | 0.236639 | 64.1 |
| C3_DEV_SHRINK | 293 | 58.7 | 59.39 | 0.235654 | 58.97 |
| ENSEMBLE_50_50_DEV_SHRINK | 293 | 59.39 | 59.75 | 0.236732 | 61.54 |
| DIRECT_LOGIT_C0.5 | 293 | 59.39 | 64.39 | 0.241396 | 58.97 |
| FIXED_M4_MS_C3_OTHER | 293 | 57.68 | 62.77 | 0.242331 | 66.67 |

## Sınırlar ve mühendislik kararı

- Sonuçlar **RETROSPEKTİF / KEŞİF**: 2026/27 sonuçları geçmiş araştırmalarda görülmüştü. Ekim iyi çıkınca uygulamaya terfi yok.
- xG zaman damgaları ve özel kaynaklı as-of sayılar bu araştırma dalına taşınmadı; xG ablation tamamlanmış sayılmaz.
- Gol dağılımı DC, bivariate ve Negative Binomial adayları M4 lambdasını sabit tutarak test edildi; bunlar tam yeniden eğitilmiş rakip gol modelleri değildir.
- Doğrudan logit yalnız önceden üretilmiş C3/M4 olasılıkları ve lig geçmişiyle eğitilmiş ikinci-aşama sınıflandırmadır; sıfırdan ham maç özelliği kullanan derin model değildir.
- Model sonuçlarının 39 Kasım mühürlü karşılığı yalnız bir maç günüdür; sonuçların tamamı federasyon seviyesinde bağımsız teyit edilmiş değil.
- Aynı maçtaki 7 sonuç tek bir bağımsız gözlem değildir. Karar tablosu her maç için tam **bir** olay sayar.
- Bahis oranı/EV/ROI bu denetimin hedefi değildir. Herhangi bir yöntemden kâr garantisi çıkmaz.
- **Karar: Mevcut 2.6.3, mühürler, aktif modeller ve PDF korunur.** Denenen adaylar yalnız aday araştırmadır; kör kanıt yokken üretim terfisi yapılamaz.

Ayrıntılı ham ölçümler, kapsama ve eşleşmiş güven aralıkları: `02_result.json`.
