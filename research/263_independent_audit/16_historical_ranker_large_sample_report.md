# 2.6.3 — Daha fazla maçla ana tercih güvenilirliği karşılaştırması

Araştırma dalında tamamlanan geriye dönük tarih-sıralı deney: **3.802 değerlendirme maçı; 39 gerçek SHA değil**.

2025/26 2.922 as-of maç ve 2026/27 880 as-of maç (M4 ham MS, C3 ham KG/2.5).
Ek ayrı 2026 Eylül-Ekim 621 kaynak maçta dondurulmuş Ağustos ortak MS kalibrasyonuyla canlıya yakın varyant.
As-of olayın kendisi, aynı maç gününün başka lig sonuçları ve gelecek skorlar eğitim arşivine dahil edilmez.
39 SHA yalnız gerçek pre-kickoff mühür kanıtıdır; diğerleri doğrulanmış as-of geriye dönük yeniden hesaplamadır.

## Karar katmanı seçenekleri

- RAW_MAX: En büyük olasılık.
- PAST_20PRIOR_NO_SUPPORT_GATE: mevcut sıralamaya benzer (20*p + geçmiş isabet)/(20+n); yerel ligde n>=8 varsa yerel, değilse tüm lig.
- PAST_20PRIOR_ONLY_WHEN_N20: n<20 ise mevcut model yüzdesine dön.
- PAST_20PRIOR_ONLY_WHEN_N50: n<50 ise mevcut model yüzdesine dön.
- TEN_LEAGUE_ONLY_20PRIOR: yalnız tüm lig, yerel örnek yok.
- PAST_20PRIOR_N20_NORMALIZED: n<20 fallback, sonra üç olay ailesi kendi içinde toplam 1 olacak biçimde normalize.
- M4_MS_PLUS_25_C3_75_PREVIOUS_LEAGUE: M4 MS aynen; KG ve 2.5 için C3'ün %25'i, maç gününden önceki lig bazının %75'i.

## Dönem bazlı sonuçlar

### 2025_26_datewise_2922 (2898 maç / 188 gün)

| Ana tercih kuralı | n | Gerçekleşme % | Ortalama tahmin % | Seçim Brier | Raw'dan farklı olay sayısı |
|---|---:|---:|---:|---:|---:|
| RAW_MAX | 2898 | 57.246 | 62.929 | 0.2499529 | 0 |
| PAST_20PRIOR_NO_SUPPORT_GATE | 2898 | 55.59 | 61.552 | 0.2477429 | 1135 |
| PAST_20PRIOR_ONLY_WHEN_N20 | 2898 | 56.108 | 62.118 | 0.2485515 | 960 |
| PAST_20PRIOR_ONLY_WHEN_N50 | 2898 | 56.522 | 62.865 | 0.2502584 | 522 |
| TEN_LEAGUE_ONLY_20PRIOR | 2898 | 56.073 | 58.779 | 0.2439294 | 1117 |
| PAST_20PRIOR_N20_NORMALIZED | 2898 | 56.729 | 61.789 | 0.2466733 | 992 |
| M4_MS_PLUS_25_C3_75_PREVIOUS_LEAGUE | 2898 | 56.97 | 59.879 | 0.2431593 | 1106 |

### 2026_27_datewise_880 (873 maç / 60 gün)

| Ana tercih kuralı | n | Gerçekleşme % | Ortalama tahmin % | Seçim Brier | Raw'dan farklı olay sayısı |
|---|---:|---:|---:|---:|---:|
| RAW_MAX | 873 | 57.617 | 62.046 | 0.2395367 | 0 |
| PAST_20PRIOR_NO_SUPPORT_GATE | 873 | 58.992 | 61.63 | 0.2364674 | 397 |
| PAST_20PRIOR_ONLY_WHEN_N20 | 873 | 59.45 | 61.86 | 0.2354271 | 387 |
| PAST_20PRIOR_ONLY_WHEN_N50 | 873 | 60.023 | 62.274 | 0.2343088 | 325 |
| TEN_LEAGUE_ONLY_20PRIOR | 873 | 61.168 | 58.982 | 0.2339721 | 390 |
| PAST_20PRIOR_N20_NORMALIZED | 873 | 59.908 | 61.44 | 0.2337104 | 391 |
| M4_MS_PLUS_25_C3_75_PREVIOUS_LEAGUE | 873 | 59.794 | 59.34 | 0.2335103 | 358 |

### all_asof_3802 (3771 maç / 248 gün)

| Ana tercih kuralı | n | Gerçekleşme % | Ortalama tahmin % | Seçim Brier | Raw'dan farklı olay sayısı |
|---|---:|---:|---:|---:|---:|
| RAW_MAX | 3771 | 57.332 | 62.725 | 0.2475415 | 0 |
| PAST_20PRIOR_NO_SUPPORT_GATE | 3771 | 56.378 | 61.57 | 0.2451326 | 1532 |
| PAST_20PRIOR_ONLY_WHEN_N20 | 3771 | 56.881 | 62.058 | 0.2455132 | 1347 |
| PAST_20PRIOR_ONLY_WHEN_N50 | 3771 | 57.332 | 62.728 | 0.246566 | 847 |
| TEN_LEAGUE_ONLY_20PRIOR | 3771 | 57.253 | 58.826 | 0.2416242 | 1507 |
| PAST_20PRIOR_N20_NORMALIZED | 3771 | 57.465 | 61.708 | 0.2436723 | 1383 |
| M4_MS_PLUS_25_C3_75_PREVIOUS_LEAGUE | 3771 | 57.624 | 59.754 | 0.2409255 | 1464 |

### 2026_sep_oct_frozen_MS (615 maç / 39 gün)

| Ana tercih kuralı | n | Gerçekleşme % | Ortalama tahmin % | Seçim Brier | Raw'dan farklı olay sayısı |
|---|---:|---:|---:|---:|---:|
| RAW_MAX | 615 | 56.423 | 62.48 | 0.2430819 | 0 |
| PAST_20PRIOR_NO_SUPPORT_GATE | 615 | 57.073 | 62.82 | 0.245438 | 282 |
| PAST_20PRIOR_ONLY_WHEN_N20 | 615 | 58.211 | 62.68 | 0.2428351 | 177 |
| PAST_20PRIOR_ONLY_WHEN_N50 | 615 | 57.724 | 62.453 | 0.2414791 | 69 |
| TEN_LEAGUE_ONLY_20PRIOR | 615 | 57.724 | 62.508 | 0.2436261 | 360 |
| PAST_20PRIOR_N20_NORMALIZED | 615 | 58.537 | 62.496 | 0.2429282 | 180 |
| M4_MS_PLUS_25_C3_75_PREVIOUS_LEAGUE | 615 | 57.073 | 59.777 | 0.2393923 | 246 |

### 2026_oct_only_frozen_MS (293 maç / 19 gün)

| Ana tercih kuralı | n | Gerçekleşme % | Ortalama tahmin % | Seçim Brier | Raw'dan farklı olay sayısı |
|---|---:|---:|---:|---:|---:|
| RAW_MAX | 293 | 55.973 | 63.12 | 0.2447544 | 0 |
| PAST_20PRIOR_NO_SUPPORT_GATE | 293 | 57.679 | 63.422 | 0.2437096 | 128 |
| PAST_20PRIOR_ONLY_WHEN_N20 | 293 | 56.997 | 63.123 | 0.2434987 | 77 |
| PAST_20PRIOR_ONLY_WHEN_N50 | 293 | 56.314 | 62.999 | 0.2442791 | 30 |
| TEN_LEAGUE_ONLY_20PRIOR | 293 | 58.703 | 63.03 | 0.2420245 | 188 |
| PAST_20PRIOR_N20_NORMALIZED | 293 | 57.338 | 62.801 | 0.2436924 | 76 |
| M4_MS_PLUS_25_C3_75_PREVIOUS_LEAGUE | 293 | 57.679 | 60.423 | 0.2391026 | 111 |

## Sınırlamalar

- Aynı olay ve benzer olasılık bandı (±5 puan), önceki gün sonuçları. Tek maç yedi bağımsız bahis değildir.
- Eski dönemde kullanılan M4 sürümü ile Ağustos'ta kalibre edilen MS sürümü birbirine geçmiş kayıt diye karıştırılmadı.
- M4'ün 2025/26 ayar dönemini ve daha önce araştırılmış 2026/27 sonuçlarını yeniden değerlendirmek tamamen yeni kör test değildir.
- Üretimdeki tam karar kodu tarihsel 39 gerçek mühür için ayrı sınır uygular; buradaki 3.802 as-of denemesi onun gerçek mühür havuzuna eklenmedi.
- Oran, xG, kâr, ROI, aktif model, ana mühürler ve otomasyonlar değişmedi.

JSON: 15_historical_ranker_large_sample.json; betik: audit_ranker_large_sample.py.
