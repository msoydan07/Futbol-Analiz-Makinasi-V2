# 2.6.3 araştırması: KG ve 2.5 kalibrasyonu, 7 olaydan tek seçim

## Veri ve yöntem

Orijinal SHA sabit 4.413 maç; 2025/26 3.533 içinden ilk 611 başlangıç geçmişi, diğer 2.922 sadece önceki günle üretilen tahmin.
Sonraki 2026/27 587 Ağustos-Eylül ve 293 Ekim kronolojik tahmin; 39 Kasım 8 orijinal SHA (tek gün).
2025/26 sezonu M4 ayarlarının geliştirilmesinde kullanıldığı, 2026/27 daha önce araştırıldığı için hiçbir örneklem yeni kör final değildir.
M4 için MS, C3 için KG/2.5. Ağırlık p = w x model + (1-w) x gün öncesi lig frekansı. w eğitim döneminde seçilip sonra donduruldu.

## Eğitimden dondurulan ağırlıklar

| Eğitim | M4 MS w | C3 KG w | C3 2.5 w |
|---|---:|---:|---:|
| train_2025_all | 0.75 | 0.25 | 0.25 |
| train_2025_nondev | 0.75 | 0.25 | 0.25 |
| train_2026_aug_sep | 1 | 0.5 | 0.25 |

## 2026_aug_sep_587

| Seçici | MS n | MS Brier | KG Brier | O2.5 Brier | Tek seçim n | İsabet % | Ortalama tahmin % |
|---|---:|---:|---:|---:|---:|---:|---:|
| FIXED_RAW_M4_MS_C3_OTHERS | 580 | 0.6011326 | 0.2437321 | 0.2451611 | 580 | 57.59 | 61.68 |
| FIXED_SHRINK_TRAIN_2025 | 580 | 0.6051475 | 0.2426112 | 0.2399376 | 580 | 62.07 | 57.43 |
| FIXED_SHRINK_TRAIN_2025_NONDEV | 580 | 0.6051475 | 0.2426112 | 0.2399376 | 580 | 62.07 | 57.43 |
| FIXED_SHRINK_TRAIN_2026_AUGSEP | 0 | None | None | None | 0 | None | None |
| LOGIT_TRAIN_2025_NONDEV | 580 | 0.6096162 | 0.2426855 | 0.2400315 | 580 | 61.55 | 58.69 |
| ASOF_LEAGUE_RATE | 587 | 0.6547396 | 0.2439779 | 0.2401027 | 587 | 56.9 | 56.59 |
| C3 | 580 | 0.6008706 | 0.2437321 | 0.2451611 | 580 | 58.62 | 61.14 |
| M4 | 587 | 0.6025588 | 0.2441503 | 0.2457875 | 587 | 59.8 | 62.72 |

## 2026_oct_293

| Seçici | MS n | MS Brier | KG Brier | O2.5 Brier | Tek seçim n | İsabet % | Ortalama tahmin % |
|---|---:|---:|---:|---:|---:|---:|---:|
| FIXED_RAW_M4_MS_C3_OTHERS | 293 | 0.5855418 | 0.2467515 | 0.2470892 | 293 | 57.68 | 62.77 |
| FIXED_SHRINK_TRAIN_2025 | 293 | 0.5897539 | 0.2440215 | 0.2436595 | 293 | 58.02 | 58.25 |
| FIXED_SHRINK_TRAIN_2025_NONDEV | 293 | 0.5897539 | 0.2440215 | 0.2436595 | 293 | 58.02 | 58.25 |
| FIXED_SHRINK_TRAIN_2026_AUGSEP | 293 | 0.5855418 | 0.2440702 | 0.2436595 | 293 | 58.7 | 60.03 |
| LOGIT_TRAIN_2025_NONDEV | 293 | 0.6030562 | 0.2441374 | 0.2434355 | 293 | 56.31 | 59.21 |
| ASOF_LEAGUE_RATE | 293 | 0.6450058 | 0.2448339 | 0.2455098 | 293 | 57.0 | 56.91 |
| C3 | 293 | 0.5823324 | 0.2467515 | 0.2470892 | 293 | 58.36 | 62.25 |
| M4 | 293 | 0.5855418 | 0.2487792 | 0.2493031 | 293 | 57.0 | 63.46 |

## 2026_nov8_sha_39

| Seçici | MS n | MS Brier | KG Brier | O2.5 Brier | Tek seçim n | İsabet % | Ortalama tahmin % |
|---|---:|---:|---:|---:|---:|---:|---:|
| FIXED_RAW_M4_MS_C3_OTHERS | 39 | 0.5099587 | 0.2463668 | 0.247555 | 39 | 66.67 | 62.67 |
| FIXED_SHRINK_TRAIN_2025 | 39 | 0.5349448 | 0.2453977 | 0.2388232 | 39 | 53.85 | 57.67 |
| FIXED_SHRINK_TRAIN_2025_NONDEV | 39 | 0.5349448 | 0.2453977 | 0.2388232 | 39 | 53.85 | 57.67 |
| FIXED_SHRINK_TRAIN_2026_AUGSEP | 39 | 0.5099587 | 0.2447006 | 0.2388232 | 39 | 64.1 | 60.07 |
| LOGIT_TRAIN_2025_NONDEV | 39 | 0.5319579 | 0.2462987 | 0.2519792 | 39 | 53.85 | 58.72 |
| ASOF_LEAGUE_RATE | 39 | 0.655725 | 0.2471151 | 0.2387669 | 39 | 51.28 | 55.71 |
| C3 | 39 | 0.5173222 | 0.2463668 | 0.247555 | 39 | 61.54 | 61.66 |
| M4 | 39 | 0.5099587 | 0.248164 | 0.2627444 | 39 | 61.54 | 63.42 |

## 2026_all_880

| Seçici | MS n | MS Brier | KG Brier | O2.5 Brier | Tek seçim n | İsabet % | Ortalama tahmin % |
|---|---:|---:|---:|---:|---:|---:|---:|
| FIXED_RAW_M4_MS_C3_OTHERS | 873 | 0.5958999 | 0.2447455 | 0.2458082 | 873 | 57.62 | 62.05 |
| FIXED_SHRINK_TRAIN_2025 | 873 | 0.5999811 | 0.2430845 | 0.2411868 | 873 | 60.71 | 57.7 |
| FIXED_SHRINK_TRAIN_2025_NONDEV | 873 | 0.5999811 | 0.2430845 | 0.2411868 | 873 | 60.71 | 57.7 |
| FIXED_SHRINK_TRAIN_2026_AUGSEP | 293 | 0.5855418 | 0.2440702 | 0.2436595 | 293 | 58.7 | 60.03 |
| LOGIT_TRAIN_2025_NONDEV | 873 | 0.6074145 | 0.2431728 | 0.241174 | 873 | 59.79 | 58.86 |
| ASOF_LEAGUE_RATE | 880 | 0.6514987 | 0.2442629 | 0.241903 | 880 | 56.93 | 56.69 |
| C3 | 873 | 0.5946487 | 0.2447455 | 0.2458082 | 873 | 58.53 | 61.51 |
| M4 | 880 | 0.5968929 | 0.2456916 | 0.246958 | 880 | 58.86 | 62.97 |

## Doğruluk ve sınırlar

MS Brier, üç sınıfın Brier toplamı; KG ve 2.5 Brier tek ikili olaydır. Düşük iyi.
Her maçtan en fazla bir olay seçildi. Aynı olayın lig geçmiş referans Brier'i de ölçüldü.
Ayrıca 60/65/70 güven eşikleri, tahmin gerçekleşme güven tabloları, lig kesitleri, maç-günü bloklu belirsizlikler ham JSON'da bulunur.
2026 Ağustos-Eylül eğitimli ağırlık o dönemde kullanılmadı: yalnız Ekim ve Kasım'a uygulandı.
Ağırlıklar görülmüş sonuçlardan seçildiği için yeni maç önü kör kanıt olmadan canlı sisteme yükseltme yapılmaz.
Canlı 2.6.3, sonuç/mühür arşivi, iş akışı, PDF, bahis otomasyonu değiştirilmedi; EV veya ROI hesaplanmadı.

Ayrıntılı veri: 07_calibration_result.json. Tekrar üretilebilir kaynak: audit_market_calibration.py.
