# 20 Kasım 2026 — İkinci mühendis denetimi: 293 maçlık kapsam eksikliğinin giderilmesi

## Düzeltme ve kapsam
Kullanıcının eleştirisi yerindedir: ilk bağımsız çalışma yalnız 293 Ekim maçını aynı dönem test karşılaştırması olarak aldı. Orijinal 4.413 maçın daha erken 2025/26 sezonu geniş ve tarih sıralı incelenebilirdi. Bu inceleme **ek olarak yapıldı**: 2026/27'nin önceden çalışılmış 880 maçı yeniden işletilmedi, 2025/26'nın 3.533 satırı ilk kez tam tarih bazlı B/C3/M4 ve sabit matematiksel alternatifler için prequential tarandı.

GitHub Actions: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44809963151 (başarılı).

**Kaynak:** orijinal 4.413 maç 10 lig; veri SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1` eşleşti. 2025/26 **3.533** maçın **611**'i, her ligde en az 60 daha önce oynanmış maç olmadığından dürüstçe başlangıç eğitim örneklemi oldu; **2.922** maç yalnız önceki günlere ait bilgiden değerlendirmeye girdi. **702** bu 2.922 maç, orijinal M4 hiperparametre geliştirme tarih bloklarının içindeydi; **2.220** maç bu tarih bloklarının dışındaydı.

**Birleştirilmiş tarihsel kapsam:** 2025/26'dan bu turda incelenen **2.922** + daha önce tarih sıralı incelenen 2026/27 **880** = **3.802** tarih bazlı model değerlendirme maçı. Bu 3.802'nin hepsi aynı bağımsız kör test veya her yöntem için eşit kapsam değildir. M4, 2025/26 sezonunun bazı bloklarıyla ayarlanmış olduğundan **2.922'nin hiçbiri mutlak kör final test diye gösterilmez**.

2025/26'da **C2 çıkmaması beklenen bir sınırdır**: ana C2 modelinin gerekli önceki sezonu (2024/25) orijinal 4.413 veri kaynağında bulunmuyor. Başka arşivden 2024/25 skorlarını sessizce karıştırmadık.

## 2025/26 binlerce maçın yeni bulguları
Tabloda ölçümler farklı kapsamalara sahiptir; her marketi aynı model için karşılaştırırken **eşleştirilmiş gün-blok farkları** da aşağıda verilmiştir. MS Brier 3 sınıfın toplamıdır; KG/2.5 ikili Brier.

| Yöntem | Maç | MS Brier | KG Brier | 2.5 Alt/Üst Brier |
|---|---:|---:|---:|---:|
| Geçmiş lig olay frekansı | 2.922 | 0,655071 | **0,246342** | **0,248558** |
| B | 2.549 | 0,621717 | 0,253144 | 0,256504 |
| C3 | 2.898 | 0,612732 | 0,251771 | 0,254894 |
| M4 | 2.919 | 0,612355 | 0,253779 | 0,256044 |
| C3+M4 yarı yarıya | 2.898 | 0,614039 | 0,252772 | 0,255847 |

**Önemli uyarı:** 2025/26'nın ham KG ve 2.5 sonuçlarında hem C3 hem M4, basit geçmiş lig frekansı tahmininden daha kötü görünüyor. MS'de ise tersine C3 ve M4, yalnız lig frekansından anlamlı ölçüde daha bilgilendirici. Bu, modelin **MS için rakip/takım sinyali yararlı olabilirken KG/2.5'te belirsiz yüzdeleri fazla kesin sunduğu** ihtimalini güçlendiriyor.

### Geliştirme tarih blokları hariç 2.220 maç
Orijinal M4 ayar seçiminde kullanılmış 702 tarih-blok maçını sonuç duyarlılığından ayırdık. Aynı maçlarda eşleştirilmiş, tarih-günü bazlı 800 bootstrap ile:

- **MS, C3 - M4:** M4 referans eksi C3 farkı **+0,004193**, %95 **[+0,002636; +0,005989]**, 2.201 ortak maç. C3 lehine; ancak 2025/26 sezonundan model ayarı seçildiği için bağımsız nihai üstünlük değildir.
- **KG, C3 - M4:** M4 eksi C3 **+0,002027**, %95 **[+0,001072; +0,002960]**, 2.201 ortak maç: C3 lehine.
- **2.5, C3 - M4:** M4 eksi C3 **+0,001883**, %95 **[+0,000544; +0,003257]**, 2.201 ortak maç: C3 lehine.
- **KG lig frekansı - C3:** C3 eksi lig referansı **+0,005370**, %95 **[+0,001626; +0,009690]**, 2.201 ortak maç: lig frekansı lehine.
- **2.5 lig frekansı - C3:** C3 eksi lig referansı **+0,006666**, %95 **[+0,002888; +0,010998]**, 2.201 ortak maç: lig frekansı lehine.

Bunlar **çoklu test düzeltmeli ve bağımsız kör p-değerleri değildir**. Birçok hipotez zaten önceki aylarda görülmüştür.

### "Bir maç için en olası yedi olaydan biri" araştırma seçimi
Her maçta yalnız bir MS1/MSX/MS2, KG Var/Yok veya 2.5 Üst/Alt olayı seçildi. Alt tablodaki isabet oranları farklı olayları değerlendirebildiğinden *modelin aynı olaya karşı eşleştirilmiş düzgün skorunun yerine geçmez*.

| Araştırma seçicisi | Kapsam | Gerçekleşen isabet | Ortalama bildirilen güven |
|---|---:|---:|---:|
| Tarih öncesi lig frekansı | 2.922 | %55,17 | %56,77 |
| B ham | 2.549 | %55,24 | %62,45 |
| C3 ham | 2.898 | %56,90 | %62,46 |
| M4 ham | 2.919 | %56,66 | %63,80 |
| C3/M4 karışımı | 2.898 | %57,11 | %62,96 |

Ham M4'te **%63,80 güvene karşı %56,66 gerçekleşme** ve C3'te **%62,46 güvene karşı %56,90 gerçekleşme**, yalnız Ekim'e özgü olmayan bir **aşırı güven/kalibrasyon riski** işaretidir.

## Matematiksel alternatif ve karar
Dixon–Coles, bivariate ve negatif binomun sabit dağılım düzeltmelerinin 2025/26'nın geniş örnekleminde de KG/2.5'te C3 veya lig frekansını belirgin olarak geçtiği görülmedi. 2025/26'da negatif binomun k=3 sürümünün KG Brier'i **0,267235**, C3 **0,251771**: burada özellikle olumsuz.

Önceki Ekim araştırmasında C3/MS, kalibrasyonlu C3/KG ve 2.5, lojistik/2.5 olumlu görünmüştü. 8 Kasım 39 mühürde M4/MS öne geçmişti. 2025/26'nın büyük örneklemi yeni, değerli bir bulgu ekledi: **KG ve 2.5'te basit tarihsel lig oranları, ham Poisson modellerinden daha doğru çıkabiliyor.** Bunun uygulamaya dönüşmesi için sonradan model seçme yanlılığına düşmeden tarih öncesi dondurulmuş kalibrasyon/lig frekansı harmanını mevcut yeni mühürlerin sonuçlarında karşılaştırmak gerekir. Bu çalışma **yeni pilot açma** çağrısı değildir.

**Karar: üretim değişikliği yapılmadı**; mevcut modeller ve mühürler korunuyor. İlk raporun 293 maç üzerinden tüm matematik ailesi hakkında karar verir gibi görünmesi eksikti ve bu raporla düzeltilmiştir. Aktif MS=M4 / KG-C3 ailesel sabit yönlendirmesi bir mühendislik sabitidir, kanıtlanmış en iyi yöntem değildir.

## Sınırlar
- **Bu çalışma sadece orijinal SHA doğrulanmış 10 lig, 4.413 veri kaynağına aittir.** Ayrı 4.518/4.617/4.618 skor ve xG havuzları eşlenik maç önü olasılıkları olmadan birleştirilmedi; aynı örneklemlermiş gibi söylenmedi.
- 2025/26, M4 hiperparametresi seçilmiş sezon olduğu için tüm 2.922 maç prequential as-of olsa bile tam bağımsız kör test değildir.
- 2026/27 880 geçmiş tahmin zaten vardı; ayrı kayıtlardan genişletici olarak ifade ediliyor, burada yeniden test edilmedi.
- xG yayımlanma zamanları, oyuncu-11, oran/EV, canlı tek maç API/PDF saha işlemesi, 22 liglik araştırma havuzu bu **tam sezon tarih-as-of testinin dışındadır**.
- Birden fazla modelin KG/2.5'te lig tabanını geçememesi ortada hesaplama hatası olduğunu tek başına ispatlamaz; model yanlış kalibrasyonu, lig ortalaması durağanlığı veya zayıf ek sinyal olabilir.
- Araştırma çıktısı kullanıcıya bilinçli şekilde test kazanma ya da kârlılık vaadi olarak sunulmaz.

**Kanıt:**
[GitHub Actions başarılı #44809963151](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44809963151);
[05_full_history_result.json](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/05_full_history_result.json);
[audit_full_history.py](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/audit_full_history.py)
