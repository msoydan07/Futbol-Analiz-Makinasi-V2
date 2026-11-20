# 2.6.3 — Son ayrıştırma: MS modelini koru, KG ve 2.5'i ayrı düzelt

Bu çalışma ilk 2025/26 ve 2026/27 kalibrasyon çalışmalarının takip tanı testidir.
Hiperparametreler ve alternatifler daha önce araştırılmış verilere göre seçilmiş olduğu için sonuçlar yeni kör kanıt değildir.
Kaynak: aynı SHA doğrulanan orijinal 4.413 maç, 2026/27 880 tarih bazlı tahmin, ayrıca 8 Kasım 39 maç önü SHA.
Yalnız M4 MS hamı ve C3 KG/2.5 + o günden önceki lig frekansı karışımı; aile bazlı tek olay seçimi.

## Aday ağırlıkları (MS M4 her zaman 1.0)

- RAW: KG C3=1, 2.5 C3=1; önceki aktif benzeri ham aile yönlendirmesi.
- P25: KG C3=0.25, 2.5 C3=0.25 (2025/26 geliştirme-dışı öğrenilmiş, 2026/27'ye dondurulmuş).
- P50: KG C3=0.50, 2.5 C3=0.25 (2026 Ağustos-Eylül öğrenilmiş; SADECE Ekim ve Kasım'da incelendi).
- P00: KG ve 2.5 C3=0, yalnız önceki günün lig frekansı.

## aug_sep

| Aday | n | MS Brier | KG Brier | 2.5 Brier | Tek seçim % | Tahmin % | n(>=65) | >=65 isabet % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FIXED_RAW_M4_MS_C3_OTHERS | 580 | 0.6011326 | 0.2437321 | 0.2451611 | 57.59 | 61.68 | 157 | 71.97 |
| MS_M4_RAW_KG_C3_025_O25_C3_025 | 580 | 0.6011326 | 0.2426112 | 0.2399376 | 60.52 | 59.03 | 97 | 77.32 |
| MS_M4_RAW_KG_C3_050_O25_C3_025 | 0 | None | None | None | None | None | 0 | None |
| MS_M4_RAW_KG_LEAGUE_O25_LEAGUE | 580 | 0.6011326 | 0.2438549 | 0.2407591 | 60.69 | 59.42 | 91 | 76.92 |

Eşleştirilmiş hit farkı ve Brier farkı %95 tarih-gün blok bootstrap dahil JSON dosyasındadır.

## october

| Aday | n | MS Brier | KG Brier | 2.5 Brier | Tek seçim % | Tahmin % | n(>=65) | >=65 isabet % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FIXED_RAW_M4_MS_C3_OTHERS | 293 | 0.5855418 | 0.2467515 | 0.2470892 | 57.68 | 62.77 | 94 | 65.96 |
| MS_M4_RAW_KG_C3_025_O25_C3_025 | 293 | 0.5855418 | 0.2440215 | 0.2436595 | 58.36 | 59.96 | 62 | 66.13 |
| MS_M4_RAW_KG_C3_050_O25_C3_025 | 293 | 0.5855418 | 0.2440702 | 0.2436595 | 58.7 | 60.03 | 62 | 69.35 |
| MS_M4_RAW_KG_LEAGUE_O25_LEAGUE | 293 | 0.5855418 | 0.2448339 | 0.2455098 | 59.04 | 60.26 | 67 | 62.69 |

Eşleştirilmiş hit farkı ve Brier farkı %95 tarih-gün blok bootstrap dahil JSON dosyasındadır.

## nov8_sha

| Aday | n | MS Brier | KG Brier | 2.5 Brier | Tek seçim % | Tahmin % | n(>=65) | >=65 isabet % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FIXED_RAW_M4_MS_C3_OTHERS | 39 | 0.5099587 | 0.2463668 | 0.247555 | 66.67 | 62.67 | 13 | 76.92 |
| MS_M4_RAW_KG_C3_025_O25_C3_025 | 39 | 0.5099587 | 0.2453977 | 0.2388232 | 61.54 | 59.47 | 7 | 85.71 |
| MS_M4_RAW_KG_C3_050_O25_C3_025 | 39 | 0.5099587 | 0.2447006 | 0.2388232 | 64.1 | 60.07 | 7 | 85.71 |
| MS_M4_RAW_KG_LEAGUE_O25_LEAGUE | 39 | 0.5099587 | 0.2471151 | 0.2387669 | 64.1 | 59.46 | 7 | 85.71 |

Eşleştirilmiş hit farkı ve Brier farkı %95 tarih-gün blok bootstrap dahil JSON dosyasındadır.

## original_880

| Aday | n | MS Brier | KG Brier | 2.5 Brier | Tek seçim % | Tahmin % | n(>=65) | >=65 isabet % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FIXED_RAW_M4_MS_C3_OTHERS | 873 | 0.5958999 | 0.2447455 | 0.2458082 | 57.62 | 62.05 | 251 | 69.72 |
| MS_M4_RAW_KG_C3_025_O25_C3_025 | 873 | 0.5958999 | 0.2430845 | 0.2411868 | 59.79 | 59.34 | 159 | 72.96 |
| MS_M4_RAW_KG_C3_050_O25_C3_025 | 293 | 0.5855418 | 0.2440702 | 0.2436595 | 58.7 | 60.03 | 62 | 69.35 |
| MS_M4_RAW_KG_LEAGUE_O25_LEAGUE | 873 | 0.5958999 | 0.2441835 | 0.2423535 | 60.14 | 59.7 | 158 | 70.89 |

Eşleştirilmiş hit farkı ve Brier farkı %95 tarih-gün blok bootstrap dahil JSON dosyasındadır.

## Nihai araştırma güvenlik kapısı

2025/26 M4 parametre geliştirme dönemi ve 2026/27 daha önce araştırılmıştır: bağımsız kör sonuç yok.
8 Kasım 39 mühür tek maç günü olduğu için aralık hesaplanmaz ve tek başına üretim terfisi için kullanılamaz.
Farklı yedi olay birbirinden bağımsız değildir, maç başına en fazla bir seçim yapılmıştır.
Sonuçlar canlı 2.6.3 motoru, mühürleri, mevcut günlük/haftalık takip işleri veya bahis kuralları üzerinde hiçbir değişiklik yapmaz.
Piyasadan maç önü oranı ve EV/ROI olmadığından bahis kârlılığı iddia edilmez.

Ham çıktı: 09_decision_ablation_result.json; test kodu: audit_decision_ablation.py.
