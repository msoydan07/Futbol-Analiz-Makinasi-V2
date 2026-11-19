# 20 Kasım 2026 — C3 KG ve 2.5 Alt/Üst tek kalibrasyon kararı

## Önceki kilitli karar — DEĞİŞMEDİ
D-MARKET-006: İddaa sabah PDF oranları **yalnız beşinci referans**. Modelin ana/alternatif/PAS seçimi ve tahmin matematiği oranlardan bağımsızdır.
D-ODDS-001: İki iddaa PDF, **tek sabah tahmin mührü**; ikinci PDF yalnız fiyat hareketi ve kanıtlı ilk 11/rotasyon değerlendirmesi.
20 Kasım sabit uzmanları: **MS=M4 (tek üçlü)**, **KG ve 2.5 Alt/Üst=C3**. Ana M4, C3 matematiği ve eski SHA mühürlü tahminler değiştirilmez.

## Ölçüm — ağırlıkları sonuca bakarak yeniden öğrenmedik
- Kaynak: orijinal SHA-dondurulmuş 4.413 sonuç ve 2026 Ağustos–Ekim tarihli, yalnız geçmişi gören yeniden oluşturulmuş 880 tahmin. Geliştirme 587 maç (C3 için 580 mevcut), Ekim 293 retrospektif maç. Ekim önceden de incelenmiş olduğundan kör bağımsız nihai test **değildir**.
- Ayrı değerlendirme: 8 Kasım 2026'da **maç başlamadan SHA mühürlenmiş** 40 kayıttan 39 sonuçlanmış maç. Sonuç arşivi 3 TFF doğrudan ağ, 13 kulüp web, 22 lig web, 1 dış federasyon web araştırma düzeyindedir; 39'u da doğrudan bağımsız federasyon teyitli değildir.
- Donmuş geliştirme kalibratörü: `experiments/263/forward_dev_calibration_lock_263.json` (SHA `8ebed4a8b2d795935217826012e3ea5d2211d3d8503b29318266f10a2d09ceb5`); **KG Var ve Yok aynı 0.5083407177 ağırlık**, **2.5 Üst/Alt aynı 0.3113038451 ağırlık**.
- Dönüşüm: `q=geçmiş_lig_frekansı + w × (C3_ham − geçmiş_lig_frekansı)`. Bu geçmiş lig frekansı mutlaka hedef maçın **öncesinde** hesaplanmış olmalı; fiyat, gelecekteki maç skoru veya son 11 bu hesapta yer almaz. q ve 1−q tamamlayıcıdır.

## Sonuç — Brier (DÜŞÜK İYİ)

| Dönem | Pazar | C3 ham | C3 kalibre (dondurulmuş) | Geçmiş frekans |
|---|---|---:|---:|---:|
| Aug–Eyl / C3 n=580 | KG Var/Yok | 0.24373207 | **0.24217560** | 0.24385487 |
| Aug–Eyl / C3 n=580 | 2.5 Alt/Üst | 0.24516114 | **0.23993180** | 0.24075908 |
| Ekim / n=293 | KG Var/Yok | 0.24675147 | **0.24408670** | 0.24483395 |
| Ekim / n=293 | 2.5 Alt/Üst | 0.24708916 | **0.24343433** | 0.24550978 |
| 8 Kasım SHA / n=39 | KG Var/Yok | 0.24636679 | **0.24469490** | 0.24711512 |
| 8 Kasım SHA / n=39 | 2.5 Alt/Üst | 0.24755500 | **0.23905485** | 0.23876690 |

Aynı dönemlerde dondurulmuş kalibrasyon **log-loss'u da düşürdü**. ECE10 görünür kalibrasyon hatası Ekim KG'de 0.055551→0.028395, 2.5'te 0.084842→0.064459; Kasım KG'de 0.188554→0.103548 ve 2.5'te 0.154457→0.094863. ECE on-bin, örnekleme duyarlı yalnız açıklayıcı ölçüdür.

### Belirsizlik
Ekim için **eşleşmiş maç günü blok bootstrap %95** ham eksi dondurulmuş Brier farkı:
- KG: ortalama +0.00266477, güven aralığı **[−0.00246869; +0.00996143]**.
- 2.5: ortalama +0.00365483, güven aralığı **[−0.00509523; +0.01641177]**.

İki aralık da sıfırı kapsar. Kasım yalnız **bir maç günü** olduğu için geçerli gün-blok belirsizlik sınırı yoktur. Dönemler için testten **önce** tanımlanan terfi koşulumuz, Ekim gün-blok %95 alt sınırının pozitif olması + Ekim ve Kasım Brier/logloss iyileşmesidir. İkinci şartlar başarılı, **istatistiksel ilk şart başarısız**. Terfiyi sonuçlara bakarak gevşetme yok.

## KESİN MÜHENDİSLİK KARARI
1. **KG ve 2.5 uzmanlığı C3'te KALIR.**
2. Frozen C3 kalibrasyonu **umut verici ve ölçüldü**, fakat bilimsel üstünlüğü yeterince belirgin olmadığından **ana karar yüzdelerine TERFİ YOK**. Model-first seçici hâlâ önceki ham C3 değerini kullanır. Ana/alternatif/PAS kurallarını, M4'ü, eski testleri veya xG politikası değiştirmeyiz.
3. Aynı ilk İddaa PDF'nin **mevcut SHA zincirinin içine eklenen bir ARAŞTIRMA GÖLGESİ**: `c3_calibration_shadow_263.py`. Kendi SHA'sı ve referans verdiği eski SHA'lar vardır; ham C3 ve frozen kalibrasyon yan yana gösterilir; `selection_changed=false`, `pas_changed=false`, `do_not_use_to_pick=true` zorunludur. Yeni tahmin mührü veya yeni pilot değildir.
4. Eksik/bozuk gölge kalibrasyonu **modelin ana tahminini PAS'a dönüştürmez**. Sahte takım/sonradan değiştirilmiş ilk PDF/yanlış SHA ise eski resmî kimlik doğrulama tarafından **teknik engel** sayılmaya devam eder. İkinci PDF yalnız futbol açıklaması, model refit veya yeniden seçim **YOK**.
5. Mevcut otomatik maç sonu kontrolünde zaten mühürlenen sonraki gerçek maçlar gözlenirken dondurulmuş kalibrasyonun Brier/log-loss üstünlüğünü izleyebiliriz. **Yeni pilot talebi veya tekrar tarihsel parametre araması YOK.**

## Kanıt ve tekrar üretim
- Hesaplama: `experiments/263/c3_kg_o25_calibration_review_263.py`
- SHA gölge: `experiments/263/c3_calibration_shadow_263.py`
- Güvenlik: `test_c3_kg_o25_calibration_review_263.py`, `test_c3_calibration_shadow_263.py`.
- Girdi: imzalı 4.413 orijinal arşiv GitHub Actions varlık SHA'sı `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- Pipeline: `.github/workflows/263-c3-kg-o25-calibration-research.yml`.
- 2 PDF gerçek maç günü saha testi bu CI'ın bir parçası **değildir**. Karar defteri D-ODDS-001 / D-MARKET-006'ya bak; oran kaynakları yeniden tartışmaya açılmaz.

Durum: **A (karar) kapandı, B (araştırma ve koruma) kodlandı, C (kalibrasyon üretim terfisi) verilmedi.**
