# 2.6.3 M4 ve B/C2/C3 — ön kayıtlı dörtlü pilot

**4 Kasım 2026, maçlar başlamadan yapılan kullanıcı onaylı REVİZYON:** Eski hedef 100 iken şimdi [96 maçlık sabit 6–8 Kasım kohortu](../../docs/263_96_mac_hafta_sonu_2026_11_06_09_pazartesi_degerlendirme.md) esastır. 9 Kasım'da geçerli gerçek kayıt sayısı N üzerinden tanımlayıcı rapor yapılır. Üç ayrı maç günü, 10+ gün gerektiren tarih-blok güven aralığı veya kesin model üstünlüğü için yetersizdir; model terfisi yok.

**Sadece deney dalı:** `experiment/263-toplu-karsilastirma`. `main` ve eski modeller değiştirilmez.

## Dondurulan çalışma

- Geçmiş arşiv: 4.413 gerçek maç, 10 lig, SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- M4, geçmişten öğrenilen log-lineer iki gol ortalaması üretir. İki lig intercept'i, lig içinde takım hücum/savunma bileşenleri ve iç/dış saha özelleşmeleri rakibi ortak Poisson kaybıyla bir defa hesaba katar. Önceki maçlar zaman aşınmalı ağırlıklarla kullanılır. Kayıp xG/şut/sakatlık yok sayılmaz; M4'ün ilk sürümünün girdi kapsamına **alınmaz** ve raporda eksik/karşılaştırma dışı olarak açıklanır.
- 12 aday yapılandırması **önceden tanımlandı**. Sadece 2025/26 sezonunda üç gelişim zaman bloğunda kronolojik doğrulama ile seçildi: (15 Kasım–6 Aralık 2025), (15 Ocak–5 Şubat 2026), (15 Mart–5 Nisan 2026). Geliştirme karşılaştırmasında 702 geçerli maçın ortalama 1X2 log-loss'u 1,010659; Brier'i 0,602288 çıktı. Bu **bağımsız ileri doğrulama değildir**. 2026/27 parametre seçiminde kullanılmadı.
- Sabit seçilen M4 ayarı: 360 gün yarı ömür, ortak Ridge=4, saha bağlamı Ridge=48. Ayar dosyası `m4_lock.json`, çalışan M4 kodunun SHA-256'sını içerir. Elle ağırlık eklenmez.
- B = mevcut `exp_263_batch.c1`; C2 = mevcut `analysis_math_core.canonical_c2_lambda`; C3 = mevcut `exp_263_batch.fit_c3/predict_c3`, Ridge=6. Bu formüller değiştirilmez.

## İleri pilot

- 6–8 Kasım 2026 tarihli **96 sabit fikstür adayı**; gerçekten oynanmış ve maç öncesinde mühürlenmiş olanlar sayılır. Liste dışı maç veya sonraki hafta telafi eklenmez. Otomatik maç keşfi/modül 0 yok. Resmî kaynak teyidi, gerçek başlama saati ve güncel veri gereklidir.
- Maç başlamadan tek dosyada dört modelin ayrı olasılıkları, durumları ve λ değerleri (varsa), kaynak kontrol zamanı, veri/kod/hash, m4 lock, Poisson kuyruğu kaydedilir. `open('x')` sessiz üzerine yazmayı engeller. Git commit'i gerekir; yerel dosya tek başına kalıcı değil. Yetkili force-push'ı mutlak engelleyemez.
- Girdi sonucu aynı gün olsa dahi model sadece **maç gününden önceki** tam maçlara bakar. Pilot maçının sonucu katsayı öğreniminde kullanılmaz. 2026/27 veri güncellendikçe yalnız geçmişte tamamlanan maçlar yeni ileri tahminlerin girdisi olabilir; pilot boyunca hiperparametreler sabittir.
- C2 minimum 4 ev/deplasman maçı koşulunu sağlamazsa `UNAVAILABLE` yazar, M4'e doğrudan aktarılmaz. Hem toplam kapsama hem ortak dört modelin bulunduğu maç sayısı raporlanır.
- B/C3'ün eski 0–10 normalize skor yaklaşımı korunur ve açıklanır. C2/M4 daha tam Poisson dağılımı kullanır. İlk yarı/korner ve xG etki hesapları bu dörtlü deney kapsamında değildir.
- Sadece aynı maçlar için 1X2 log-loss, çok sınıflı Brier, en yüksek olasılıklı sonuç isabeti; KG ve 2.5 üst için ikili logloss/Brier ve basit kalibrasyon kovaları; günlük blok bootstrap ve lig ayrımı.
- 25 maçta yalnız veri/kod/hatalı olasılık kontrolü; modeli güncelleme yok. 96'de kapsamlı rapor ve manuel karar. 96 maç, kesin üstünlük veya bahis avantajı kanıtı sayılamaz. Oran, EV, bahis ve A/B/C onayı yok.

## Veri kabul politikası

Dondurulmuş arşiv kendi SHA ve satır sayısıyla kabul edilir. Değişmiş CSV ancak orijinal 4.413 maç **aynı verilerle** korunmuşsa ve güncel snapshot SHA, kaynak linkleri, inceleyen kişi, gerçek inceleme zamanı bulunan ayrı `HUMAN_VERIFIED_SOURCE_ACCEPTANCE` belgesi varsa kayıt oluşturabilir. Bu insan kaynak teyididir; otomatik harici doğrulama değildir. Salı yenilemesi yapılmış gibi iddia edilmez. Şüpheli içerik otomatik ana modele alınmaz.

## CI

Bir defalık yeni pakete özel CI dondurulmuş Actions artifact'ini indirir, SHA'yı kontrol eder, gelişim kilidi, M4 güvenlik ve dört model kayıt/sonuç değerlendirme testlerini **tek işte** çalıştırır. Önceki yeşil 2.6.3 entegrasyon testleri tekrar çalıştırılmaz. Başarılı CI yalnız yazılım güvenliği içindir, 96 maçlık gerçek sonuç kanıtı değildir.
