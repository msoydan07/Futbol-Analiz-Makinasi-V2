# Futbol Maç Analiz Makinası 2.6.3 — Ana tercih / alternatif / PAS karar katmanı
## Kapsamlı araştırma, uygulama kararı, ÖN KAYIT (4 Kasım 2026)

**Karar:** S1/S2 için tek boyutlu sabit %75/%70/%65 eşik tablosunu nihai mekanizma yapmıyoruz. Ana aday: **kanıt ve güvenlik kapısı + kalibre edilmiş pazar-bazlı olasılıklar + seçici karar (risk–coverage) + ayrı fiyat/değer kontrolü**. Mevcut B/C2/C3/M4 ve ana/deney dalı model kodları DEĞİŞMEYECEK. Alternatifleri değerlendirmeden kazanan ilan edilmeyecek.

## Kaynak araştırması, bulgular, sınırlar

1. Wilkens (2026), Bundesliga 11 sezon: basit xG temelli model pazara göre daha zayıf kategorik kalibrasyon gösterebilirken piyasanın kaçırdığı sinyaller bulunabiliyor; ROI bulguları farklı sezon ve pazarlara koşulsuz genellenemez. https://journals.sagepub.com/doi/10.1177/22150218261416681
2. Hegarty & Whelan (2025), International Journal of Forecasting: klasik üç sonuçlu piyasada favori/sürpriz yanlılığı; piyasa marjsız fiyatı mutlak gerçek değil. https://www.sciencedirect.com/science/article/pii/S0169207024000670
3. scikit-learn calibration docs: gerçek olasılık kalibrasyonu modellerin eğitildiği AYNI örneklerle öğrenilmez; izotonik küçük örneklerde overfit eder. Az örnekte basit shrinkage / sigmoid / temperature; isotonic ancak yeterli OOF örneklem olunca. https://scikit-learn.org/stable/modules/calibration
4. Karinov et al. (2025), 'Domain-Driven Identification of Football Probabilities': birden fazla oran pazarı kullanımı ve margin removal fark yaratabilir; orantısal no-vig tek doğru çözüm değildir. https://ideas.repec.org/a/gam/jmathe/v13y2025i24p3976-d1817259.html
5. Risk–coverage literatürü: bir 'PAS / karar ver' kuralını tek accuracy skoruyla değil, **karar verilen maç sayısı ve o kararların hatası** ile birlikte incelemek gerekir. https://pmc.ncbi.nlm.nih.gov/articles/PMC13631354/
6. Conformal prediction koşulu: normal kapsama garantisi exchangeability ister; sezon, takım, kadro ve dağılım değişimlerinde garanti diye sunulmaz. İlk kabulde zorunlu conformal / sahte kesin güven yüzdesi yok. https://journals.sagepub.com/doi/10.1177/25152459251380452

## Gerçek kod/veri durumu — neden sadece 3 eşiği denemiyoruz?

Mevcut `experiments/263/classification_odds_263.py`:
- S1/A adayı: `p>=0.75`, Poisson lambdaları ±%10 senaryolarında min `>=0.70`.
- S2/B adayı: `EV>=0.05` ve aynı kitap/karşı fiyat marjsız pazar avantajı `>=0.03`.
- Her ikisi ayrıca doğrulanmış resmî maç, `context_ok`, tam/basit matematik seviyesi, yüksek/orta veri güvenilirliği ve kritik kayıp olmaması koşullarına bağlı.
- Fiyat için kaynak ve eşzamanlı karşı pazar; snapshot yaş sınırı 10 dk. Kodun `official_class=None` döndürdüğü durumda 'oyna' onayı üretilmiş değildir.
- Şu anki %75 tüm pazarlar için eşit olduğu için 1,5 Üst, 1X/çifte şans gibi yüksek taban oranlı pazarları MS/KG karşısında öne sürme yanlılığı var.
- ±%10 stres alt sınırı **gerçek güven aralığı değildir**. Modeller arası benzerlik de kalibrasyon kanıtı değildir.

**4 Kasım veri envanteri:** `extended_history.csv` 4.509 sonuç (3.533 maç 2025/26 + 976 maç 2026/27) ve 10 lig. Dosya başlıklarında **eski maçların zaman damgalı bookmaker fiyatları YOK**. Bu dosya olasılıkların as-of geçmişe dönük değerlendirilmesi için ham sonuç bazını sağlar; **dürüst geçmiş ROI/S2 testi yapılmasına tek başına yetmez**. İlk 4.413 dondurulmuş, son 96 yeni sonuç makine-stage/human acceptance bekliyor. Tek erken Gaziantep–Kasımpaşa shadow ise resmî T−60 pilotunun parçası değil.

## Tercih edilecek mimari — tek nihai karar, en fazla bir alternatif

### 1. Bağımsız zorunlu kapılar (gerçek PAS nedenleri)
- Geçerli resmî gelecek maç, doğru takım/ev-deplasman, başlamadan önce doğrulanmış saat; zaman sızıntısı yok; skor veya gelecekteki verilerle geri hesaplanan tahmin yasak.
- En az bir teknik olarak geçerli, yeterince tarihsel bağlamlı ve as-of kurulabilen önceden kabul edilmiş tahmin motoru; veri çelişkisi veya hesap tutarsızlığı yok. Deney motoru terfisi yasak.
- Kritik ve belirsizliği çözülememiş durum tüm destek verisini geçersiz kılıyorsa PAS. **İlk 11 açıklanmaması, tek bir xG'nin bulunmaması, bir yardımcı istatistiğin eksikliği tek başına PAS DEĞİL**.
- Bir maçta S1 adayı puanlanabilirken fiyat eksikse bütün maç PAS olmaz. 'S1 analitik aday — fiyat doğrulanmadı' yaz; **bahis amaçlı ana tercih onayı verme**, S2 = oran yok.
- Fiyat kaynak onayı/karşı fiyat/eşzamanlılık/tazelik yoksa EV/S2 yayınlama. Aynı bookmaker'ın tam karşı fiyatları gerekli.

### 2. Geliştirilecek seçim ve değerlendirme katmanı
A) Her modelin MS, KG, gol piyasalarını as-of zamanlı tahminlerden ayır. Önce tarihsel gerçeklerle **Brier, çok sınıflı log-loss, kalibrasyon eğrisi** ve lig/market taban olasılığına göre beceri ölç. Bu sonuçlar modelin yüzdesiyle karıştırılmasın. Önce minimal pooled calibration ve shrinkage; yeterli örnek olmadan model/lig/pazar başına izotonik optimizasyon YOK.

B) Her pazarın ham p'sini basit %75 eşiğine göre değil; **pazar türüne özel tarihi taban olasılığı, kalibre edilmiş hata, veri güveni, basit stres-duyarlılığı, model anlaşmazlığı** üzerinden değerlendir. Modeller arası uyum ancak empirically faydalıysa puan olsun. Piyasa yakını modeli otomatik seçme. İleri karşılaştırmada market-only, her model ayrı, market–model blend (ayrı araştırma rakibi) puanlansın.

C) En iyi **tek ana aday**: önceden ölçülebilir, kabul edilmiş S1 veya fiyat gerçekten varsa S2 ailesinden. Alternatif, ana adayın eş anlamlısı / aynı sonuca mekanik olarak bağlı pazar ise ikinci bağımsız risk gibi tanıtılmasın. Örn. '1,5 Üst' ve '2,5 Üst' ilişkili; '1X' ile 'MS1' de ilişkili. Alternatif sadece kendisi ayrıca yeterli düzeydeyse gösterilir.

D) S1 ve S2 **iki ayrı amaç**: S1 = gerçekleşme olasılığı / istatistiksel isabet; S2 = doğrulanmış piyasa fiyatına göre kalibre edilmiş beklenen değer. ROI yüksek görünmese de yüksek olasılıkları gizleme; fakat **S1 yüksek olasılık ≠ fiyatı iyi bahis**. Eski fiyatı kullanıp canlı değer önerisi çıkarma.

E) PAS nedenlerini ayrı tut: `PAS_DATA`, `PAS_NO_QUALIFIED_SELECTION`, `PAS_NO_VALID_PRICE_FOR_VALUE`, `PAS_MODEL_UNCERTAINTY`. Salt PAS oranı düşük diye kapıyı gevşetme. Kalibre edildiği kanıtlanmayan %90 'güven' etiketi üretme. İlk sürümde `GÜVEN: ONAYLI / SINIRLI / ÖLÇÜLEMEDİ`.

### 3. Adaylar — önceden yalnız sınırlı alternatifler

| Kandidat | S1 seçimi | S2 seçimi | Neyi test edecek? |
|---|---|---|---|
| T0 / mevcut | %75 + stres %70 | EV %5 ve no-vig fark 3yp | Halihazırdaki sıkı referans |
| T1 / sade esnek | %70 + stres %65; sadece deney | S2 mevcut değişmez | Esnetmenin kapsam/hata etkisi |
| T2 / önerilen seçici | Esnek tek eşik yerine **pazar bazlı kalibrasyon ve risk–coverage** eşiği, geçmiş sonuçlardan öğrenilen, as-of | S2 eski kural + p belirsizliğine göre ihtiyatlı alt p duyarlılığı; ayrı ablasyon | Denge: PAS sayısı vs seçilenlerin kalitesi |
| R0 / piyasa | S1 seçmez; marjsız piyasa referansı | Kendi fiyatıyla 'piyasa üstünlüğü' iddia etmez | Güçlü dış kıyas |
| R1 / piyasa-model havuz | Piyasa+model kalibrasyonlu blend; araştırma çıktısı | Kendi dayanak piyasasına karşı EV kanıtı diye kullanılmaz | Piyasadan gelen bilginin ek değeri |

**Nihai tercih adayı T2.** T0 ve T1 deneyden düşürülmesin; T2 kendisini kanıtlayana kadar **T0'nın mevcut kuralları değişmeyecek**. T2 kıyas pazarlarını önceden belirlenmiş MS1/X/2, KG Var/Yok, 1,5/2,5/3,5 Alt-Üst ile sınırla; ilk yarı korner yok. Çifte şans değerlendirilecekse ilişki ve karşı oran kuralı ayrı.

## Tek toplu tarihsel ve ileri deney protokolü

1. Önce gerçek **as-of** geçmiş tahmin kaydı üretilebilir mi denetle: her modelin geçmiş tarihte mevcut olan veriyle çalışması gerekir. Bugünkü parametrelerle eski maçlara 'o zaman söylemiştik' demek yasak. Yalnız hata ölçmek için geçmişte zamanında erişilen ham verilerle yeniden oluşturulan tahminler **retrospektif simulasyon** diye etiketlenir. `2026/27` sonucu sonuç olarak bilindiği için bir de gerçek ileri 6–8 Kasım kohortu şart.
2. Geçmiş lig/sezon dosyasını kronolojik alt dönemlere ayır, sıralı walk-forward (rolling/expanding); kalibrasyon parametresi **yalnız daha eski, model fit'inden ayrık tahminler** üzerinde öğrenilir. Gelecek maçın gerçek sonucunu veya ileri oranını görerek model seçilmez. Sezon ve lig aşırı öğrenme riski için pooled/shrinkage düşün.
3. Pilot kaynak fiyatı olmadığı maçlara **yokmuş gibi EV yazma**. `2025/26` daki closing odds ileride ayrı kaynak olarak bulunursa yalnız 'geçmiş pazar benchmark' diye işaretle; T−60'da erişilebilirdi iddiası veya tarihli bahis getirisi yapma. ROI/S2 gerçek sınaması ancak kickoff öncesi zaman ve fiyat mühürlü örneklerde.
4. Aynı maç kümesinde 1X2 için çok sınıflı Brier + log-loss; KG/O-U için binary Brier + log-loss; calibration slope/reliability chart; pazar/lig oranlarına göre performans. Sonra **seçici risk–kapsama eğrisi**: toplam aday maçın kaçı seçildi, seçilenlerde hata/kalibrasyon, PAS nedenleri, pazar yoğunluğu ve ligler arası dağılım.
5. Piyasa kıyasını ancak aynı fiyat/saat/kaynak ve maç kümesine sahip alt kümede yap. `EV=p*oran-1` hesaplanabilir, **kâr garantisi değildir**. Raporla: seçim sayısı, gerçekleşme, ROI/drawdown için geniş güven aralıkları, mümkünse CLV; analiz sonrasında oran seçerek geçmişe değer yazma.
6. S1 için önceden belirlenmiş temel amaç: **pazar-tabanlı modele göre kalibre edilmiş tahmin hatasını kötüleştirmeden sağlıklı kapsama**. S2 için temel amaç: **belirsizlik duyarlı, gerçek aynı an fiyatı olan örneklerde pozitif ve tekrarlanabilir avantajın gösterilmesi**. T2'nin sırf daha çok maç seçtiği için kazanmış sayılması YASAK.
7. 25 maç **teknik ara kontrol**, 96 aday bir **kapsam listesi**, 100 ileri tahmin bir **erken pilot**; hiçbiri tek başına kârlılığı kanıtlamaz. Karar için çoklu dönem/lig istikrarı ve haftaya göre gruplanmış paired-bootstrap belirsizlik aralıkları. Çok alternatif deneme (data snooping) önlenmek için strateji ailesi ve eşikler önceden kaydedilir.
8. **Tek paket, tek test, tek rapor**: model motorlarını yeniden yazma; önce hangi eski as-of tahminler ve hangi oranlar gerçekten erişilebilir sayım raporu; ardından yalnız mevcut stok çıktılardan tüm T0/T1/T2/R0/R1 kıyaslarını kur; tüm karşılaştırmalar birlikte, tek CI/tek kapsamlı rapor. Sonuç yetersizse 'YETERSİZ KANIT', sahte şampiyon yaratma.

## Kullanıcıya tek ekran sözleşmesi

```
MAÇ / T-60 veya erken araştırma / kaynak kalitesi
MAKİNENİN KARARI: ANA [pazar / kalibre olasılık / varsa eşzamanlı oran]
ALTERNATİF: [yalnız ayrıca uygunsa; ilişkiliyse not]
S1 en olası / S2 değerli ayrı nedenleri
PAS varsa: kesin nedeni, fiyat mı model mi veri mi
PİYASA İLE KIYAS: yalnız referans; marjsız yaklaşımdır
DÖRT MODEL DETAYI: B C2 C3 M4, değişmemiş
MAÇ SONU: mühürlü kayıt vs gerçek skor, logloss/brier + geçerli fiyat varsa ROI
```

**Bu doküman araştırma/ön kayıt kararıdır; çalışan canlı seçim motoruna T2 terfisi, T−60 pilotuna ek tahmin, insan veri kabulü veya bahis önerisi değildir.**
