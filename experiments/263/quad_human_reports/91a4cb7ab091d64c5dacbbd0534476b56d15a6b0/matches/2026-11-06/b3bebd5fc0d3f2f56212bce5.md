# Futbol Maç Analiz Makinası 2.6.3 — TEKLİ MAÇ KARAR EKRANI

**Toulouse – Strasbourg** · 06.11.2026 22:45 TSİ · FRA1

**DENEYSEL, maç öncesi kayıt. Resmî bahis veya onaylı S1/S2 kararı değil.**

## 1. MAKİNENİN ANA KARARI — S2 / matematiksel değer

**PAS** · değerli ana seçim doğrulanamadı

**Alternatif tercih:** YOK

**Karar gerekçesi:** Güncel veya geçerli sabah oranı doğrulanamadı; EV/değer seçimi üretilemez

| Kontrol | Sonuç |
|---|---|
| S1 · yüksek olasılık | ONAYSIZ — araştırma uyarısı: 1.5 Üst 82,9% |
| S2 · matematiksel değer | PAS — değerli seçim doğrulanmadı |
| A/B/C tercih sınıfı | ONAYSIZ — bu kayıt §12.2 resmî sınıfı üretmedi |
| En olası MS (4 model medyanı, açıklayıcı) | MS 1 |
| M4 en olası MS | MS 1 38,8% |
| M4 en olası tek skor | 1-1 10,4% |
| Veri güveni | KISMİ — kaynak kabulü tüm maçların bağımsız teyidi değildir |
| İlk 11 / xG / sakatlık / hava / Elo | Bu dörtlü matematik kaydında etkileri doğrulanmadı |
| İlk yarı / maç sonu korner | Bu dört-model karar dosyasında hesaplanmadı |
| Oran / EV kanıtı | NO_VERIFIED_ODDS; NO_PRICE |
| Tahmin kilidi | 2026-11-06T19:11:50.958830+00:00 · SHA be375b7dba9cc265… |

**Önemli:** S2 PAS, açıklayıcı futbol tahmininin olmadığı anlamına gelmez. S1 araştırma uyarısı resmî GEÇTİ veya bahis tavsiyesi değildir.

---

## 2. AYRINTILI MATEMATİK, VERİ VE KAYNAK RAPORU


**2.6.3 DENEYSEL / MAÇ ÖNCESİ — resmî bahis veya kesin sonuç tavsiyesi değildir.**

Lig: FRA1 · Lig yerel tarihi: 2026-11-06
Türkiye başlama: 06.11.2026 22:45 (TSİ) · Başlama UTC: 2026-11-06T19:45:00+00:00
Tahmin kaydı UTC: 2026-11-06T19:11:50.958830+00:00
Resmî fikstür kaynağı: https://ligue1.com/fr/articles/l1_article_5839-
Fikstür kontrol UTC: 2026-11-06T19:11:53.045083+00:00

## A. Gerçek kaydedilmiş veriler
- Kaynak kabul sınıfı: **APPEND_ONLY_HUMAN_SOURCE_ATTESTED_NOT_INDEPENDENTLY_RECHECKED**. Bu sınıf bütün maçların bağımsızca yeniden doğrulandığını göstermez.
- Önceki lig maç sayısı: **387**; son kayıtlı sonuç: **2026-11-02**.
- xG/xGA, güncel sakatlık, cezalılar, ilk 11, hava durumu: **BU DÖRTLÜ KAYITLA DOĞRULANAMADI**. Ayrı kontrol yapılmış olabilir; burada uydurulmaz.

## B. B / C2 / C3 / M4 ayrı tahminleri
| Model | MS 1 | MS X | MS 2 | 2.5 Üst | KG Var | Beklenen gol λ ev/deplasman | En olası skor |
|---|---:|---:|---:|---:|---:|---:|---|
| B | 34,3% | 22,8% | 42,9% | 64,5% | 65,4% | 1,56/1,76 | 1-1 9,9% |
| C2 | 38,1% | 23,5% | 38,4% | 61,6% | 63,4% | 1,59/1,59 | — |
| C3 | 42,1% | 23,8% | 34,1% | 59,6% | 61,7% | 1,63/1,45 | 1-1 10,8% |
| M4 | 38,8% | 23,3% | 37,8% | 62,5% | 64,0% | 1,62/1,60 | 1-1 10,4% |

Model yüzdeleri basit ortalamayla birleştirilmez; geçmiş performans kalibrasyonu karar aşamasında ayrı değerlendirilir.

## C. Kalibre olasılıklar ve piyasa fiyatları
| Pazar | Modellerin medyanı* | Kalibre yüzde | Oran | EV | Gözlem zamanı | Eleme / değer durumu |
|---|---:|---:|---:|---:|---|---|
| MS 1 | 38,5% | 39,3% | — | — | Oran yok (—) | PAS / UNDER_3_MODEL_SUPPORT, LOW_CALIBRATED_LIFT, NO_SYNCHRONIZED_ODDS |
| MS X | 23,4% | 23,9% | — | — | Oran yok (—) | PAS / UNDER_3_MODEL_SUPPORT, LOW_CALIBRATED_LIFT, NO_SYNCHRONIZED_ODDS |
| MS 2 | 38,1% | 33,8% | — | — | Oran yok (—) | PAS / LOW_CALIBRATED_LIFT, NO_SYNCHRONIZED_ODDS |
| 1.5 Üst | 82,9% | — | — | — | Oran yok (—) | PAS / NO_POSITIVE_DEV_BRIER_SKILL, NO_SYNCHRONIZED_ODDS |
| 1.5 Alt | 17,1% | — | — | — | Oran yok (—) | PAS / UNDER_3_MODEL_SUPPORT, NO_POSITIVE_DEV_BRIER_SKILL, NO_SYNCHRONIZED_ODDS |
| 2.5 Üst | 62,0% | — | — | — | Oran yok (—) | PAS / NO_POSITIVE_DEV_BRIER_SKILL, NO_SYNCHRONIZED_ODDS |
| 2.5 Alt | 38,0% | — | — | — | Oran yok (—) | PAS / UNDER_3_MODEL_SUPPORT, NO_POSITIVE_DEV_BRIER_SKILL, NO_SYNCHRONIZED_ODDS |
| 3.5 Üst | 39,8% | 35,7% | — | — | Oran yok (—) | PAS / LOW_CALIBRATED_LIFT, NO_SYNCHRONIZED_ODDS |
| 3.5 Alt | 60,2% | 64,3% | — | — | Oran yok (—) | PAS / UNDER_3_MODEL_SUPPORT, LOW_CALIBRATED_LIFT, NO_SYNCHRONIZED_ODDS |
| KG Var | 63,7% | 57,3% | — | — | Oran yok (—) | PAS / LOW_CALIBRATED_LIFT, NO_SYNCHRONIZED_ODDS |
| KG Yok | 36,3% | 42,7% | — | — | Oran yok (—) | PAS / UNDER_3_MODEL_SUPPORT, LOW_CALIBRATED_LIFT, NO_SYNCHRONIZED_ODDS |

*Medyan betimleyicidir; kalibre karar yüzdesi yerine kullanılmaz.*

## D. En olası sonuç ve matematiksel değerlendirme
- En olası 1X2 (açıklayıcı dört-model medyanı): **MS 1**.
- Tek skor tahminleri her model satırında ayrı gösterildi; birleşik tek skor olasılığı uydurulmadı.
- Oran kanıtı: **NO_VERIFIED_ODDS**; sabah fiyatı: **NO_MORNING_ARCHIVE**.
- 1.5 Üst yalnız yüksek yüzde nedeniyle ana tercih yapılmaz. Model desteği, fiyat, EV ve kalibrasyon koşulları gerekir.

## E. Ana tercih / alternatif / PAS
- **Ana tercih:** PAS.
- **Alternatif (ayrı aile):** YOK.
- Nihai karar statüsü: **RESEARCH_PAS**.
- **PAS nedeni:** NO_MORNING_OR_CURRENT_ODDS.
- **PAS analiz yok demek değildir.** Fiyat olmasa da model olasılıkları yukarıda görünür.

## F. Kanıt ve sınırlamalar
- Tahmin SHA: be375b7dba9cc26582d04ad5cf4f05acc8a3ad16be59ff72df36947e979190cc
- Karar SHA: 4994f32e40bf089f8c62f990c4e9f7b53e59c9b017db364ed44c269380c98c04
- Tarihsel veri SHA: 1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9
- Güncel oran SHA: YOK
- Sabah oranı SHA: YOK
- Kaynak karar sınıfı: NO_PRICE
- Bu dosyada kaç simülasyon veya kaç başarı testi yapıldığına dair doğrudan kanıt yoksa sayı eklenmez.
