# Futbol Analiz Makinası 2.6.3 — B/C2 Market Kalibrasyonu ve Dört Model Seçim Kararı

**11 Kasım 2026. Karar: Aşama tamamlandı; üretim ve maç önü tahmin yüzdeleri değiştirilmedi.**

## 1. Gerçek çalışma, tekrar pilot değil

Önceden 4 Kasım'da üretilmiş **880 tarihsel as-of maç tahminini yeniden HESAPLAMADAN** GitHub Actions artifact `263-880-four-model-goals-PAS-RESEARCH-ONLY`, run `41836437930` içinden tekrar kullandık. CSV'nin SHA256 değeri **`dc674e2d05641eca27a8655eacfe6457e4140fb2adbdb0d9002b45e38cca1b3d`** eski `forward_dev_calibration_lock_263.json` dosyasıyla bire bir karşılaştırıldı.

- **Geliştirme:** Ağustos–Eylül 2026, **587 maç**.
- **Daha önce sonuçları incelenmiş değerlendirme:** Ekim 2026, **293 maç**.
- **Hiçbir M4/C3/B/C2 modeli yeniden fit edilmedi;** mevcut SHA maç önü tahminleri (6–8 Kasım), 99 skor arşivi, canlı seçim motoru, M4 ve telefon ekranları değiştirilmedi.
- Önceki C3/M4 **11 marketlik orijinal DEV kilidi matematiksel olarak tekrar hesaplanan DEV metrikleriyle bire bir uyuştu**. Mevcut lock aynen bırakıldı.
- **Bu 880 sonuç daha önce farklı araştırmalarda kullanıldı. Ekim 2026 bağımsız, yeni bir ileri tarihli kör test değildir.** Geçmişteki 96 hedef pilot ve 39 gerçek mühürlü maç ile karıştırılmadı.

## 2. B ve C2 veri yeterliliği

| Model | Ağustos–Eylül / 587 | Ekim / 293 | Not |
|---|---:|---:|---|
| **B** | **404** | **212** | DEV kalibrasyon hesaplanabilir, ancak pazar bazında geçmesi şart |
| **C2** | **0** | **105** | Açılış aylarında modelin as-of bağlamı yok; erken DEV'den ağırlık üretilemez |
| C3 | 580 | 293 | Orijinal kalibrasyon kilidi zaten var |
| M4 | 587 | 293 | Orijinal kalibrasyon kilidi zaten var |

**C2'ye erken dönemden bir kalibrasyon ağırlığı uydurulamaz.** Sonradan oynanmış Ekim veya Kasım maçlarından seçilen ağırlığı, Ağustos–Eylül'den öğrenilmiş gibi sunmak veri sızıntısı ve model seçimi yanlılığı olur.

## 3. B'nin 404 tarihsel geliştirme maçından çıkan pazar özel sinyali

Aynı olayın maç tarihi öncesi lig frekansı bazına karşı **ham B Brier skill** (pozitif daha iyi):

| B marketi | DEV n | Ham Brier skill / lig bazına göre | DEV salt araştırma büzüştürme ağırlığı | Model seçimi |
|---|---:|---:|---:|---|
| KG Var | 404 | **−%2,16** | 0,2175 | Kalibrasyon sinyali **YOK** |
| 2.5 Üst | 404 | **−%1,64** | 0,3550 | Kalibrasyon sinyali **YOK** |
| MS1 | 404 | +%12,74 | 0,9174 | Yalnız sınıf bazlı DEV araştırma |
| MSX | 404 | +%0,78 | 0,7899 | Yalnız sınıf bazlı DEV araştırma |
| MS2 | 404 | +%11,41 | 0,9174 | Yalnız sınıf bazlı DEV araştırma |

**MS1/X/2'nin tek tek ikili kalibrasyonunu** doğrudan üçlü 1X2 olasılığı diye sunamayız: ayrı ayrı kırpılan/büzüştürülen üç yüzde toplamı 1 olmayabilir. Normalizasyon ve kronolojik doğrulama olmadan B ile MS yönlendirmesi yapılamaz.

Ayrıca B/C3/M4 eski geliştirme ölçümlerinde 2.5 Üst'ün lig bazını sistematik yenememesi, yalnız yüksek yüzdeyi güvenilirlik veya değer sinyaline dönüştürmememiz gerektiğini doğruluyor.

## 4. Ekimde dört modelin AYNI tahmini verdiği 79 maç

**Brier düşük daha iyi.** Ekim sonuçları daha önce incelendiğinden burada yalnız tutarlılık/teşhis ölçümü.

| Model | KG Var/Yok Brier | 2.5 Alt/Üst Brier | MS 1/X/2 Brier |
|---|---:|---:|---:|
| B | 0,242209 | 0,240676 | 0,608328 |
| C2 | 0,252723 | 0,247198 | 0,609177 |
| **C3** | **0,238764** | **0,236227** | 0,600703 |
| M4 | 0,240750 | 0,237751 | **0,598060** |

B/C2/C3/M4'ün ayrı ayrı farklı maç sayılarıyla oluşturulmuş ham sıralamalarına bakılmadı; **sadece dördünün de bulunduğu 79 maç** kıyaslandı.

### Ekim C2'nin tek başına 105 maçlık eşleşmesi

C2−M4 Brier (negatif C2 lehine):
- KG: **+0,006676** (C2 kötü); gün bloklu keşifsel aralık **[−0,011237, +0,020707]**.
- 2.5 Üst: **−0,003097** (C2 daha iyi); aralık **[−0,024499, +0,015861]**.
- MS: **+0,009758** (C2 kötü); aralık **[−0,012581, +0,052520]**.
- C2'nin C3'e karşı KG farkı **+0,010263**; yani C3 daha iyi. Aralıkları sıfırı kapsıyor.

**Kilit bulgu:** Geçen hafta sonu 39 SHA-mühürlü maçta KG için C2 en iyi görünürken, Ekim'deki 79 ortak maçta C2 son sırada. Bu, tek haftanın kazananını otomatik motor yapan yaklaşımın neden riskli olduğunu somut gösteriyor. Her iki dönem de kesin üstünlük ispatı değildir.

### B'nin DEV büzüştürmesini Ekim 212 maçta sadece gölge karşılaştırma

| Market | Ham B Brier | DEV-ağırlıklı gölge Brier | O maçların lig bazı Brier | Gölge sonuç |
|---|---:|---:|---:|---|
| KG | 0,249775 | 0,246034 | 0,246710 | Bazdan %0,27 göreli daha düşük hata |
| 2.5 Üst | 0,253301 | 0,245971 | 0,246165 | Bazdan %0,08 göreli daha düşük hata |

Bu küçük kazanımlar **önceden keşfedilmiş Ekim verisinde**, **lig bazına çok yakın sonuçlar** ve farklı bağımsız tarihlerde doğrulanmış değil. Sadece `DEV'den öğrenilen shrinkage daha fazla zarar vermeyi önleyebilir` şeklinde sınırlandırılmış bir matematik gözlemidir. B'yi otomatik ana seçiciye almak için yeterli değil.

## 5. Son mühendislik kararı

1. **Ana matematikte mevcut M4 devam**; B/C2/C3 bağımsız karşı görüş olarak bırakılır. Tek hafta sonuna göre otomatik "KG'de C2", "Üst'te C3" kuralı koyulmaz.
2. **B ve C2 eski mevcut kalibrasyon kilidine eklenmez.** B'nin KG ve 2.5 Üst için ham DEV becerisi negatif; C2'nin o DEV döneminde tahmini sıfır.
3. **MS için B'nin sınıf-bazlı pozitif skill'i tek başına üç ihtimalli düzgün kalibrasyon anlamına gelmez.** 1X2 vektör toplamını koruyan yöntem ayrıca önceden kilitli kronolojik sınama gerektirir.
4. **2.5 Üst ve KG geliştirmesi**, yalnız yüzdesi yüksek diye veya son skorları görünce katsayı ekleyerek yapılamaz. Kullandığımız ayrı beklenen gol/dağılım deneyleri ve gelecek gerçek SHA tahminleri temel kanıttır.
5. **Piyasa seçimi:** Fiyatlar doğru zamanlı ve güvenilir biçimde mevcut değilse EV/no-vig değer iddiası yok, **PAS** gerekçesi korunur; 1.5 Üst'ün sırf yüksek ihtimaline dayanarak ana pazar seçimi yok.
6. **Bu araştırma bitti ve tekrar edilmeyecek.** Yeni pilot açılmıyor, eski 880/99/39 tekrar puanlanıp ayrı bir "kazanan" aranmıyor. Sıradaki somut teknik adım, *ya* MS için üçlü olasılık toplamını koruyan DEV-only kalibrasyon adayının daha önce çalışılmış deneylerde var olup olmadığını taramak, *ya da* kullanıcı analiz–fiyat–mühür–sonuç uçtan uca zinciri için eksik kabul testine odaklanmak. **Geçmiş sonuçlar sürekli test edilerek bağımsız başarı kanıtı üretilemez.**

## Kanıt

- [Başarılı GitHub Actions — 7/7 test, eski 880 SHA dosyası aynen kullanıldı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42997020834)
- [Salt araştırma analiz kodu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-b-c2-market-calibration-reuse-20261111/research/model_selection/b_c2_existing_880_market_calibration_audit_263.py)
- Eksiksiz model–market Brier/logloss, tarih bloklu karşılaştırma ve kilit kontrol JSON'u: aynı run içindeki `263-existing-880-B-C2-KG-O25-MS-dev-market-calibration-audit-only` artifact.

**Sınır:** GitHub CI'nin yeşil olması **geçmiş veriye dayalı hesap doğruluğunu** gösterir; otomatik piyasa seçicinin yeni maçta daha çok kazanacağını kanıtlamaz. M4/lock/main/aktif araştırma/telefon ve gerçek SHA mühürleri dokunulmaz.
