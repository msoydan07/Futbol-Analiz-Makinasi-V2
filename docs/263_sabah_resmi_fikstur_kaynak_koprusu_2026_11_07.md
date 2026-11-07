# 2.6.3 — Resmî kaynak okuyucu: 7 Kasım 2026 uygulama notu

Yeni sabah_official_fixture_gateway_263.py yalnız resmî alan adı onaylı lig sayfalarını okur, aynı ligde 10 dakika içinde sayfayı tekrar istemez ve isimleri dondurulmuş 215-kulüp kimlik haritasındaki eşsiz kulüp ID'siyle eşleştirir.

- Sabah toplu analiz işleyicisi her maç öncesi canonical analyze_named_match_gate çağırır. İlk yol, güncel resmî sayfadaki açık saatli eşleşmedir. Sayfa veri vermiyorsa var olan canlı lig/federasyon adaptörü devreye girer. İki yoldan biri doğrulanmazsa tahmin engellenir.
- Premier League yıllık programındaki geçici saatler maç günü saati olarak onaylanmaz. Tarih var, saat yoksa tarih-bilgi statüsü çıkar, tahmin başlamaz.
- Kaynak URL, SHA-256 içerik özeti ve kaynak okuma yönteminin adı rapora eklenir; kaynak HTML'si arşive kopyalanmaz.
- Aynı resmî lig sayfasındaki açık kickoff ve eşsiz kimlikli diğer maçlar, geçmiş 7 / gelecek 10 gün rotasyon niteliksel raporuna girebilir. UEFA/yerel kupaların tam kapsandığı iddia edilmez; model lambda/yüzdeleri değiştirilmez.
- Sabah resmî kaynak tanı kodu bugünkü önceden sabit 96 adayın yalnız canlı resmî sayfa okunabilirliğini araştırır; tahmin ve Pinnacle sorgusu yapmaz. Sayfada bulmak ile resmî maç kapısında mühürlenmiş ileri tahmin oluşturmak farklıdır.
- 10 lig için gerçek günkü kaynak/parsing sonucu ve blok nedenleri görülmeden tam kapsama iddia edilmez.
- main, B/C2/C3/M4, iki kalibrasyon kilidi ve 96 aday dosyası değiştirilmez.

Açık sınırlama: resmî sayfaların hepsinde tüm maçlar/tam saatler bulunmayabilir; bazı kaynaklar JavaScript gerektirir. Gerçek uçtan uca ileri kayıt için hâlen kickoff öncesi Git commit ve veri kabulü gerekir.
