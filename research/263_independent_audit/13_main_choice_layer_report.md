# 2.6.3 ana tercih karar katmanı — aktif MS kalibrasyonunu koruyan kontrol

**Sınırlar:** Sadece araştırma dalı, mevcut 10 lig; xG ve piyasa oranı kullanılmadı. Bütün eski SHA, aktif kod, lock ve PDF dokunulmadı.
Ağustos 2026'da öğrenilen M4 ortak MS kalibrasyonu geçerli tarih kullanımı açısından Ağustos'ta değerlendirilmedi. Eylül-Ekim orijinal SHA doğrulanmış tarih öncesi rekonstrüksiyon; yeni canlı mühür değildir.
Bu geçmiş dönemlerde sonuçlar daha önce görüldüğü için yeni bağımsız kör test denemez. 8 Kasım 39 orijinal SHA ayrıca test edildi; tek gün sonuçları kesin kanıt değildir.
Üretim kodu geçmiş 39 maçın benzer market olasılıklarından sınırlı güvenilirlik skoru hesaplar. Bu 39 sonuç Eylül-Ekim için **gelecek veridir**, dolayısıyla bu geçmiş günlere uygulanıp başarı uydurulmadı. Test edilen LIVE_SHAPED aktif kararın **M4 August MS + C3 RAW KG/O25 ham-yüzde sıralama parçasıdır**; 39 SHA tarihsel sıralama bileşenini kapsamaz.

## Maç başına tek olay — özet

| Dönem | Kural | n | İsabet % | Tahmini ort % | Seçim Brier | 2pp içinde iki tercih % |
|---|---|---:|---:|---:|---:|---:|
| september | RAW_M4_MS_C3_BINARY | 322 | 56.83 | 61.55 | 0.242421 | 33.85 |
| september | M4_AUG_JOINT_MS_C3_RAW_BINARY | 322 | 56.83 | 61.9 | 0.24156 | 30.12 |
| september | M4_AUG_JOINT_MS_C3_025_BINARY | 322 | 56.52 | 59.19 | 0.239656 | 42.55 |
| september | M4_AUG_JOINT_MS_LEAGUE_BINARY | 322 | 55.59 | 59.57 | 0.239164 | 38.51 |
| october | RAW_M4_MS_C3_BINARY | 293 | 57.68 | 62.77 | 0.242331 | 30.72 |
| october | M4_AUG_JOINT_MS_C3_RAW_BINARY | 293 | 55.97 | 63.12 | 0.244754 | 30.72 |
| october | M4_AUG_JOINT_MS_C3_025_BINARY | 293 | 57.68 | 60.42 | 0.239103 | 42.66 |
| october | M4_AUG_JOINT_MS_LEAGUE_BINARY | 293 | 59.73 | 60.74 | 0.238619 | 40.27 |
| sept_october | RAW_M4_MS_C3_BINARY | 615 | 57.24 | 62.13 | 0.242378 | 32.36 |
| sept_october | M4_AUG_JOINT_MS_C3_RAW_BINARY | 615 | 56.42 | 62.48 | 0.243082 | 30.41 |
| sept_october | M4_AUG_JOINT_MS_C3_025_BINARY | 615 | 57.07 | 59.78 | 0.239392 | 42.6 |
| sept_october | M4_AUG_JOINT_MS_LEAGUE_BINARY | 615 | 57.56 | 60.12 | 0.238904 | 39.35 |
| nov8_sha | RAW_M4_MS_C3_BINARY | 39 | 66.67 | 62.67 | 0.212814 | 43.59 |
| nov8_sha | M4_AUG_JOINT_MS_C3_RAW_BINARY | 39 | 69.23 | 63.23 | 0.203286 | 41.03 |
| nov8_sha | M4_AUG_JOINT_MS_C3_025_BINARY | 39 | 69.23 | 60.12 | 0.203886 | 51.28 |
| nov8_sha | M4_AUG_JOINT_MS_LEAGUE_BINARY | 39 | 69.23 | 60.1 | 0.207472 | 51.28 |

## Aynı maç eşleştirme, belirsizlik

Bütün kararlarda aynı geçmiş maçlardan tek olay alınır; farklı olay seçildiğinde doğru/yaklış ve Brier farkı ayrı değerlendirilir. Bootstrap gün bazlıdır. Çoklu araştırma yapıldığı için tam bağımsız nihai üstünlük iddiası yoktur.

### sept_october

- M4_AUG_JOINT_MS_C3_RAW_BINARY: {'n': 615, 'days': 39, 'hit_delta_pp': 0.0, 'selected_brier_improvement': 0.0, 'choice_flip': {'same_event': 615, 'same_family': 615}, 'hit_delta_95_pp': [0.0, 0.0], 'brier_improvement_95': [0.0, 0.0]}
- M4_AUG_JOINT_MS_C3_025_BINARY: {'n': 615, 'days': 39, 'hit_delta_pp': 0.6504, 'selected_brier_improvement': 0.0036896, 'choice_flip': {'same_event': 369, 'same_family': 387, 'different_event': 246, 'different_family': 228}, 'hit_delta_95_pp': [-2.977, 4.7619], 'brier_improvement_95': [-0.0041797, 0.0125826]}
- M4_AUG_JOINT_MS_LEAGUE_BINARY: {'n': 615, 'days': 39, 'hit_delta_pp': 1.1382, 'selected_brier_improvement': 0.0041774, 'choice_flip': {'different_event': 325, 'different_family': 274, 'same_event': 290, 'same_family': 341}, 'hit_delta_95_pp': [-2.5896, 6.0086], 'brier_improvement_95': [-0.0050598, 0.0149958]}
### october

- M4_AUG_JOINT_MS_C3_RAW_BINARY: {'n': 293, 'days': 19, 'hit_delta_pp': 0.0, 'selected_brier_improvement': 0.0, 'choice_flip': {'same_event': 293, 'same_family': 293}, 'hit_delta_95_pp': [0.0, 0.0], 'brier_improvement_95': [0.0, 0.0]}
- M4_AUG_JOINT_MS_C3_025_BINARY: {'n': 293, 'days': 19, 'hit_delta_pp': 1.7065, 'selected_brier_improvement': 0.0056518, 'choice_flip': {'same_event': 182, 'same_family': 192, 'different_event': 111, 'different_family': 101}, 'hit_delta_95_pp': [-4.0, 10.3448], 'brier_improvement_95': [-0.0074882, 0.0249693]}
- M4_AUG_JOINT_MS_LEAGUE_BINARY: {'n': 293, 'days': 19, 'hit_delta_pp': 3.7543, 'selected_brier_improvement': 0.0061353, 'choice_flip': {'different_event': 155, 'different_family': 128, 'same_event': 138, 'same_family': 165}, 'hit_delta_95_pp': [-2.9126, 14.5631], 'brier_improvement_95': [-0.0092083, 0.0287139]}
### nov8_sha

- M4_AUG_JOINT_MS_C3_RAW_BINARY: {'n': 39, 'days': 1, 'hit_delta_pp': 0.0, 'selected_brier_improvement': 0.0, 'choice_flip': {'same_event': 39, 'same_family': 39}}
- M4_AUG_JOINT_MS_C3_025_BINARY: {'n': 39, 'days': 1, 'hit_delta_pp': 0.0, 'selected_brier_improvement': -0.0005997, 'choice_flip': {'different_event': 11, 'same_family': 29, 'same_event': 28, 'different_family': 10}}
- M4_AUG_JOINT_MS_LEAGUE_BINARY: {'n': 39, 'days': 1, 'hit_delta_pp': 0.0, 'selected_brier_improvement': -0.0041855, 'choice_flip': {'different_event': 14, 'same_family': 30, 'same_event': 25, 'different_family': 9}}

## Karar mantığı

1. MS1/MSX/MS2 tek bir kalibre edilmiş M4 olasılık dağılımından gelir; KG ve 2.5 ayrı aile olasılıklarıdır. En yüksek % doğrudan kıyaslandığında aileler farklı kalibrasyona sahipse sıralama yanlı olabilir.
2. Ana tercih öncesi her olayın aynı tarihe göre kalibre edilmiş gerçekleşme ihtimali gerekir. En çok hesaplanan değil, en çok **gerçekleşmesi beklenen** olay seçilmelidir.
3. İlk iki adayın puan farkı çok dar olduğunda sonuçlar beraberlik içinde sayılmalı; bu güveni artırmaz. Mevcut ana tercih sessizce değiştirilmez.
4. 39 tek-gün önceden mühürlü maç 7 bağımsız piyasa kanıtı değildir; gerçek mühür ve maç günü bağımsız doğrulama yayıldıkça aynı döneme ait eski maçları geriye dönük olarak kullanmak yasaktır.
5. Bu karar katmanı araştırması bahis kârlılığı değil, olasılık sıralaması araştırmasıdır.

JSON: 12_main_choice_layer_result.json. Kaynak: audit_main_choice_layer.py.
