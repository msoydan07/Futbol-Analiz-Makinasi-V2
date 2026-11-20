# 2.6.3 — Tek ana tercihi mühendisçe seçmek: tarih-kilitli model kararı

Bu rapor sonuçları kendiliğinden canlıya terfi ettirmez. Sadece izole araştırma kodu çalıştırıldı.
Temel hedef: MS1, X, MS2, KG Var/Yok, 2.5 Üst/Alt olasılıklarını **aynı ölçekte kalibre edip** maç başına sadece en büyük olasılıklı olayı ana tercih yapmak.
Olayın gerçek olasılığı bilinemez; kaçınılmaz belirsizliğin bir kısmı açıklanmalıdır.

## Veri ayrımı ve güvenlik

- Orijinal 4.413 maç kaynağı SHA sabit; 2025/26 2.922 maçın C3 geçmişi, 2026/27 Ağustos-Ekim 880 tarih öncesi retrospektif rekonstrüksiyon, 8 Kasım 39 gerçek SHA.
- 2025/26 C3 KG/2.5 bağımsız olarak her pazar için sadece *önceden* öğrenildi (lojistik); geçmiş tahmin ve sonuçlar 2026 testinden önce tamamlanmıştı.
- Beta kalibratörü her maç günü sadece önceki günlerin C3 olasılık/sonuçlarını kullanır; **aynı günün sonuçları yok**.
- Canlıya yakın MS: Ağustos 2026'da kilitli ortak M4 MS kalibrasyonu sadece 2026 Eylül-Ekim ve Nov8 mühürlerinde kullanıldı; 2025/26 ve Ağustos 2026'ya yanlış uygulanmadı.
- 2025/26 M4 hiperparametre geliştirme, 2026/27 önceden araştırılan dönem. Sonuçlar yeni, tamamen kör dış test değildir.

## Karşılaştırılan sabit seçenekler

- RAW: M4 MS + C3 KG ve 2.5 ham yüzdeleri.
- C3_25_BASE_75, C3_50_BASE_50: KG ve 2.5 için ham C3 ve o günün öncesindeki lig bazını karıştır, MS aynen.
- C3_BETA80_N30, C3_BETA200_N30: aynı marketin ±5pp yakın geçmişini 80 veya 200 örneklik model yüzdesi öncülüyle yumuşat; n<30 ise C3 hamına dön.
- C3_LOGIT_2025_ONLY: 2025/26 sezonunda C3 ve yalnız geçmiş lig bazını kullanarak öğrenilmiş ayrı KG/2.5 L2 lojistik kalibratör.
- C3_BLEND_25_BETA80 ve C3_BLEND_25_LOGIT2025: %25 C3-lig karışımını diğer kalibratörle 50/50 birleştir, MS aynen.

## Günlere göre sınırları koruyan sonuçlar

### 2026_aug_oct_880_raw_M4 — 873 maç, 60 takvim günü

| Karar yöntemi | n | İsabet % | Öngörü % | Tek tercih Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|---:|---:|---:|
| RAW | 873 | 57.617 | 62.046 | 0.2395367 | 0.2447455 | 0.2458082 |
| C3_25_BASE_75 | 873 | 59.794 | 59.34 | 0.2335103 | 0.2430845 | 0.2411868 |
| C3_50_BASE_50 | 873 | 58.19 | 59.753 | 0.235704 | 0.2428119 | 0.2413736 |
| C3_BETA80_N30 | 873 | 60.252 | 60.113 | 0.2328853 | 0.2434561 | 0.2398934 |
| C3_BETA200_N30 | 873 | 60.137 | 60.403 | 0.2331571 | 0.2431206 | 0.2402071 |
| C3_LOGIT_2025_ONLY | 873 | 62.543 | 59.721 | 0.2315073 | 0.2425049 | 0.2397471 |
| C3_BLEND_25_BETA80 | 873 | 60.137 | 59.498 | 0.2331526 | 0.2427674 | 0.240082 |
| C3_BLEND_25_LOGIT2025 | 873 | 61.397 | 59.411 | 0.2314432 | 0.2426727 | 0.2403032 |

### 2026_aug_sep_587_raw_M4 — 580 maç, 41 takvim günü

| Karar yöntemi | n | İsabet % | Öngörü % | Tek tercih Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|---:|---:|---:|
| RAW | 580 | 57.586 | 61.679 | 0.238125 | 0.2437321 | 0.2451611 |
| C3_25_BASE_75 | 580 | 60.517 | 59.028 | 0.2307487 | 0.2426112 | 0.2399376 |
| C3_50_BASE_50 | 580 | 58.276 | 59.442 | 0.233656 | 0.2421762 | 0.2403975 |
| C3_BETA80_N30 | 580 | 61.552 | 59.802 | 0.2299604 | 0.2435475 | 0.2395803 |
| C3_BETA200_N30 | 580 | 60.345 | 60.089 | 0.2307509 | 0.2428474 | 0.2396794 |
| C3_LOGIT_2025_ONLY | 580 | 63.448 | 59.459 | 0.2291772 | 0.2421881 | 0.239227 |
| C3_BLEND_25_BETA80 | 580 | 61.034 | 59.186 | 0.2305382 | 0.2425843 | 0.239342 |
| C3_BLEND_25_LOGIT2025 | 580 | 62.069 | 59.127 | 0.2298985 | 0.242276 | 0.2394203 |

### 2026_oct_293_raw_M4 — 293 maç, 19 takvim günü

| Karar yöntemi | n | İsabet % | Öngörü % | Tek tercih Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|---:|---:|---:|
| RAW | 293 | 57.679 | 62.772 | 0.2423313 | 0.2467515 | 0.2470892 |
| C3_25_BASE_75 | 293 | 58.362 | 59.957 | 0.2389771 | 0.2440215 | 0.2436595 |
| C3_50_BASE_50 | 293 | 58.02 | 60.369 | 0.2397579 | 0.2440702 | 0.243306 |
| C3_BETA80_N30 | 293 | 57.679 | 60.728 | 0.2386754 | 0.2432751 | 0.2405132 |
| C3_BETA200_N30 | 293 | 59.727 | 61.023 | 0.2379202 | 0.2436616 | 0.2412518 |
| C3_LOGIT_2025_ONLY | 293 | 60.751 | 60.24 | 0.2361199 | 0.243132 | 0.2407766 |
| C3_BLEND_25_BETA80 | 293 | 58.362 | 60.114 | 0.238328 | 0.2431298 | 0.2415469 |
| C3_BLEND_25_LOGIT2025 | 293 | 60.068 | 59.972 | 0.2345011 | 0.243458 | 0.2420508 |

### 2026_sep_oct_621_frozen_MS — 615 maç, 39 takvim günü

| Karar yöntemi | n | İsabet % | Öngörü % | Tek tercih Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|---:|---:|---:|
| RAW | 615 | 56.423 | 62.48 | 0.2430819 | 0.2469734 | 0.2487955 |
| C3_25_BASE_75 | 615 | 57.073 | 59.777 | 0.2393923 | 0.2455656 | 0.2427994 |
| C3_50_BASE_50 | 615 | 56.26 | 60.163 | 0.2409298 | 0.245163 | 0.2433832 |
| C3_BETA80_N30 | 615 | 58.699 | 60.461 | 0.2365527 | 0.2444747 | 0.2416996 |
| C3_BETA200_N30 | 615 | 58.699 | 60.748 | 0.2373032 | 0.2445219 | 0.2424106 |
| C3_LOGIT_2025_ONLY | 615 | 59.512 | 60.129 | 0.2370109 | 0.2444877 | 0.2412567 |
| C3_BLEND_25_BETA80 | 615 | 57.398 | 59.88 | 0.2383277 | 0.2445026 | 0.2417599 |
| C3_BLEND_25_LOGIT2025 | 615 | 57.886 | 59.816 | 0.2371864 | 0.2449064 | 0.2418616 |

### 2026_oct_293_frozen_MS — 293 maç, 19 takvim günü

| Karar yöntemi | n | İsabet % | Öngörü % | Tek tercih Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|---:|---:|---:|
| RAW | 293 | 55.973 | 63.12 | 0.2447544 | 0.2467515 | 0.2470892 |
| C3_25_BASE_75 | 293 | 57.679 | 60.423 | 0.2391026 | 0.2440215 | 0.2436595 |
| C3_50_BASE_50 | 293 | 57.338 | 60.809 | 0.2401546 | 0.2440702 | 0.243306 |
| C3_BETA80_N30 | 293 | 58.02 | 61.166 | 0.2382444 | 0.2432751 | 0.2405132 |
| C3_BETA200_N30 | 293 | 59.727 | 61.448 | 0.2375097 | 0.2436616 | 0.2412518 |
| C3_LOGIT_2025_ONLY | 293 | 60.068 | 60.727 | 0.2358153 | 0.243132 | 0.2407766 |
| C3_BLEND_25_BETA80 | 293 | 58.02 | 60.578 | 0.2377407 | 0.2431298 | 0.2415469 |
| C3_BLEND_25_LOGIT2025 | 293 | 58.703 | 60.447 | 0.2350795 | 0.243458 | 0.2420508 |

### 2026_nov8_39_original_sha — 39 maç, 1 takvim günü

| Karar yöntemi | n | İsabet % | Öngörü % | Tek tercih Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|---:|---:|---:|
| RAW | 39 | 69.231 | 63.227 | 0.203286 | 0.2463668 | 0.247555 |
| C3_25_BASE_75 | 39 | 69.231 | 60.116 | 0.2038858 | 0.2453977 | 0.2388232 |
| C3_50_BASE_50 | 39 | 71.795 | 60.953 | 0.2049739 | 0.2447006 | 0.2403066 |
| C3_BETA80_N30 | 39 | 64.103 | 61.881 | 0.2236915 | 0.251205 | 0.2504106 |
| C3_BETA200_N30 | 39 | 66.667 | 62.132 | 0.2218855 | 0.2512956 | 0.2505435 |
| C3_LOGIT_2025_ONLY | 39 | 69.231 | 60.834 | 0.2053719 | 0.2460011 | 0.2449828 |
| C3_BLEND_25_BETA80 | 39 | 69.231 | 60.842 | 0.2092264 | 0.247715 | 0.2441096 |
| C3_BLEND_25_LOGIT2025 | 39 | 66.667 | 60.374 | 0.2083471 | 0.2455525 | 0.2417684 |

### 2026_sep_oct_nov_660_frozen_MS — 654 maç, 40 takvim günü

| Karar yöntemi | n | İsabet % | Öngörü % | Tek tercih Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|---:|---:|---:|
| RAW | 654 | 57.187 | 62.524 | 0.2407087 | 0.2469372 | 0.2487215 |
| C3_25_BASE_75 | 654 | 57.798 | 59.797 | 0.2372749 | 0.2455556 | 0.2425623 |
| C3_50_BASE_50 | 654 | 57.187 | 60.21 | 0.2387857 | 0.2451354 | 0.2431998 |
| C3_BETA80_N30 | 654 | 59.021 | 60.545 | 0.2357857 | 0.2448761 | 0.2422191 |
| C3_BETA200_N30 | 654 | 59.174 | 60.831 | 0.2363838 | 0.2449259 | 0.2428956 |
| C3_LOGIT_2025_ONLY | 654 | 60.092 | 60.171 | 0.2351241 | 0.244578 | 0.2414789 |
| C3_BLEND_25_BETA80 | 654 | 58.104 | 59.937 | 0.2365923 | 0.2446941 | 0.2419 |
| C3_BLEND_25_LOGIT2025 | 654 | 58.41 | 59.85 | 0.2354666 | 0.2449449 | 0.2418561 |

## Sorumlu kullanım kararı

En yüksek geçmiş isabet tek başına yetmez: aynı maçlarda eşleşmiş fark, gün-blok %95 aralık ve öngörülen yüzde-gerçekleşen oran uyumu birlikte değerlendirilir.
İlk iki olasılık arasında <=2 yüzde puanı varsa kesin üstünlük gibi gösterilmez; **YAKIN ADAYLAR** etiketiyle ikinci aday açıklanır. Otomatik PAS değildir.
Yeterli veri olmadığında model çıkışının olasılık doğruluğu garanti edilmez; veri olmadığı için başarı oranı uydurulmaz.
Önceki tekrar testleri nedeniyle sahte şekilde büyük sayıda bağımsız canlı mühür iddiası yoktur; 39 gerçek SHA tek gün.
Ana üretim kodu, günlük mühürler, xG sorunu, PDF, maç önü odds, iddaa ve otomasyonlar değiştirilmedi.
Detaylı ham JSON ve tüm paired bootstrap: 18_candidate_selector_result.json; kod: audit_best_choice_selector.py; bağımsız seçim API: choice_probability_shadow_v1.py.
