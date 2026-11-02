# M4 / B–C2–C3–M4 | Tek toplu mühendislik kabul raporu
**Tarih:** 2 Kasım 2026 (TSİ)  
**Proje:** Futbol Maç Analiz Makinası 2.6.3  
**Deney dalı:** `experiment/263-toplu-karsilastirma`  
**Yeni toplu kabul:** [GitHub Actions #41365258677](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41365258677) — **7/7 test başarılı**.

## Kesin hüküm
**M4 yazılım çekirdeği + dört modeli aynı maç önünde ayrı kaydeden deney protokolü kabul testinden geçti; matematiksel üstünlük henüz kanıtlanmadı.** Yüz maçlık gerçek ileri pilot henüz başlamadı, hiçbir model ana sisteme taşınmadı ve resmî A/B/C, EV ya da bahis getirisi onaylanmadı.

## Denetlenen kaynaklar ve önceki işlerin korunması
- **DOĞRULANDI:** Dondurulmuş `historical_results.csv` 4.413 maç, 10 lig, 2025/26'da 3.533; 2026/27'de 880 maç. Son veri günü **29 Ekim 2026**. SHA-256: `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`. ZIP GitHub run `41251343847`, artifact `13061725424` içinden alındı. Kaynak içinde doğrulanmış maç tarih, taraf, gol, sonuç alanları var.
- **DOĞRULANDI:** Arşivde xG/xGA sütunları bulunmuyor. Şut/kaleyi bulan şut alanları önemli ölçüde mevcut (deplasman şut/kaleyi bulan şutta 4.412/4.413), ancak eski C4 ek faydası gösterilmediğinden M4 v1'e ayrıca güç çarpanı olarak eklenmedi. xG olmadığı hâlde xG katkısı varmış gibi yapılmadı.
- **KORUNDU:** B/C1 = `exp_263_batch.c1`; C2 = `analysis_math_core.canonical_c2_lambda` (k=5; w=0,5; bağlam min. 4); C3 = `exp_263_batch.fit_c3/predict_c3` (Ridge=6). Bunların kaynak dosyaları değiştirilmedi. Eski C3, xG, şut, ilk yarı ve korner tarihsel backtest'leri tekrar çalıştırılmadı.
- **KORUNDU:** `main` commit `ec6b02b8406b4b9320a74f32a5166d7d3a87fb03`; yalnız deney dalı ilerletildi. Yeni otomatik fikstür taraması veya Modül 0 yazılmadı. 2.6.3'ün maç sonu korner bölümü korunuyor; bu dört modelin yalnız gol pazarları değerlendirmesi, korner modeline onay değildir.

## M4 öğrenme tasarımı
Tek bir ortak Poisson gol modeli iki ayrı `λ_ev` ve `λ_dep` üretir. Öğrenilen etkiler: lig iç/deplasman taban seviyesi, takımların ortak hücum ve savunma katsayıları, iç/dış saha takım bağlamı, karşı rakibin bir kez hesaba katılması ve eski maçlara azalan zaman ağırlığı. Ek parametrelerin cezaları düzenlileştirmedir; model B/C2/C3 olasılıklarını birleştirmez. Bütün 1X2, KG, 1.5/2.5/3.5 gol ve en olası skor olasılıkları bir ortak gol dağılımından hesaplanır.

**Parametre seçimi:** Önceden sabit 12 aday (yarı ömür 90/180/360 gün × ortak Ridge 4/12 × saha Ridge 12/48) sadece **2025/26** tarih sıralı 3 gelişim bloğunda kıyaslandı. 2026/27 bu seçimden çıkarıldı. Geçerli gelişim değerlendirmesi **702 maç**, seçilen ayar **360 gün / Ridge 4 / Ridge 48**. Seçilen ayarın gelişim **1X2 log-loss=1,0106594**, **çok sınıflı Brier=0,6022883**. Adaylar arasında 701–702 maçlık ufak kapsama farkı mevcut; bu sayılar kesin üstünlük veya ileri sonuç göstergesi olarak kullanılmaz. Sabit ayarlar, tüm adayların geliştirme özetleri ve M4 kaynak SHA-256 değeri `m4_lock.json` içinde kilitlendi.

**Sınırlar:** xG, kadro, oran, ilk yarı ve korner M4'ün öğrenilmiş λ bileşenleri değildir. İlk 11 yokluğu hesaplamayı engellemek zorunda değildir, ancak doğrulanmış kadro varmış gibi sunulamaz. Güncel sezon gelişimi modelin günlük olarak geçmiş maçlardan refit edilmesini sağlar; **hiperparametreler pilot süresince değiştirilmez**. İlk modelin kalibrasyonu bağımsız gelecekte henüz doğrulanmadı.

## Dörtlü ileri kayıt protokolü
- Bir **kullanıcının adlandırdığı tek maç** resmî doğrulama kapısından geçmek zorunda; resmî kaynak, takım kimlikleri, tarih ve maç başlangıcından önceki kontrol zamanı geçersizse yazma işlemi durur. Sahte kullanıcı fixture JSON'u gerçek CLI'dan alınmaz.
- **B, C2, C3 ve M4** aynı veri dosyası/tarih kesiti üzerinde ayrı `status`, olasılıklar, mümkün olan λ, gol pazarı, kayıt zamanı, snapshot SHA, kod SHA ve M4 ayar kilidi ile tek JSON'da yer alır. C2'nin minimum bağlamı yoksa `UNAVAILABLE`; diğerlerini etkilemez.
- Kayıt en fazla 100 yeni tek-maç dosyası, `open('x')` ile üzerine yazmama ve JSON SHA-256 ile değişiklik tespiti uygular. Dosyanın GitHub'a **kickoff öncesi normal commit** edilmesi ayrıca operasyonel gerekliliktir; local dosya oluşumu kendi kendine Git commit değildir. Depo yöneticisinin geçmişi force-push etmesini mutlak engelleyemez.
- Frozen 4.413 SHA dışındaki yenilenmiş veri, geçmiş 4.413 satırın eşleşmesi ve insanca kontrol edilmiş kaynak/onay belgesi olmadan kabul edilmez. Böyle bir belgenin varlığı otomatik gerçek-kaynak doğruluğu kanıtı değildir; Salı otomatik yenilemesi doğrulanmış sayılmaz.
- Sonuç değerlendirmesi **yalnız maç sonunda**, kaydedilmiş pre-kickoff SHA'dan hareketle 1X2 log-loss/çok sınıflı Brier/başarı, KG ve 2.5 üst ikili log-loss/Brier, kapsama, dört model ortak örneklemi, lig bazında rapor ve gün bloklu bootstrap hazırlar. Tahmin dosyalarına dokunmaz.

## Tek toplu kabul testi ve hata kaydı
- İlk Actions koşusu `41365094057` Python önbelleği için gereksiz requirements aramaktan test aşamasına gidemedi; yalnız CI yapılandırması düzeltildi.
- İkinci koşuda `41365153803` testlerden 6'sı geçerken C2'nin `MS1/MSX/MS2` alanları ortak `1X2` sözleşmesine uymadığı için sonuç değerlendirici hata verdi. Aynı koşu `tee` yüzünden yanlışlıkla **yeşil görünüyordu**. Her iki sorun **topluca** düzeltildi: C2'ye sadece alan adaptörü eklendi; kabuk test komutuna `set -o pipefail` eklendi. C2 matematik formülü değiştirilmedi.
- **Son kabul:** Actions `41365258677`, commit `5d141d6f3721e16a0cfda527ed3f4172e8e9ff2f`, gerçek SHA-pinned arşiv indirildi, **7/7 yeni birim/entegrasyon kontrolü geçti**, CI gerçekten test adımını başarılı olarak doğruladı. Kontroller: Poisson pazar tutarlılığı, frozen veri/parametre kilidi, dört model kaydı ve overwrite koruması, 2026/27 sonuçlarıyla M4 ayarının değişmemesi, aynı maç günü sızıntı engeli, hatalı resmî kapının reddi, maç sonu değerlendirme ve değiştirilmiş kayıt reddi.
- Bu kabul **bir ileri tarihli gerçek resmî fikstürün tahmininin GitHub'a otomatik kaydedildiğini**, saha verisi güncelleme hattının çalıştığını veya 100 maçlık bahis avantajını göstermez. Eski yeşil testler yeniden koşturulmadı.

## Kalan kabul koşulları
**HENÜZ YAPILMADI:** (1) 3 Kasım Salı güncel veri ekinin gerçek kaynaklardan doğrulanması ve yeni snapshot kabulü; (2) ilk resmî adı verilen maç için dört modelin başlamadan önce tek JSON üretmesi, SHA ve Git commit kanıtı; (3) tüm 100 gerçek maçta sonuç tamamlanınca ortak örneklem performansı ve bloklu belirsizlik aralıkları. **25 maçta yalnız operasyonel kontrol** yapılır; parametre değiştirilmez. 100 maç sonu M4 B/C2/C3'e üstün değilse ana motora terfi ettirilmez. Güçlü iyileşme görülse bile daha uzun bağımsız ileri dönem doğrulaması gerekebilir.

**Nihai mühendislik kararı:** Deney altyapısı **KABUL — DENEYSEL**; ana motor değişikliği **RET**; 100 maç sonucu ve istatistiksel üstünlük değerlendirmesi **BEKLEMEDE**.
