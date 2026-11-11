# 2.6.3 — Gerçek maç önü SHA mühürleriyle B/C2/C3/M4 pazar seçimi denetimi
**11 Kasım 2026 · Araştırma tamamlandı · Ana M4/telefon/pick/99 skor arşivi DEĞİŞMEDİ.**

## Mühendislik kararı

**İlk kez gerçek kaydedilmiş maç önü dört-model yüzdelerini, mevcut 99 maçlık sonuç arşivine güvenli şekilde eşleştirdik.** KG Var için C2, 2.5 Alt/Üst için C3, MS üçlü Brier için çok küçük farkla C3, aynı maçlardaki *tanımlayıcı* en düşük hataya sahip. **Yeni bir otomatik model-pazar seçim kuralına terfi ettirmek doğru değil.** 39 ortak maç ve üç takvim günü farklı maçlarda üstünlük göstermek için yeterli değil. **Mevcut kullanım kararı: M4 ana referans, B/C2/C3 yardımcı karşılaştırma; doğrulanmış güncel piyasa ve pozitif kalibrasyon yoksa araştırma PAS.**

## 96 iddiası ile depodaki gerçek kanıt aynı değil

Önceden "legacy96" olarak adlandırılan kohort **96 hedef aday** demektir; GitHub'da **96 bağımsız SHA-mühürlü ve skorla eşleşmiş maç bulunduğu** anlamına gelmez. Mevcut gerçek dosyalar tek tek SHA ve maç önü zaman damgasıyla doğrulandı:

| Kaynak sınıfı | Gerçek SHA mührü | 99 sonuç arşiviyle tam eşleşen | Dört model birlikte |
|---|---:|---:|---:|
| 6 Kasım, quad gerçek kayıt | 4 | 4 | 4 |
| 7 Kasım, ayrı kabul kohortu | 3 | 3 | 2 |
| 8 Kasım, new100 sabah mührü | 40 | 39 | 33 |
| **Toplam** | **47** | **46** | **39** |

- **Eşleşmeyen 1 kayıt:** 8 Kasım POR1, `forward_morning_263/2026-11-08/2ab937b233e1028fc8bc56b1.json`, SHA `48ad4e1f69f6768e8574cbec47160eef4aa33ada0d2b4ac7b284c1a26a6dc069`. 99 arşivinde **aynı lig+tarih+ev/deplasman iç kimliğiyle** tam skor yok; **sonuç veya skor uydurulmadı**.
- 46 eşleşmiş sonuç kaynağı: **15** resmî sayfa/sağlayıcı uyumlu, **17** doğrudan lig/kulüp sonuç sayfası, **14** ikincil/kısmen teyitli. Sonuçlar bugün bağımsız biçimde yeniden doğrulanmış değildir; her biri bu arşivin araştırma kanıt seviyesiyle değerlendirilir.
- 46 eşleşmiş maçta B **40**, C2 **45**, C3 **46**, M4 **46** maçta kullanılabilir; **eşit karşılaştırma için 39 ortak maç** esas alındı.
- Eski 7 Kasım 44 araştırma maçını, 8 Kasım 42 aday denemesini veya 99 bitmiş maçı **geriye dönük yeni mühür** gibi sunmadık.

## Aynı 39 gerçek mühürlü karşılaşmada dört modelin üç pazar ailesi

**Brier düşük daha iyi. 2'li KG ve 2.5 Alt/Üst Brier ile 3'lü MS Brier doğrudan "pazar kârlılığı" kıyası değildir.**

| Model | KG Var/Yok Brier | 2.5 Alt/Üst Brier | MS 1/X/2 Brier |
|---|---:|---:|---:|
| B | 0,229651 | 0,258109 | 0,561238 |
| **C2** | **0,219127** | 0,246525 | 0,544387 |
| C3 | 0,232141 | **0,245379** | **0,540185** |
| M4 | 0,231230 | 0,254719 | 0,541054 |

Aynı 39 maçta en olası sonuç yönünün doğru çıkma sayıları:

| Model | KG Var/Yok (39) | 2.5 Alt/Üst (39) | MS 1/X/2 (39) |
|---|---:|---:|---:|
| B | 25 | 19 | 23 |
| C2 | **27** | **24** | 21 |
| C3 | 20 | 22 | 23 |
| M4 | 21 | 22 | **24** |

**Yorum:** C2 bu küçük örnekte KG'de daha iyi, hatta 2.5 Alt/Üst'te C3'e çok yakın. MS olasılık hatasında C3 ile M4 arasındaki fark **0,000869 Brier** kadar küçük; bu, yeni sürüm seçmek için neden olamaz. En yüksek doğru MS sayısı M4'te. İki farklı "başarı" ölçüsü birbirine karıştırılmamalı.

Örneğin KG'de C2−M4 Brier **−0,012102**, 2.5 Alt/Üst'te **−0,008193**; MS'de **+0,003333**. Sadece mevcut eşit 39 maç için geçerli farklar; 3 gün olduğundan güvenilir gün-kümeli belirsizlik aralığı yok.

### Neden 46 maçlık genel tabloyu model sıralamasında kullanmadık?

Eksik model sayıları farklıdır. 46 maçın hepsinde B 40, C2 45, C3 ve M4 46 sonuç üretmiştir. Bu yüzden 46 maçtaki ham Brier ortalamalarını doğrudan karşılaştırmak **farklı maç kümesi sorununa** yol açar. Hangi modelin doğru olduğunu ilan edeceğimiz yer 39 ortak maç olmak zorunda; o sayı da şimdilik sınırlı.

## Asıl teknik açık: gelecekteki maçta hangi model hangi pazar için seçilebilir?

Mevcut `experiments/263/four_model_value_policy_263.py` karar zincirini ve `experiments/263/forward_dev_calibration_lock_263.json` kilit dosyasını kontrol ettik.

Bu karar mekanizması, dört modelden gelen olasılıkları tanımlayıcı olarak gösterse de **kalibrasyon çapası seçerken yalnız C3/M4'e bakıyor**; B/C2 dev-kanıtlı seçim ağırlıkları bu kilitte yok. Maçtan sonra 39 sonuçta C2'nin KG performansı iyi diye C2'yi sessizce üretime atamak **veri sızıntısı/aşırı uyum** riski olur.

Önceden dondurulmuş geliştirici kalibrasyonundaki `development_brier_skill` değerleri:

| Pazar | C3 geliştirme Brier skill | M4 geliştirme Brier skill |
|---|---:|---:|
| KG Var/Yok | **+0,000504** | −0,000707 |
| 2.5 Alt/Üst | **−0,018284** | **−0,023676** |
| MS1 | +0,113743 | +0,114610 |
| MSX | +0,008551 | +0,003732 |
| MS2 | +0,112613 | +0,106275 |
| 1.5 Alt/Üst | −0,006775 | −0,008437 |

- Bu sayıların **pozitif** olması yalnız geliştirme dönemindeki ilgili referansın üstünde sinyal gösterdiğini belirtir, bahis değeri veya kâr garantisi değildir.
- 2.5 Alt/Üst'te **hem C3 hem M4 için negatif** olduğundan mevcut politika bu aileye otomatik kalibrasyon onayı veremez. Tam da güçlendirmek istediğimiz pazarın öncelikli matematik/kalibrasyon ihtiyacı buradadır.
- C2/B'nin bu kilitte olmaması, bu modellerin işlevsiz olduğu anlamına gelmez; **otomatik piyasa-pazar yönlendirmesi için dev kanıtının burada eksik** olduğu anlamına gelir.
- Senkronize ve doğrulanmış fiyat bulunmazsa mevcut value policy **PAS** verir; sırf yüksek görünen 1.5 Üst yüzdesini otomatik ana tercih yapmayız.

## Sonlu aksiyon kararı (yeni pilot açmadan)

1. **Öncelik:** B ve C2'nin KG/2.5/MS için *daha önce sonuçlarına bakılmamış* aynı gelişim kesitlerinde, as-of ve gerçek veri kaynağıyla kalibrasyonunu **bağımsız araştırma kilidi** olarak değerlendir. Önceden denenmiş 39 maçtan çıkan kazançla otomatik parametre seçme.
2. **Karar kapısı:** Mevcut M4/C3 karşılaştırmasını koru; B/C2'yi ancak tutarlı farklı-tarihli kalibrasyon ve sonra yeni maçlar gösterirse aday seçim listesine ekle. Uydurma canlı piyasa fiyatı, kazanç oranı veya zoraki ana tercih yok.
3. **Ekran:** Kullanıcıya her maç için MS1/X/2, KG Var ve 2.5 Üst yüzdelerini orijinal kaynaklarıyla göster. Ana tercih + alternatif + PAS mantığı aynı kalsın. **1.5 Üst'ün sırf yüksek % olduğu için seçilmesine izin verme**; M4'ün mevcut matematiği veya mobil ekranı bu çalışmada değişmedi.
4. **Test statüsü:** İş bitti: **47 SHA doğrulandı, 46 bire bir skorla eşleşti, 39 dört-model ortak karşılaştırma tamamlandı**. Bu rapor aynı pilotu tekrar tekrar çalıştırmak için bahane değildir.

## GitHub kanıtı

- [Gerçek GitHub Actions — 7/7 PASS; SHA doğrulama, eşit maç 4-model Brier/logloss](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42990485576)
- [Tek dosya gerçek karşılaştırma kodu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-sealed-legacy96-paired-market-audit-20261111/research/model_selection/legacy96_sealed_4model_market_pair_audit_263.py)
- Actions artifact `actual-sealed-legacy96-cohorts-4model-btts-over25-ms-only-research`: tüm 46 eşleşmenin orijinal SHA, skor sınıfı ve dört model pazar hatası, 1 eşleşmeyen kayıt.
- **Dokunulmayanlar:** `main`, `experiment/263-toplu-karsilastirma`, orijinal B/C2/C3/M4 ve dev kilit, eski SHA tahmin dosyaları, 99 skor havuzu, bahse dönük seçimler, LITE/basketbol.

**Mühendislik hükmü:** Makine ana M4 ile kullanılır, yeni otomatik model yönlendirmesi kurulmaz. **Sonraki gerçekten değerli tek iş, B/C2'nin pazar-özel kalibrasyon ve yeterli tarihlerle yanlışsız as-of kıyasıdır**; eski 96 hedef sayısına bakıp yeni pilot ilan etmek değil.
