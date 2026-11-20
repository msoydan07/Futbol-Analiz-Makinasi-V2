# FUTBOL MAÇ ANALİZ MAKİNESİ 2.6.3 — BAĞIMSIZ MÜHENDİSLİK DENETİMİ
## 20 Kasım 2026 | Toplu sonuç ve karar raporu

**Karar: Aktif sistem korunsun; hiçbir yeni matematik otomatik terfi almasın.** Bu, mevcut M4'ün ya da C3'ün kesin kazandığı anlamına gelmez. Ekim retrospektifinde C3 özellikle MS için, Ağustos–Eylül'de ayarlanmış ölçülü kalibrasyon KG/2.5 için, doğrudan lojistik model de 2.5 için umut veren sonuçlar verdi. Ancak Ekim daha önce görülmüş bir dönemdir; 8 Kasım'daki 39 mühürlü maç yalnız tek güne aittir ve kaynakların tümü resmî değişmez maç kimliğiyle yeniden onaylanmış değildir. **Bağımsız üstünlük kanıtı yoktur.**

**Kapsam:** Kullanıcının esas hedefi, bir maçta yalnız **MS 1 / X / 2, KG Var / Yok ve 2.5 Üst / Alt** içinden gerçekleşmesi en olası **tek bir olayı** mümkün olduğunca doğru olasılıkla bulmaktır. Karar katmanı, olasılık modelinin başarısından ayrı test edildi. Getiri veya oran avantajı yüksek isabet olasılığıyla eşitlenmedi.

## 1. Doğrulanan kanıtlar ve farklı veri kümeleri

| Kaynak | Kapsam | Güven sınırı |
|---|---|---|
| Orijinal SHA-dondurulmuş arşiv | **4.413 maç, 10 lig**, 2025/26 **3.533**, 2026/27 **880**. SHA-256 başlangıcı **35c5e7b4...** | Bu yeni testte indirildi, tam SHA kontrolünden geçti; yeniden oluşturmada yalnız bu arşiv kullanıldı. |
| Ağustos–Eylül 2026 | **587** maç | Önceki araştırmalarda kullanılmış kronolojik geliştirme; yeni shrink katsayıları yalnız buradan seçildi. |
| Ekim 2026 | **293** maç, **19 maç günü** | Aynı maçlarda yeni yöntemler karşılaştırıldı; sonuçlar önceden araştırıldığından **kör nihai test değil**. |
| 8 Kasım 2026 | **40 eski maç önü SHA kaydı / 39 sonuç / 1 erteleme**, bir maç günü | Sonuçlar orijinal tahmin SHA'larıyla bağlandı; tüm skorlar bağımsız federasyon maç-ID onaylı değil, geçmişte incelemeye konu oldular. |
| Diğer arşiv: **4.518** | Kabul edilmiş farklı sürüm. SHA başlangıcı **1170ecf9...** | Orijinal 4.413'e karıştırılmadı. |
| Diğer araştırma skor havuzu: **4.617** | SHA başlangıcı **637b8597...** | Yalnız skor alanları, 99 yeni sonucun kaynak güven sınıfları farklı; özgün 4.413 deneyine karıştırılmadı. |
| xG araştırma havuzu: **4.618** | SHA başlangıcı **3b13921d...** | Özel xG kaynakları için ilk yayımlanma/as-of zamanları kesin değil. Bu deneyde veriymiş gibi kullanılmadı. |

Orijinal 4.413 arşiv GitHub Actions'ın daha önce imzaladığı artefakttan çekildi ve gerçek SHA-256 ile sınandı. Dönemlerin tamamı daha önce projede tartışıldığı için **880 retrospektif maçı sonradan ilk kez görülen 880 kör maç gibi sunmuyoruz**. Pazarlar arasında 7 olayı 7 bağımsız müsabaka diye saymıyoruz.

## 2. Bu yeni denetimde gerçekten ne yapıldı?

Aktif çalışma kolundan ayrı **research/263-independent-math-audit** kolu açıldı. Önce **00_experiment_matrix.json** ile 15 matematik adayı, tarihler, birincil ölçütler, kalibrasyon ızgarası ve karar kuralları kayıt altına alındı. Bu kayıttan sonra orijinal modeller, veri ve SHA mühürleri değiştirilmeden tek defalık as-of tahmin yeniden oluşturması kullanıldı.

15 aday: geçmiş lig olay frekansı, B, C2, C3, M4, C3–M4 eşit karışımı, iki sabit Dixon–Coles düşük skor düzeltmesi (rho -0.1 / +0.1), ortak-gol bileşenli bivariate Poisson (0.15), iki sabit negatif binom yayılımı (k=3 / k=8), M4/C3/karışım için geliştirmeden kilitli pazar-ailesi shrink kalibrasyonu ve tek sabit cezalı lojistik sınıflandırma (C=0.5).

Aynı **293 Ekim maçında** 15 adayın MS, KG ve 2.5 Brier/log-loss ölçümleri alındı; eksik modellerin farklı örnek sayıları ayrıca korundu. Ekim 19 maç günüyle eşleştirilmiş **1.600 tekrarlı gün-blok bootstrap** uygulandı. 39 Kasım maçında katsayılar yeniden öğrenilmedi. Her politika için maç başına tam **bir** tercih seçildi; seçim kapsaması, ortalama güveni, gerçekleşen isabeti, seçilen olayın Brier'i ve yüzde 65 eşiğinde PAS davranışı karşılaştırıldı.

Bu adayların tümü **eşit düzeyde sıfırdan eğitimli gol modelleri değil**. Dixon–Coles/bivariate/negatif binom sürümleri M4'ün aynı maç önü gol beklentilerinin dağılım dönüşümleridir. Doğrudan lojistik, C3/M4 ve lig frekansı gibi mevcut maç önü tahminlerinden öğrenen ikinci aşamadır; Elo veya ham takım özellikleriyle baştan inşa edilen model olarak gösterilmez. Bu ayrım sonuçların kapsamını belirler.

## 3. Ekim: model olasılığının doğruluğu

**Brier düşük oldukça iyidir.** MS için üç sonucun karesel hataları **toplanmıştır**. KG ve 2.5 tek olay için ikili Brier'dir. Üç farklı ölçek birbirine doğrudan kıyaslanmaz.

| Aday | Ortak kapsam | MS Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|---:|
| Lig as-of olay frekansı | 293 | 0,645006 | 0,244834 | 0,245510 |
| B | 212 | 0,583902 | 0,249775 | 0,253301 |
| C2 | 105 | 0,623237 | 0,247246 | 0,245890 |
| **C3 ham** | 293 | **0,582332** | 0,246752 | 0,247089 |
| **M4 ham** | 293 | 0,585542 | 0,248779 | 0,249303 |
| C3/M4 yarı yarıya | 293 | 0,583318 | 0,247558 | 0,247860 |
| Dixon–Coles rho -0,1 | 293 | 0,587933 | 0,248102 | 0,249303 |
| Dixon–Coles rho +0,1 | 293 | 0,584528 | 0,249686 | 0,249303 |
| Bivariate Poisson 0,15 | 293 | 0,587399 | 0,247720 | 0,249777 |
| Negatif binom k=3 | 293 | 0,587623 | 0,261578 | 0,252715 |
| Negatif binom k=8 | 293 | 0,585726 | 0,251933 | 0,250109 |
| M4 + geliştirme shrink | 293 | 0,585542 | 0,244610 | **0,243584** |
| C3 + geliştirme shrink | 293 | **0,582332** | **0,244070** | 0,243660 |
| Yarı yarıya + shrink | 293 | 0,583318 | 0,244288 | 0,243601 |
| Doğrudan cezalı lojistik | 293 | 0,583760 | 0,244344 | **0,240995** |

**B veya C2'nin kendi örneklemindeki sayıları diğer tam-kapsam yöntemlerle doğrudan karşılaştırılamaz.** B yalnız 212/293, C2 105/293 maçta tahmin üretmiştir. B ile M4'ün aynı 212 maçındaki MS eşleşmiş farkı M4 lehine 0,005915, fakat gün-blok aralığı sıfırı içerir; C2'de kapsam daha da zayıf.

**MS:** C3 Ekim'de M4'e karşı Brier'i **0,003209** iyileştirdi. Eşleşmiş gün-blok yüzde 95 aralık **[-0,002119; +0,009021]**. Bu yüzden “C3 kesin daha iyi” denemez. Basit lig frekansı ise MS'de hem C3 hem M4'e belirgin şekilde yenildi; takım/rakip bilgisi gerçekten yararlı sinyal taşıyor.

**KG:** C3'ün 0,246752 ham Brier'i, tek başına lig frekansının 0,244834 değerinden bile daha kötü. Ağustos–Eylül ile kilitlenen **C3 shrink** bunu 0,244070'e düşürdü. C3 hamdan shrink'e olan iyileşme umut verici ama Ekim aralığı **[-0,002459; +0,010240]**; kesin üstünlük değil.

**2.5 Alt/Üst:** En düşük Ekim Brier **0,240995**, doğrudan lojistikte. Fakat C3 hamı referans alan farkın belirsizlik aralığı **[-0,009818; +0,028645]**; çok geniş. M4 ve C3 shrink yaklaşık **0,2436** ile, sırf daha karmaşık Poisson yerine doğru kalibrasyonun ciddi aday olduğunu gösteriyor.

## 4. Kasım'daki orijinal mühürlü 39 sonuçta stres kontrolü

| Aday | MS Brier | KG Brier | 2.5 Brier |
|---|---:|---:|---:|
| Lig frekansı | 0,655725 | 0,247115 | **0,238767** |
| C3 ham | 0,517322 | 0,246367 | 0,247555 |
| M4 ham | **0,509959** | 0,248164 | 0,262744 |
| C3 + shrink | 0,517322 | **0,244701** | **0,238823** |
| M4 + shrink | **0,509959** | 0,244963 | 0,242011 |
| Doğrudan lojistik | 0,512301 | 0,246865 | 0,248813 |

Ekim'de **C3 MS önde**, 8 Kasım'da **M4 MS önde**: dönemler arasında üstünlük ters dönüyor. Lojistiğin Ekim'deki 2.5 liderliği Kasım'da korunmuyor; bu nedenle güncel üretime **terfi ettirmeyiz**. C3 2.5 shrink 0,238823 ile yalnız lig frekansı 0,238767'ye çok yakın; her bileşik sistemin taban oranı aşabildiği varsayılamaz.

39 maç yalnız **bir maç günüdür**. Bu kümeyle geçerli maç-günü bootstrap aralığı üretilemez. Sonuçların önceki karar araştırmalarında da incelenmiş olması ayrıca bağımsızlık sınırıdır.

## 5. Asıl hedef: “Bu maçta en olası yedi olaydan hangisi?”

Aşağıdaki deneyde her maçta MS1, MSX, MS2, KG Var, KG Yok, 2.5 Üst, 2.5 Alt içinden **tek en yüksek bildirilen olasılık** seçildi. Bu **sadece araştırma prototipidir**: mevcut üretim karar vericisindeki Ağustos M4 müşterek MS kalibrasyonu, 39 sonuçlu tarihsel meta referansı, İddaa/PAS güvenlik kapıları ve kullanıcı PDF akışının birebir yeniden işletimi değildir.

| Politika | Ekim doğru/293 | Ortalama verilen güven | Seçilen olay Brier | Kasım doğru/39 |
|---|---:|---:|---:|---:|
| M4 ham | **%57,00** | %63,46 | 0,243090 | %61,54 |
| C3 ham | **%58,36** | %62,25 | 0,239456 | %61,54 |
| Sabit MS=M4 / KG-2.5=C3 **ham prototip** | **%57,68** | %62,77 | 0,242331 | %66,67 |
| M4 aile shrink | **%59,39** | %60,22 | 0,236639 | %64,10 |
| C3 aile shrink | **%58,70** | %59,39 | **0,235654** | %58,97 |
| Yarı yarıya + shrink | **%59,39** | %59,75 | 0,236732 | %61,54 |
| Lojistik | **%59,39** | %64,39 | 0,241396 | %58,97 |
| Lig frekansı | **%57,00** | %56,91 | 0,244008 | %51,28 |

**Çıkarım:** Ekim'de ham M4 yüksek olasılıklarını olduğundan emin sunma eğiliminde (**%63,46 tahmin / %57,00 gerçekleşme**). Önceden geliştirmede seçilmiş shrink, M4 için farkı **%60,22 / %59,39** düzeyine indiriyor ve seçilen olay Brier'ini düşürüyor. Bu, artırılmış isabet garantisi değil; **kalibrasyon probleminin modeli biraz daha karmaşıklaştırmaktan daha önemli olabileceği** yönünde kanıt.

**Kritik adalet notu:** Politikalar bazen farklı pazar olaylarını seçtiğinden, seçilen olay Brier ve isabeti aynı maçta bile **aynı etikete karşı yapılan eşleşmiş Brier** değildir. Bu tablo kullanıcının “en olası bir olay seçilsin” hedefini ölçer; modellerin tek tek pazar doğruluğunun yerine geçemez. MS/KG/2.5 ayrı Brier'leri ve kapsama birlikte okunmalıdır.

**%65 koşullu PAS stres deneyi:** Örneğin Ekim'de C3 shrink 52/293 maç seçti ve %73,08 gerçekleşme gözlendi; M4 shrink 65/293 seçti ve %67,69 gerçekleşti. Kasım tek günde M4 shrink 8 maçta %87,5 gözledi. **Bu az sayıdaki alt gruplar seçime bağlıdır, yeni bir %65 canlı bahis kuralı ilan edilmez.** Örnekleme/çoklu arama yanlılığı ve farklı kapsama yüzünden görünen yüksek yüzdeler kazanma garantisi değildir.

## 6. Matematik alternatiflerinden öğrendiklerimiz

- **Bağımsız Poisson çekirdeği:** Tutarlı bir ortak gol olasılık dağılımı üretmesi güçlü bir tasarım özelliği. Yeni denetim “Poisson en iyi matematik kesin budur” ispatı bulmadı, fakat reddini gerektiren sağlam bir kanıt da bulmadı.
- **Dixon–Coles:** Sabit pozitif rho MS'de M4'e karşı yalnız 0,001014 Brier kazandırdı, sıfırı içeren aralık nedeniyle önemsiz. Negatif rho MS'yi kötüleştirdi; iki rho da tüm pazarları iyileştirmedi. Gerçek gelişim verisinde rho'nun öğrenildiği tam bir model bu testin kapsamı değildir.
- **Bivariate Poisson:** Paylaşılan gol bileşeni KG'de ham M4'e göre biraz iyi olsa da C3 ve kalibre adayları geçmedi; MS ve 2.5 için genel fayda göstermedi.
- **Negative Binomial:** Sabit k=3/8 aşırı yayılım varsayımları mevcut örneklemde özellikle KG'yi bozdu (k=3 KG 0,261578). Bunlar yeniden öğrenilmiş dispersion modelleri değil; mevcut lambda'ların stres alternatifleridir.
- **Düzenlileştirilmiş lojistik:** 580 geliştirilebilir örnekte, 12 maç-önü tahmin özelliğiyle eğitilmiş ikinci-aşama model. Ekim 2.5 iyileşti; Kasım geriye döndü. Farklı pazar ailesi olasılıkları **tek bir gol skor dağılımını temsil etmek zorunda değil**.
- **Kalibrasyon:** Geliştirmede sabit **MS 1, KG 0,50, 2.5 0,25** aile ağırlıkları üç ailede de ortaya çıktı. Bu farkın nedeni gelecek bilgi değil; 587 geçmiş geliştirme maçındaki Brier ile önceden sabit aday seçimi. Her pazarın tamamlayıcılığı korunur, fakat farklı ailelerden ayrı ayar tek ortak Poisson dağılımı olduğu iddiasına dönüşmez.

## 7. xG, rakip gücü, ilk 11 ve veri kalitesi

Önceki **M4+xG** araştırmasında 1.083 tarih sıralı karşılaşma, geçmiş xG'si kullanılabilir 810 / güvenli fallback 273 ölçülmüştü. O araştırmada 2.5 için Brier ham M4 **0,247734**, xG düzeltmeli **0,244649**, gün-blok aralığı **[+0,000613; +0,005660]**. Buna karşı MS ortalama-üçlü Brier **0,195592 → 0,196817** kötüleşti; KG artışı da güven aralığı açısından belirsizdi. **Bu daha önceki araştırma sonuçlarını burada tekrar üretmedik ve bu sayıları yeni 293 Ekim karşılaştırmasıyla aynı ölçekmiş gibi birleştirmiyoruz.** xG'nin kaynak yayımlanma zamanı ve özel veriye erişim kesin olmadığı için üretim terfisi haklı değil.

Rakip gücü, hücum-savunma, ev/deplasman ve zaman ağırlığı M4'te kısmen zaten öğreniliyor; ayrıca özellik eklerken rakibin gücünü **iki kez saymama** kontrolü gerekir. C3 ile M4 kıyası bu faktörlerin **tek tek izole ablation testi değildir**. Son 5/10/20, Elo, ham xGA ve oyuncu/ilk 11 bilgisi için bağımsız ve doğrulanmış maç önü özellik kesitleri bulunmadan yeni sonuca hükmedilmedi. Bu unsurları yapılmış gibi saymıyoruz.

## 8. Denetimin sınırları ve risk kaydı

1. **Kör veri yok:** Ekim gelişim sonrası değerlendirme olsa da geçmişte sonuçları görülmüş; Kasım aynı gün ve önceden skorlu. Başarı derecesi **keşif** olarak kalır.
2. **Farklı kapsam:** B 212/293; C2 105/293. Tam kapsam Brier tablosu ile karar verilmez, yalnız eşleşmiş alt kümeler ve kapsama birlikte değerlendirilir.
3. **Kaynak doğrulama:** 4.617 arşiv skorları tam bağımsız resmî ID onaylı değildir; Nov8 skorları da tek kalite sınıfında değildir. Bunlar birbirine güven kazandırmak için karıştırılmadı.
4. **Zaman kanıtı:** Takım maç sonucu geçmişi hedef günden önceki günle sınırlı; bunun dışında xG yayımlanma-vintage ve dakika bazlı veri erişim zamanları kapatılmış değil.
5. **Çoklu deneme:** 15 aday ve çok sayıda pazar/karar görünümü üretildi. Verilen güven aralıkları **çoklu hipotez düzeltmesi yapılmış nihai ispat aralıkları değil**.
6. **Pazar aileleri arası tutarlılık:** Birleştirilmiş/shrink/lojistik olay yüzdeleri kendi pazarında normlanır, fakat ortak skor dağılımından gelmeyebilir. Kullanıcıya öyle gösterilmemeli.
7. **Aktif uygulamanın aynısı değil:** Sabit uzmanı burada **ham M4 MS + ham C3 KG/2.5** prototipi olarak değerlendirdik; aktif Ağustos birlikte kalibre M4 MS, tarihsel referans ve gerçek PDF/PAS güvenlik akışını birebir simüle ettiğimizi ileri sürmüyoruz.
8. **Bahis getirisi:** Gerçek tarihli oran ve marjdan arındırılmış fiyatlar olmadığı için EV/ROI ölçümü veya kârlılık sonucu yok.

## 9. Hangi tasarımı öneriyoruz?

**Şimdilik uygulama değişikliği = sıfır.** 20 Kasım itibarıyla sabit **MS=M4, KG/2.5=C3** mevcut yönlendirmesini, model kodlarını, 10 aktif ligi, orijinal tahmin mühürlerini, otomatik işlemleri ve onaylı mobil PDF şablonlarını olduğu gibi tut. Bu yönlendirme **kanıtlanmış küresel optimum** diye sunulmasın; bir operasyonel sabitlik kararıdır.

**En güçlü araştırma adayı tek başına yeni “süper model” değil, pazar ailesi bazında küçük ve dondurulmuş bir olasılık kalibrasyonudur.** Mevcut C3 KG/2.5 kalibrasyon gölge katmanı zaten var; bu denetim yeni, yinelenen bir pilot veya aynı kodu başka adla üretime sokma nedeni değildir. MS tarafında C3 ve M4 arasında istatistiksel net galip yoktur; MS için M4'ü sırf daha karmaşık, C3'ü sırf Ekim kazandı diye otomatik seçmek doğru olmaz.

Bağımsız sonraki kanıt olarak **zaten kendiliğinden oluşan yeni maç önü SHA mühürlerini** doğru maç-ID ve resmî sonuçla eşleştirmek, farklı maç günlerinde önceden dondurulmuş aday yüzdelerini değerlendirmek gerekir; kullanıcıya yeni pilot görevi yüklemek ya da geriye dönük aynı maçları tekrar “kör test” saymak gerekmez. Yeterli güç oluşmadan üretim terfisi yapılmaz.

## 10. Kod güvenliği, tekrar üretilebilirlik ve teslim

- Çalışma kolu: **research/263-independent-math-audit**. Aktif M4/B/C2/C3, model-first karar dosyaları, ana kol, orijinal mühürler ve kullanıcı onaylı PDF'ler üzerinde değişiklik **yapılmadı**.
- Dosyalar: **00_experiment_matrix.json** (önden kayıt), **01_evidence_inventory.json** (dosya/SHA ve kaynak sınırları), **audit.py** (kod), **02_result.json** (15 adayın iki dönemli sayıları, 19 gün eşleşmiş aralıkları, karar tabloları), **03_report.md** (ham karşılaştırma).
- GitHub Actions: **44808068394 — başarılı**; orijinal veri SHA doğrulandı; 880 geçmiş tahmin tek as-of protokolünden yeniden üretildi; kod çalıştı; araştırma çıktıları araştırma koluna işlendi; aktif kaynaklar ve mühürlerin değiştirilmediği Git diff koruma adımı başarılı.
- İlk çalıştırmadaki sklearn RNG parametresi aralık hatası **yalnız deterministik çalıştırma düzeltmesiyle** giderildi. Son başarılı koşunun uygulanan kodu audit.py içinde; gizli başarısız adım görmezden gelinmedi.
- Belgeler araştırma amaçlıdır. **Olasılık üstünlüğü onayı, para/EV yetkisi veya canlı üretim terfisi verilmedi.**

**Son hüküm:** Mevcut Poisson merkezli dört-model mimari **savunulabilir bir başlangıç**, ama “mümkün olan en güvenilir çözüm olduğu kanıtlandı” sonucu **yanlış** olur. Bu bağımsız araştırmada asıl sorun kompleks matematik eksikliğinden çok, **pazar bazlı kalibrasyonun ve en yüksek olasılık seçiminin gerçekten güvenilirliğinin yeterli kör kanıtla gösterilememiş olmasıdır**. İyileştirme adayları bulundu; hiçbiri bugün üretime geçecek kadar kesinleşmedi.

### Kanıt bağlantıları
- [Başarılı GitHub Actions denetimi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44808068394)
- [Bağımsız araştırma sonuç klasörü](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/tree/research/263-independent-math-audit/research/263_independent_audit)
- [Önceki M4 geliştirici kabulü](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/M4_ENGINEERING_ACCEPTANCE_REPORT.md)
- [C3 kalibrasyonunun terfi edilmeme gerekçesi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/C3_KG_O25_CALIBRATION_DECISION_20261120.md)
- [Mevcut pazar uzmanlığı kararı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/DECISION_FIXED_MS_M4_C3_KG_GOALS_20261120.md)
- [Önceki xG pazar bazlı test](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/M4_XG_MARKETWISE_KARAR_20261119.md)
