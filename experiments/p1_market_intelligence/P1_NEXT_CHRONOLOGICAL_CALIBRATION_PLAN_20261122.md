# P1 — 22 Kasım 2026, kronolojik kalibrasyon mühendislik planı

**Ana sistem dokunulmaz:** M4/C3, 2.6.3, mühürler, karar v4 ve ana GitHub dalına değişiklik YOK.

## Gerekçe
Kullanıcının İngiltere 2025/26 (380), İngiltere LS (380), Almanya LS (306), İspanya LS (380) toplam **1.446 geçerli oran+sonuç** toplu yerel raporunun ağırlıklı incelemesinde P1 **904**, P0 **898** ana isabet elde etmiş; P0, Brier 0.514179 ve log-loss 0.774348 ile P1'in 0.515033 / 0.775550 değerlerinden az farkla önde. Bu sayılar **kalibrasyon öğrenildiği anlamına gelmez**; müşahhas olasılık aralıkları ve maçların eşleşik sonuçları yalnız TXT özetinden geri çıkarılamaz.

## Sonraki kontrollü deney

- Önce resmi manuel **Almanya 2024/25** ve **İspanya 2024/25**, her biri Odds + Scores tam XLSX çiftlerini edinme. Önceki iki İngiltere sezonu, Almanya/İspanya 2025/26 dosyaları kullanıcı bilgisayarında kalır.
- Altı **ayrı** klasörde her lig/sezon için sadece ilgili Odds + Scores XLSX. Gerçek `Season` sütunu doğrulanır; dosya adı veya `LS` tek başına kesin sezon değildir.
- **2024/25 yalnız kalibrasyon öğrenimi**, **2025/26 yalnız daha yeni bağımsız test**. 2025/26 test sonuçlarına bakıp parametre tekrar ayarlamak yasak.
- Yedi olasılığı tek ortak normalizasyon gibi davranma: MS üçlü, Alt/Üst ikili, KG ikili. Her pazar için P0/P1 ayrı sıcaklık katsayısı 2024/25'ten öğrenilir; sabit parametreler sonraki sezonlara uygulanır.
- Rapor: P0/P1 ham ve kalibre Brier, log-loss, ana tercih isabeti; pazar ayrımları, olasılık aralıklarında beklenen/gerçek oran; aynı maçların **takvim haftası blok bootstrap** eşleşik fark aralıkları. Bunlar açıklayıcı istatistiklerdir, kâr garantisi değildir.
- Bütün hesaplar **kullanıcının bilgisayarında çevrimdışı**; GitHub'a ve sohbete ham Footiqo XLSX yüklenmeyecek. Kullanıcı yalnız kişisel araştırma için izinli manuel export yapar, otomatik web toplama yok.

## Yerel paket durumu

2026-11-22 tarihli `P1_2024_2025_Kalibrasyon_Yerel_Paket.zip` **ayrı sohbet dosyası olarak üretildi**, **GitHub deposuna yüklenmedi**. SHA-256 `039965d0545cafe0c63b7ad9af570808e8540c1d840b3f8472c54eaeb76f8866`; Python 3.11+ stdlib, çevrimdışı Windows BAT, XLSX okuyucu, matematik motoru, zaman ayrımını zorlayan kalibrasyon kodu, dört sentetik birim testi ve kullanım notu içeriyor. Lokal sentetik testler **4/4 geçti**; ancak gerçek altı sezon XLSX üzerinde uçtan uca çalıştırma **henüz yapılmadı**. Bu nedenle kalibrasyonun gerçek veri sonuçları **beklenmektedir**. GitHub'da bu yeni paket için CI çalışmış gibi rapor verilmeyecek.

Kaynak fiyatlarının orijinal pre-match gözlem zamanı hâlâ bağımsız sertifikalı değildir; tek bahis şirketi bilgisi kaynak sağlayıcı beyanıdır. Kapı: gerçek dosyalar + kontrollü test + eşleşik ve tarih sıralı denetim + lisans.
