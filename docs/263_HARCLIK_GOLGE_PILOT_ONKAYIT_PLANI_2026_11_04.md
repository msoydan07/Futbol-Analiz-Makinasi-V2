# Futbol Maç Analiz Makinası 2.6.3 — TEMKİNLİ SEÇİM / HARÇLIK SANAL PİLOTU

**Tarih:** 4 Kasım 2026 (Türkiye saati)  
**Durum:** ÖNCEDEN YAZILMIŞ DENEY PLANI — UYGULAMA / CANLI KABUL HENÜZ YOK  
**Dal:** `experiment/263-toplu-karsilastirma`  
**Birincil pilot:** `experiments/263/M4_PILOT_PROTOCOL.md` — B, C2, C3, M4, 100 yeni yerel lig maçı.

## 0. Araştırma sorusu ve sınır

Kullanıcı amacı: büyük getiriyi kovalamak değil, az sayıda ve daha güvenilir görünen **tekli** seçimi ayırarak mütevazı bir kazancın mümkün olup olmadığını **risk almadan önce** ölçmek. Sabit gelir, garantili kazanma veya günlük bahis mecburiyeti vaadi yok.

Bu deney ana 100 maç pilotunun yerini almaz; onun **önceden mühürlenmiş**, aynı maç ve aynı pre-kickoff girdilerini *salt okunur* tüketen ayrı bir `shadow` karar defteridir. B/C2/C3/M4 model kodu, hiperparametreler, `m4_lock.json`, kaynak tarihsel kabulü, maç öncesi kayıtlar ve `main` **DEĞİŞMEZ**. Model sıralaması veya terfisi yapılmaz. Modül 0 yeniden çalıştırılmaz. Yeni bir risk tahmin modeli yaratılmaz. İlk 11 henüz açıklanmamış diye dört modelin hesaplaması durdurulmaz; seçim kararında hangi bağlamın kontrol edilmediği görünür olmalıdır.

Önemli: %75 gibi ham model olasılığı gerçek %75 güvenilirlik anlamına gelmez; dört model ortak veriden beslendiğinden birbirleriyle uyuşmaları da bağımsız kanıt sayılmaz. Resmî `A/B/C` hâlâ **ONAYSIZ** (`official_class=null`). Bu gölge deney bahis tavsiyesi/otomatik bahis veya yüksek güven onayı üretmez.

## 1. Veri akışı — T−60, aynı kesim ve iki ayrı kayıt

1. 10 kapsam ligi ve kullanıcının önceden belirlediği karşılaşmalar. Resmî başlangıç saati, takım kimliği, doğrulanmış geçmiş veri/tarih kesimi, kadro açıklanma durumu, eksiklikler ve haberler yeniden kontrol edilir. Son maç golleri/rakip gücü B/C2/C3/M4'ün içine zaten girebileceğinden yeni çarpan olarak **tekrar eklenmez**.
2. Maçtan önce B/C2/C3/M4 ayrı ayrı hesaplanır ve **ana pilot tahmin JSON'u**, kod/veri SHA ve gerçek GitHub commit kanıtıyla mühürlenir. Dört modelden biri `UNAVAILABLE` olabilir, veri uydurulmaz. Bu aşama mevcut pilotun görevidir.
3. Karar katmanı mühürlenmiş snapshot'ı **salt okunur** alır. Aynı kesimden 1X2 (1/X/2), tam maç 2.5 alt/üst ve KG var/yok adaylarını inceler. Çoklu kombine ve ilk yarı korner yok. Her maçta en fazla **1** sanal tercih. Çifte şans 1X/X2/12, 1.5 ve diğer pazarlar fiyat/karşı-odds kıyaslanabilirliği nedeniyle bu ilk gölge protokolün DIŞINDA; ana 17-bölüm raporunda gösterilmeleri engellenmez.
4. Analiz anında oran gerçekten erişilebiliyorsa kaynak/site, **URL, saat damgası ve tam karşı pazar oranları** kaydedilir; analiz anından en fazla **10 dakika eski** olmalıdır. MS: 1/X/2 aynı siteden; 2.5 alt/üst ve KG var/yok aynı siteden karşı fiyatlar. Kaynak gerçekte bağımsız kontrol edilmediyse `PRICE_NOT_VERIFIED`; fiyat uydurma ve tek fiyattan no-vig/EV üretme YASAK.
5. Maçtan **önce** ikinci ayrı `SHADOW_PREMATCH_LOCKED` karar kaydı GitHub'da commit edilir. Seçim, pas ve gerekçe tüm maçlarda görünür olur. Birkaç aynı saatli maçın toplu işlenmesi mümkündür. Tahmin ve seçim dosyası kickoff sonrası geriye dönük doldurulmaz; yetişmeyenler `NO_VALID_PREMATCH_LOCK`.
6. Maç sonunda resmî skor doğrulanır; hem ana pilot performansı hem ayrı **gölge seçim sonucu**, orijinal kayıtları değiştirmeden sonuç defterine eklenir. Ön kayıt bir kez yapılır, tekrar hesaplama veya kullanıcı sezgisine göre sonradan geçmişe dönük seçki değişmez.

## 2. Önceden sabit iki gözlemsel filtre (hipotez, güven sertifikası değil)

Aynı **en fazla bir** pazar ve yön, seçim yapılmadan önce tutarlı kural ile sabitlenir. Öncelikle uygun pazarları ayrı ayrı değerlendir, S1/S2'yi karşılaştır:
- **S1 — yüksek olasılık / uyum GÖLGE:** Pazar için geçerli B/C2/C3/M4 modellerinden **en az 3'ü** olasılık sağlamalı. Bu modellerin **her biri** ilgili sonuç için `p >= 0.75` vermeli; aralarındaki `max(p)-min(p) <= 0.10`; her geçerli modelde gol λ'larının birbirinden bağımsız ±%10 köşe ve baz senaryoları kullanılarak `min stress probability >= 0.70`. Bunlar eski A adayının %75 ve %70 duyarlılık koşullarından gelir; 10 puanlık modeller arası fark ayrı *önceden tanımlanmış deneysel* sınırdır, başarı ölçülmeden güven puanı diye sunulmaz. Veri/saha kimliği, saat, kaynak ve ilgili hesaplar sahici olmalı. Olasılık hesabı mümkün değilse `NOT_EVALUABLE`, zorla düşük-risk etiketi yok.
- **S2 — S1 + fiyat/değer GÖLGE:** S1 koşullarının **hepsi** ve aynı analiz anında **bağımsız doğrulanmış eksiksiz** pazar karşı fiyatları olmalı. Her geçerli model için `p * decimal_odds - 1 >= 0.05` **ve** `p - normalized_no_vig >= 0.03`; değerlendirilen model sonuçlarının hepsi eşiği karşılamalı. Oran erişilemiyorsa S1'in açıklayıcı gözlemi korunur, **S2=NOT_EVALUABLE**; oranı sıfır ya da tahmini sayma. S1 geçen ama S2'yi geçemeyen maç bahis avantajı gösterilmiş sayılmaz.
- **Kadro/belirsizlik gözlemleri:** Resmî ilk 11 henüz açıklanmadıysa `LINEUPS_UNANNOUNCED` olarak yaz, dört-model analizini durdurma. Doğrulanmış son dakika kritik kadro/sakatlık bilgisi hem kaynağı/zamanıyla kaydedilir hem sonraki gözlemsel yorum için saklanır; bu aşamada sayısal olasılığı elle değiştirme. Kritik bilgi karşılaştırmasının *eksik olması* seçimi otomatik düşük-risk diye etiketlemez.
- **İstikrarsız takım:** Son beş maç golleri/sonuçlar, rakip kalitesi ve oynaklık yalnız açıklayıcı saha olarak kaydedilir. Liverpool örneği gibi farklı skorlar tek başına modelin tahmin yüzdesini düşürmez veya maçı elemez. Bu göstergenin işe yaradığı kanıtlanmadığı için S1/S2 içine henüz matematiksel koşul olarak konmaz.
- **Birden çok seçim S2'yi geçerse:** Önce (mevcut geçerli modeller için) `minimum_EV` en yüksek olanı, sonra `minimum_p` en yüksek olanı; eşitlikte pazarlar MS1, MSX, MS2, UNDER_2.5, OVER_2.5, BTTS_NO, BTTS_YES yazılı sırası. S1'de `minimum_p` en yüksek olan, eşitlikte aynı sabit sıra. Hiçbiri geçmezse `PASS` (pas). Bu bağlayıcı sıralama sonuç gördükten sonra seçimi değiştirmeyi önler.
- **Katman ayrılığı:** S1 ve S2 her maç için iki farklı **sanal defter** tutar. S2, S1'in altkümesidir; bir maçtan her defterde en fazla bir seçim seçilir. Ana dört-model tahmin defteri üçüncü ayrı nesnedir. Sonradan bir S1 seçimini farklı bir S2 seçimine dönüştürüp aynı defterde iki kez sayma yok.

### Not: ileri model uyumu ve yüksek seçici eşik

C2'nin sık `UNAVAILABLE` kalabileceği biliniyor; en az üç geçerli model kuralı nedeniyle kapsam az olabilir. **100 maçta sıfır/çok az seçim** çıkması başarısızlık değil önceden belirlenmiş `INSUFFICIENT_SAMPLE` sonucudur; eşiği oynatmayız. Diğer model yokken tek M4/C3 yüzdesini üç bağımsız görüş gibi saymayız. Model sonuçları bağımsız değildir.

## 3. Sanal risk ve ödeme hesapları (gerçek para yok)

- Başlangıç sanal kasa: **1.000 birim**; **seçilen her tekli** için sabit **10 birim**. Her iki defterin kasası *ayrı*. Seçim yoksa 0 birim. Gerçek ödeme, bahis yerleştirme, artış/katlama, kayıp telafisi, kupon birleştirme, günlük harçlık hedefi, otomatik para transferi **YOK**.
- Yalnız doğrulanmış analiz-anı oranı varsa net sonuç: kazanırsa `10*(oran-1)`, kaybederse `-10`. Oran yoksa `UNPRICED / ROI_NOT_EVALUABLE`, sahte 1.35 gibi oran atanmaz; S2 için zaten seçim olmayacak.
- Başabaş: `1/decimal_odds`. Örnek 1.35 için yaklaşık %74,1; %75 nominal model olasılığı çok küçük marjdır ve **gerçek kalibrasyon kanıtı yoktur**.
- **Ayrı tut:** İsabet başarısı (seçilen ve sonuçlanan maçlar), fırsat/kapsama (seçilen / pilot 100), net sanal birim, ROI = net sanal / toplam sanal stake, ortalama oran, en büyük düşüş, ardışık kayıp, lig/pazar kırılımı, başarısız veri/oran doğrulama sayısı.
- Seçilmiş maçların yalnız isabeti vs tüm maçların en yüksek p seçiminin isabeti **tanımlayıcıdır**; farklı pazar/örneklemden sebepsel üstünlük kanıtı çıkmaz. Pazar bazında ve aynı seçim günü gözlemlerinde kontrol analizleri yapılır; 100 maçlık filtre net kazancı istikrarlı gelir kanıtı değildir.

## 4. Deney değerlendirmesi ve dondurma kuralı

- **0. aşama:** Bu dokümandaki eşikleri uygulama başlamadan kesinleştir; model kodlarına dokunma. Gölge kayıt sözleşmesi: `match_key`, `official_fixture_source`, `kickoff_utc`, `locked_forecast_sha`, `forecasts_commit_sha`, `shadow_decision_sha`, `shadow_commit_sha`, `asof_utc`, `data_status`, `lineups_status`, `risk_notes`, `model_availability`, `candidates`, `chosen_market`, `S1_status`, `S2_status`, `reason_codes`, `price_snapshot`. Bunlar kayıt olmadan pas/geçme kanıtı değildir.
- **1. aşama:** Mevcut 100 maç pilotunun ilk yeni yerel lig maçında (hedef 6 Kasım Cuma) T−60 gerçek veri ve odds koşullarını doğrula; temel dört-model kilit ile **iki ayrı** karar defterini kickoff öncesi SHA ve commit ile yaz. Başarısızsa gerekçe raporu, sahte kilit yok.
- **2. aşama:** Aynı saatli maçlarda bir kez toplu kaynak/kod/kimlik veri kesimi; model başına tek karşılaştırma, maç başına bağımsız `PASS`/aday. Bir maçın veri sorunu diğerini engellemez. Saat alarmının kendisi **kilit değildir**.
- **3. aşama:** Pilot 25 maçta yalnız kayıt bütünlüğü, zaman sızıntısı, odds eşleştirme, duplike ve veri açığı denetimi; **eşik optimize etme yok**.
- **4. aşama:** Pilot 100 sonuçlandıktan sonra **tek birleşik rapor:** B/C2/C3/M4 doğruluğu/kalibrasyonu, S1 seçici isabet/kapsama, S2 doğrulanmış oranla sanal ROI, belirsizlik aralığı/örneklem, pas geçen maçların karşılaştırması, en kötü kayıp ve örnek sayısı. Eşik değişikliği veya yeni ölçü ancak **gelecek ve bağımsız** yeni pilot sürümü olabilir. 100 maç yetmezse daha uzun ileri pilot önerilir, sonuç uydurulmaz.

## 5. Kabul ölçütü

**Başarı iddiası için yeterli değildir:** yüksek tahmin yüzdesi, dört modelin anlaşması, tek hafta iyi ROI, birkaç kazanılmış kupon, sadece 100 maç veya yazılım CI'nın yeşil olması.

**İlk deney kabulü:** (a) T−60'daki tahmin ve gölge karar *sonuçtan önce* gerçekten SHA+commit ile kilitlenmiş, (b) veri/oran kaynağı ile zaman damgası dürüst, (c) her maçın seçilme/pas nedeni tekrar üretilebilir, (d) skor sonradan ayrı kayıt edilmiş, (e) 25'te teknik kabul ve 100'de istatistiksel değerlendirme ayrı. Bu koşullar sağlansa bile **kârlı veya güvenli bahis yöntemi kanıtlanmış sayılmaz**.

## 6. Yapılmadı / yapılmayacak

Bu belge **plan ve ön kayıt ilkesi** oluşturur. Herhangi bir gerçek maç için seçim, canlı bahis oranı doğrulaması, yeni GitHub Action, alarm, otomatik T−60 çalıştırıcısı, dört model tahmini, shadow JSON veya sonuç raporu **OLUŞTURMADI**. Canlı sistemde resmî A/B/C onayı etkinleşmedi; gerçek para ve otomatik bahis altyapısı yoktur. Bu doküman sistemin başlama koşulu değil, ileri pilot başlamadan önce ayrı seçim katmanı uygulamasına esas alınacak taslaktır.
