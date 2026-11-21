# P1 — Piyasa Zekâsı (bağımsız araştırma)

**Tarih:** 21 Kasım 2026. **Kural:** Ana Futbol 2.6.3 M4/C3, v4 karar katmanı, iş akışları, main ve önceden SHA mühürlü tüm tahminler değişmez.

Bu dizindeki kod standart Python 3.11 ile bağımsız çalışır. GitHub bahis API'si, Pinnacle, otomatik oran toplama, xG veya gizli maç verisi kullanmaz. Girdi yalnız kullanıcının iddaa.com ilk PDF'sinden önceden türetilmiş arşiv oranlarıdır. İlk PDF'nin özgün SHA referansı kontrol edilir; orijinal PDF baytları GitHub'da olmadığından otomatik bağımsız kaynak doğrulaması yapılamaz.

## P0
Her **ayrı pazar** için (MS1/X/2; 2.5 Alt/Üst; KG Var/Yok) ters oranlar önce kendi pazarı içerisinde normalize edilir. Karşılaştırılan marj arındırma yöntemleri: **oransal**, **additive** ve **power**. Yedi sonucu birden tek dağılım olarak normalize etmek yanlıştır; üç ayrı olasılık uzayı vardır.

## P1
İki parametreli bağımsız Poisson gol modeli, üç pazardaki P0 dağılımlarının **ortalama KL sapmasını en aza** indirecek şekilde optimize edilir. Çıktı: iki gol parametresi (gerçek xG değil), MS1/X/2, 2.5 Alt/Üst, KG Var/Yok, model–fiyat pazar uyum kalıntıları ve açıklayıcı en yüksek olasılıklı tercih. Skor dağılımı da seçilen Poisson parametrelerinden hesaplanabilir. **P1 oranların yeniden matematiksel ifadesidir; piyasanın dışında bağımsız bilgi eklenmez.** Bir uygulama sonucundan daha isabetli olduğu çıkarılamaz.

## Önemli veri sınırları
- 21 Kasım GitHub ikinci-PDF arşivinde **12** maç dosyası mevcuttu. **7** maçın üç piyasası da tam, **5** Almanya maçında Alt/Üst fiyatları yoktu; bunlar 7-sonuç araştırmasından **açık etiketle çıkarılır**, tahmini fiyat doldurulmaz.
- Eski arşiv alanı `OVER_UNDER_2_5` adı yanıltıcıdır: dizi sırası gerçek iddaa ayrıştırıcısına göre `[UNDER_2.5, OVER_2.5]`'dir.
- Kullanıcı kaynaklı ilk PDF SHA izi, arşiv kaydında bulunması, **otomatik bağımsız PDF doğrulaması ya da canlı ön-maç mühür kanıtı yerine geçmez**. Bazı kayıtlar sonradan sohbetten aktarılmıştır; bu nedenle 7 maç yalnız **betimsel P0/P1 tutarlılık denemesi** sayılır.
- Geçmiş doğrulanmış maç öncesi piyasa kayıtları + doğru sonuçlar aynı fikstüre as-of kanıtıyla bağlanmadan **Brier/log-loss/kalibrasyon kıyası** veya M4/C3 ve hibrit üstünlük iddiası yapılmaz. `score_observed` yalnız skor mekanizmasıdır, veri doğrulama yerine geçmez.
- Yedi olay üç bağımlı pazarın sonucudur. Skorlama **MS çok-sınıflı + Alt/Üst ikili + KG ikili** pazarlarının makro ortalamasıyla yapılmalıdır; yedi olay bağımsız maç sayılmaz.
- P1'de bir pazar uyum farkı 8 puanı aşarsa `MARKET_FIT_CONFLICT` uyarısı konur. Bu bir güvenilirlik / getiri sertifikası değildir.
- Nihai kararın amaç fonksiyonu: doğrulanmış kalibrasyonu olan 7 olay içinde en yüksek gerçekleşme olasılığı; farklı aileden alternatif. Bahis oranına göre pozitif EV ayrıca değerlendirilebilir, yüksek olasılık **kârlılık garantisi değildir**.

## Çalıştırma

```bash
python -m unittest discover -s experiments/p1_market_intelligence -p 'test_*.py' -v
python experiments/p1_market_intelligence/p1_market.py \
  --archive-dir experiments/263/second_pdf_commentary_archive_263/2026-11-21 \
  --output /tmp/p1_diagnostic.json
```

`/tmp/p1_diagnostic.json` lokal çıktı olarak üretilir; ana makinelerin kayıtlarına, SHA dosyalarına veya GitHub'a yazılmaz. **Bu dizin hiçbir aktif 2.6.3 giriş noktasına bağlanmamıştır.**

## Kabul kapsamı
- **A (tasarım):** Tamam.
- **B (bağımsız kod):** Matematiksel birim testleri yerelde geçti, örneklenen 7 gerçek arşiv oran setinde betimsel P0/P1 hesaplaması yapıldı.
- **C (gerçek maç sonucu doğruluğu):** **Henüz kanıt yok**. Bu dal üretim kararına terfi ettirilmez.