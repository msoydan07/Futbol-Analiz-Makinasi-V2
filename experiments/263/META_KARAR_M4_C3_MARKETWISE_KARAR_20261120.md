# Meta Karar Motoru 2.6.3 — sabit pazar uzmanı / dinamik uzman testi

**Durum: ARAŞTIRMA TAMAM, ANA SİSTEME TERFİ YOK.**
2026-11-20 tarihli kullanıcı isteği üzerine, ana M4, B/C2/C3 formülleri, orijinal SHA mühürlü tahminler, operasyondaki PAS/oran kodu ve xG politikası değiştirilmeden oluşturuldu.

## Deney tasarımı

- Veri: SHA sabitlenmiş **4.413 maçlık xG içermeyen** futbol geçmişi. Önceden var olan `chrono_goal_decision_263.py` yalnız önceki tarihli maçları kullanarak **880 retrospektif as-of** B/C2/C3/M4 tahminini yeniden oluşturdu.
- Geliştirme 587 maç (Ağustos–Eylül 2026), değerlendirme 293 maç (Ekim 2026). Ekim sonuçları daha önce de araştırılmıştır; bağımsız dokunulmamış test değildir.
- Tek modelden **MS 1-X-2 vektörü**, tek modelden **KG Var/Yok**, tek modelden **1.5/2.5/3.5 gol çizgileri** seçilir. Toplam %100, tamamlayıcılık ve gol çizgisi monotoniği `valid()` ile kontrol edilir.
- Sabit uzman: MS=M4, KG=C3, bütün gol çizgileri=C3.
- Dinamik uzman: en az 120 geçmiş **eşleşmiş** maç ve 10 farklı önceki tarih, global ve lig bazlı (ağırlığı en çok %50) önceki Brier avantajı, rakibe geçiş marjı 0.005. Aynı gün hiçbir geçmiş sonuç öğrenmeye girmez. Yetersiz veri durumunda sabit uzmana döner; destek yoksa PAS.
- Referanslar: tümü M4 ve tümü C3. Farkları aynı maçta değerlendirdik. Kalibrasyon ECE10 açıklayıcıdır, veri görülerek ek kalibrasyon yapılmadı.
- Bağımsız ikinci kontrol: **8 Kasım'dan önce mühürlenmiş 40 tahminden sonuç arşivinde skorlanan 39 maç**, 1 ertelenmiş maç hariç. Meta seçici yalnız **29 Ekim'e kadarki 880 retrospektif** geçmişi gördü; 8 Kasım skorlarına göre güncellenmedi.

## Ekim 293 maç sonucu (Brier; düşük iyi)

| Pazar | Tümü M4 | Tümü C3 | Sabit uzman | Dinamik |
|---|---:|---:|---:|---:|
| MS 1-X-2 | 0.585542 | **0.582332** | 0.585542 | 0.586019 |
| KG | 0.248779 | **0.246751** | 0.246751 | 0.246751 |
| Üst 1.5 | 0.164770 | **0.161629** | 0.161629 | 0.161629 |
| Üst 2.5 | 0.249303 | **0.247089** | 0.247089 | 0.247089 |
| Üst 3.5 | 0.243978 | **0.241309** | 0.241309 | 0.241309 |

Dinamik değişimler: MS'de 28/293 C3; KG 0, GOALS 0. Dinamik MS sabit M4'ten **0.000478 Brier daha kötü**. Sabit eksi dinamik, tarih-küme bootstrap %95 aralık **[-0.002723; +0.001459]**. 19 ayrı maç günü. Güven aralığı sıfırı kapsar.

## Mühürlü 8 Kasım sonuçları, 39 maç (Brier; düşük iyi)

| Pazar | Tümü M4 | Tümü C3 | Sabit uzman | Dinamik |
|---|---:|---:|---:|---:|
| MS 1-X-2 | **0.509959** | 0.517322 | 0.509959 | 0.511454 |
| KG | 0.248164 | **0.246367** | 0.246367 | 0.246367 |
| Üst 1.5 | 0.165231 | **0.159505** | 0.159505 | 0.159505 |
| Üst 2.5 | 0.262744 | **0.247555** | 0.247555 | 0.247555 |
| Üst 3.5 | 0.182749 | **0.174528** | 0.174528 | 0.174528 |

Dinamik değişimler: MS 4/39 C3; KG ve GOALS 0. Dinamik MS sabit M4'ten **0.001496 Brier daha kötü**. Bu test **tek maç günüdür**: güne göre bağımsız bootstrap belirsizliği üretilemez. 39 skorun **3'ü doğrudan TFF network-doğrulanmış**, 13 kulüp, 22 lig, 1 dış federasyon web-araştırması kaynaklıdır; web araştırması bağımsız doğrudan doğrulama demek değildir.

## Mühendislik kararı

1. **Sabit M4-MS / C3-KG-Üst hipotezi mantıklı araştırma başlangıcı.** 293 maç MS'de C3 az daha iyi iken 39 mühürlü maçta M4 daha iyi: dolayısıyla MS uzmanlığı kesinleşmedi.
2. Dinamik meta seçici geçmişe bakmadan karar verebiliyor, ancak **iki testte de sabit uzmana göre toplam MS Brier üstünlüğü göstermedi**. Bu nedenle canlı kullanıma terfi **HOLD**; geriye dönük eşik optimizasyonu yapılmadı.
3. Karar katmanındaki %100 MS toplam sorunu için doğru mimari ortaya kondu: MS vektörünü tek modelden almak. Mevcut `four_model_value_policy_263.py` **henüz değiştirilmedi**. Ayrıca 10 günlük veri tazelik koşulu aynen kaldı; bu çalışma ayrı konu.
4. Sonuçlar bahis önerisi, oran/EV/ROI onayı, bağımsız kör nihai tahmin testi değildir. Ana M4, eski pilot, otomasyonlar ve xG dosyaları değişmedi.

## Reprodüksiyon ve CI
- `experiments/263/meta_market_selector_263.py`
- `experiments/263/meta_market_selector_nov8_263.py`
- `experiments/263/test_meta_market_selector_263.py`
- `.github/workflows/263-meta-marketwise-research.yml`
- GitHub Actions: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44617490670 — başarılı.
