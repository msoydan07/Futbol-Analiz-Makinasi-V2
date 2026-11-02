2.6.3 — Piyasa referansı (2 Kasım 2026)

Kullanıcı fikri: tek analiz anında gözlenen 1/X/2, KG veya 1.5/2.5/3.5 Alt/Üst bahis şirketi fiyatlarını marjdan arındırıp B/C2/C3/M4 olasılıklarıyla karşılaştır.

Uygulama: 1/oran ham olasılık, tüm birbirini dışlayan karşı oranların toplamına bölmek no-vig referansı verir. Her model için fark (puan), ortalama mutlak sapma, teorik adil oran (1/model olasılığı) ve yalnız aritmetik EV gösterilir. Tek seçimde en yakın ile tam pazarda en yakın farklı olabilir. Piyasaya yakınlık güvenilir tahmin veya pozitif değer kanıtı değildir.

Güvenlik: fiyat analiz anında en fazla 10 dakika eski olabilir; tam karşı oranlar ve aynı maç/pazar/kaynak-zaman gerekir. Gerçek bağımsız canlı fiyat doğrulama kaynağını bu kod kendisi sağlamaz; yalnız var olan kontrol arayüzünü okur. Kontrol bayrağı kendi başına doğrulama kanıtı değildir. Oranlar yoksa sonuç DOĞRULANAMADI. Matematik motorları değişmez; piyasaya yakın model seçilip terfi ettirilmez; C2 kanonik kalır; A/B/C değiştirilmez; ileri pilot / tahmin kayıtları oluşturulmaz. Main ve Salı zamanlayıcısı değişmez.
