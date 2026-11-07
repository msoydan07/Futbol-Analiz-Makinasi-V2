# 2.6.3 — 7 Kasım 2026 akşam mühendislik durum tutanağı

## Kullanıcının sabit kararı
Maç sabahı (Türkiye saati 05:00–12:59) kapsam 10 ligdeki önceden takip edilen maçların B/C2/C3/M4 analizi, aynı sabah The Odds API üzerinden yalnız gerçek Pinnacle h2h/MS 1-X-2 oranı, marjsız hesap, kaynak zamanları ve GitHub SHA mührü. T−60 zorunluluğu YOK. İlk 11 bulunmaması analiz engeli DEĞİL. Resmî pilotta geçmişe dönük tahmin eklemek yasak.

## Bu oturumda yapılan değişiklikler
- Belgium Next.js sentetik maç kaynağı testindeki hatalı Python çok satırlı nesne düzeltildi. Belgede olmadan testlerin yeşil olması canlı kaynak güvenilirliği demek değildir.
- EFL 2026/27 resmî TV yayın seçimi tablosunu okuyabilen ayrı PARÇALI Championship okuyucusu eklendi. Yalnız EFL resmî sayfasında gerçekten yazılı "Championship / tarih / saat / ev / V / deplasman" satırları kullanılır; Premier/League One sızmaz. Çelişkili çift kayıtlar reddedilir. Kaynak: https://www.efl.com/news/2026/july/30/see-the-latest-sky-sports-tv-selections/
- EFL ana canlı resmî maç merkezi JS-only olduğunda, yukarıdaki resmî TV sayfası yalnız varsa ek doğrulama sağlar; seçilmemiş diğer lig maçlarına otomatik saat uydurulmaz. Aynı canonical ID ve live named-gate zorunluluğu korunur.
- Sabah 10 lig ön-denetim raporu artık kullandığı ayrıştırıcıyı ve EFL/Portekiz/Belçika fallback durumunu ayrıca gösterir.
- Önceki Portekiz resmî Kasım 2026 haber kaynağı ve Belçika Next.js kaynağı korundu; tarih kısıtları veya takım eşleştirme kapısı aşılmadı.

## Kanıt
- 7 Kasım 2026 / GitHub Actions 42373904793: **181/181** sentetik entegre test yeşil (EFL TV yedek okuyucusu 6 test içerir).
- 7 Kasım 2026 / GitHub Actions 42374005423: **10 ligin tamamı** resmî kaynak ön-denetiminden geçti. Kontrol anında maçların bir kısmı başlandığı için, 44 sabah adayının yerine **henüz başlamamış 31 benzersiz saatli kanonik aday** görüldü. ENG1=3, ENG2=0, GER1=5, ESP1=4, ITA1=4, FRA1=2, NED1=3, TUR1=3, POR1=3, BEL1=4. Bu 31 aday **henüz 31 mühür veya 31 doğrulanmış tam analiz değildir**.
- ENG2: EFL /matches/ sayfası GitHub koşucusunda sunucu tarafından dönen JS "Loading..." içeriğiyle maç vermiyor. EFL resmî TV yedek kaynağı bu canlı koşuda da saatli kanonik aday üretmedi. Nedeni otomatik raporda fallback statüsüyle saklanacak. EFL.com sayfalarının web aramasında erişilebilir olması GitHub Actions'ın onları okuyabildiğini kanıtlamaz.
- Bu oturumda yeni gerçek pilot tahmini 0; Pinnacle API kredi harcaması 0; eski 44 araştırma maçı ve ana 96/100 pilot kayıtları değiştirilmedi.

## Açık kalan işler — değiştirilmemeli
1. **ENG2 tam kapsam:** Yalnız resmî yayın seçimi sayfası bütün Championship maçlarını kapsamaz; resmî tam fikstür veya resmî kulüp sayfaları için makinenin okuyabildiği güvenilir canlı API/HTML bulunana dek ENG2'nin geri kalanı eksik kaynak olarak raporlanmalı. Aynı kaynak hatasını kod değişmeden tekrar tekrar sorgulama.
2. **Otomatik pilot tetiklemesi:** 10 lig ön-denetimi yalnız kanonik resmî sayfa ADAYI üretir; yeni100 hattı hâlâ bugün kullanıcı adıyla/önceden onayla Git-push edilmiş manifest ister. İkisini otomatik uçtan uca bağlandığını iddia etme.
3. **Tek gerçek sabah kabulü:** En erken 8 Kasım 2026 Pazar sabahında, gerçek resmî maç kapısını geçmiş takım/KO, dört model, Pinnacle güncel sabah fiyatı, SHA mühür, mobil rapor ve ödemenin/kredinin tek lig/gün kilidini aynı job altında doğrula. Bugün öğleden sonra geçmişe dönük sabah kaydı oluşturma. İlk gerçek olumlu kabul olmadan "tam otomatik" demez.
4. Başka bir tekrar testinden önce **son doğrulanmış durum / kapanmamış engel / tek sonraki eylem** defterini güncelle.

**Git dalı:** experiment/263-toplu-karsilastirma. Main/üretim matematiği değişmez. Bu kaynak/yedek okuyucu entegrasyonu, bahis seçim yetkisi vermez.
