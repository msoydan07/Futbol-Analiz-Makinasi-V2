# 2.6.3 — Bahis Piyasası / Beşinci Referans (4 Kasım 2026)

**Durum:** YALNIZ ARAŞTIRMA + SALT-OKUNUR YAZILIM; canlı oran toplama ve geriye dönük kanıtsız bahis getirisi YOK.  
**Dal:** experiment/263-toplu-karsilastirma. Modeller B/C2/C3/M4 ve S1/S2 eşikleri değişmedi. `main` değiştirilmedi.

## Araştırma bulgusu
- Bahis şirketinin tek oranından `1/oran` hesabı **marj içerir**, saf gerçekleşme olasılığı değildir. MS 1/X/2 aynı kaynaktan ve aynı kontrol anında alınmalı; `p_i=(1/oran_i)/sum_j(1/oran_j)` yaygın bir marjsızlaştırma **yaklaşımı**dır. KG Var/Yok ve 2.5 Alt/Üst yalnız karşılıklı iki fiyat aynı anda varsa aynı şekilde. İddaa ve Nesine'nin kamuya açık sayfalarında fiyatlar görülebilmekle birlikte, otomatik API / tüm 96 maç ve üç pazar eksiksiz kapsama **doğrulanmamıştır**.
- Bu marjsızlaştırma **kusursuz piyasa olasılığı iddiası değildir**. Hegarty & Whelan (International Journal of Forecasting 2025) geleneksel MS piyasasında favori–sürpriz yanlılığı ve Asya handikabında daha yüksek etkinlik işaretleri raporlar; söz konusu gözlem tek bir maç için bahis değeri ispat etmez: https://www.sciencedirect.com/science/article/pii/S0169207024000670
- The Odds API geçmiş tarihe ait odds snapshot sunar; geçmiş veri ücretli pakettedir. Ücretli/hukuki erişim kabulü verilmeden sisteme bağlanmadı: https://the-odds-api.com/historical-odds-data/ . İddaa canlı kaynak: https://www.iddaa.com/populer-bahisler/futbol ; Nesine bülten: https://www.nesine.com/iddaa .

## Var olan kodu tekrar yazmadan yapılan

**Mevcut:** `classification_odds_263.py` gerçek fiyat kaynak/10 dakika/karşı pazar sözleşmesini, `market_benchmark_263.py` MS, KG, Alt/Üst no-vig ve dört modele uzaklık hesabını zaten yapıyor.

**Yeni:** `market_fifth_baseline_263.py` aynı maç için sonuçtan **sonra** veri olarak girilen tam kaynak kaydı, mevcut dört modelin mühürlü tahmini ve resmî maç sonucu iddiasını eşleştirip **MARKET'i beşinci rakip referans** olarak 1X2, KG ve 2.5 gol **log-loss / Brier / isabet** üzerinden aynı örneklemde puanlar. Geçerli olmayan oranlar `NO_COMPLETE_FRESH_QUOTE`; bulunmayan pazar `NO_SNAPSHOT_FOR_THIS_MARKET`; C2 yoksa C2'nin n=0 oluşu korunur. Hiçbir model yeniden fit edilmez, bahis/EV onayı verilmez, canlı tahmin kaydı yazılmaz.

**Güvenli veri sınırı:** Güncel kaynak gözlemi otomatik olarak gerçekleşmiyor. `source_review.method=MANUAL_PUBLIC_PAGE` bayrağı, URL, aynı bookmaker domaini, gerçek saat ve SHA ile denetlenir; bayrak/URL kendi başına **bağımsız kaynak veya GitHub commit zamanı kanıtı değildir**. Modül bu nedenle raporu her zaman `DESCRIPTIVE_ONLY_NO_LIVE_GIT_PROOF` olarak işaretler; gerçek ileri pilot iddiası için **gerçek kaynak sayfasının ayrıca incelenmesi ve commit'in kickoff öncesi GitHub üzerinden doğrulanması** gerekir. Gerçek oranlar yokken hayalî fiyat veya sonradan fiyat seçimi yapılmaz.

## Kaynak toplama önceliği ve hafta sonu basit iş akışı

1. **Oran önceliği eski kullanıcı kararı:** iddaa.com > Nesine > Bilyoner > Maçkolik > diğerleri. Yalnız gerçekten açılan ve aynı maçtaki **tüm karşı fiyatları** sunan kaynak; şirketler arasında karşı oran birleştirme yok. Daha yüksek EV'yi sonradan seçerek kaynak değiştirme yok.
2. T−60 grup kontrolünde **önce MS 1/X/2**. Aynı analizde KG Var/Yok ve 2.5 Alt/Üst bulunabiliyorsa ayrıca; bulunamazsa eksik. Kaynak URL ve TSİ/UTC kontrol zamanı, lig, canonical takım kimliği, başlama saati, fiyatlar, kontrol eden kişi tek snapshot'ta olmalı.
3. Önce dörtlü tahmin GitHub'da kickoff öncesi kilitlenir; sonra referans oran kontrolü/kayıt kimliği bu tahmine bağlanır. Oran ve seçim kayıtları kickoff öncesi GitHub'a gerçekten commit edilmeden, pazartesi skor bilgisini kullanarak 'önceden seçmiştik' denmez. Alarm ≠ kaydedilmiş bahis tahmini.
4. Pazartesi: 96 aday → geçerli dörtlü tahmin N → **aynı zamanda gerçek ve eksiksiz oranı kaydedilebilen** N_MS, N_KG, N_OU → MARKET vs B/C2/C3/M4 yalnız aynı N. Piyasa modeli daha iyi çıkarsa S2'nin az seçim bulmasını açıklayabilir; üç günlük gözlem tek başına uzun vade kanıtı değil.
5. S2, yalnız mevcut kilitli kurallarla değer varsa **sanal** tercih olarak kalır. Market ile modeli sonradan yeniden ağırlıklandırmak veya saha sonucundan filtre öğrenmek bu hafta **YOK**.

## Test/güvenlik
- Bu projeye özel testler yalnız sentetik fiyat ve sentetik skorlarla çalışır, canlı iddaa/Nesine oranı çektiğini veya gerçek parasal avantajı **kanıtlamaz**.
- Pre-kickoff forecast ve quote SHA uyuşmazlığı; fiyatın yanlış fikstüre/başka siteye ait olması; 10+ dakika eski fiyat; post-kickoff fiyat; eksik karşı taraf; sahte sonuç zamanı; veri üzerinde oynama reddedilir veya "değerlendirilemez" olur.
- Yalnız `market_fifth_baseline_263.py`, `test_market_fifth_baseline_263.py`, bu doküman ve bu özelliğe özel CI eklenir. Eski 96-maç/kod/model CI tekrar edilmez.

**Önemli açıklık:** Eşleşmiş gerçek 96 oran kaydı hâlâ 0; bu çalışma canlı scraper/API, otomatik yayın veya süper kârlı bahis tahmin motoru değildir.
