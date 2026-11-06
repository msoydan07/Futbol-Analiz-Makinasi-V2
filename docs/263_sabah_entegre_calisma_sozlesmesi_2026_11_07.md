# Futbol Makinası 2.6.3 — Sabah toplu akış denetimi, 7 Kasım 2026

## Kapsam ve güvenlik
- **Deney dalı:** experiment/263-toplu-karsilastirma. main'e değişiklik yok; B/C2/C3/M4 kodu ve hem M4 hem DEV kalibrasyon kilidi değiştirilmez.
- **İki defter:** legacy96 = 6–8 Kasım'a ait 96 sabit adaydan resmen doğrulanan maçlar (forward_quad_263); new100 = bağımsız SABAH_TOPLU_V1 önceden adlandırılmış istekler (forward_morning_263).
- Eski 96 dosyanın Git blob SHA'sı 803378e8ef0f1f285a3393a7231567eea8f25e80. Adaylar doğrulanmış başlama saatleri anlamına gelmez.
- *Sabah* 05:00–12:59 Türkiye; kullanıcı tetiklemeli, geçmişe dönük değil. Her maç bağımsız canlı resmî fikstür kapısından geçer, sonra aynı eski dört model ve m4_lock kullanılır. Karar basamağı farklı, dondurulmuş forward_dev_calibration_lock_263.json kullanır. Veri onayı eskiyse bloklanır.
- Model kayıtları önceden Git'e commit+push edilmeden hiçbir fiyat API çağrısı yapılmaz. Başlama yaklaşırsa precommit kontrolü başarısız olur, geç tahmin kaydı yapılmaz. İlk 11 gelmemişse tek başına engel değildir.
- Yeni mobil tekli ve toplu ekranlar mühürlü SHA'yı okur; tekrar model hesaplamaz. Rotasyon modülü resmî tüm yarışma takvimi henüz toplamadığı için **VERI_YETERSIZ** gösterir; yüzdeyi değiştirmez.
- **Pinnacle:** varsayılan kapalı. Kullanıcı GitHub workflow girdisinde with_pinnacle=true seçerse, sadece son 10 dakikada ve hâlen KO öncesinde mühürlenen maçların ligleri adaydır. Her lig/TSİ gün için önce experiments/263/pinnacle_daily_reservations/YYYY-MM-DD/LEAGUE_pinnacle_h2h.json kalıcı commit+push edilir; **başarılı push olmadan API yok**. Sonra sadece bir bookmaker=pinnacle, markets=h2h The Odds API çağrısı, fiyat durumu ve güncel kalan kota header değeri experiments/263/pinnacle_daily_snapshots/YYYY-MM-DD/LEAGUE.json'a yazılır. 401/403/429 ve hata sonrası otomatik tekrar YOK. Aynı gün sonraki run cache'i kullanır; yeniden satın almaz. Sabah fiyatı T−60 fiyatı değildir.
- Önceki **T−60 Pinnacle canlı çağrı adımı** no-key durumuna çekildi. Eski tek seferlik Pinnacle probe iş akışı kapatıldı; ikisi de kalıcı günlük kilit dışında kredi harcamaz. S1/S2 resmî onay, bahis veya canlı EV yok.
- Sadece deney dalındaki workflow_dispatch girişinden çalıştırma tasarlandı; kullanıcı arayüzünde görünürlüğü ve gerçek API/olay akışı ayrı kabul gerektirir. Otomasyonların kendiliğinden başlaması veya gerçek 44 maçın analiz edildiği iddia edilmez.

## Çalıştırma girdileri
GitHub Actions: .github/workflows/263-sabah-live-batch.yml
- cohort: legacy96 ya da new100
- day_turkey: bugün YYYY-MM-DD
- request_path: new100 için experiments/263/sabah_requests/AD.json
- with_pinnacle: false (varsayılan güvenli)

Yeni 100-pilot istek dosyası örnek biçimi:
~~~json
{"schema":"SABAH_TOPLU_V1","day_turkey":"2026-11-07","matches":[{"league":"TUR1","home":"Örnek Ev","away":"Örnek Deplasman"}]}
~~~
**Örnek takım isimleri gerçek fikstür doğrulaması veya kullanıcı isteği değildir.**

## Kabul ölçütü
Tek kapsamlı offline akış: iki kohortun ayrımı, yinelenen kayıt, SHA, KO üst sınırı, eksik veri, dört model ekranda aynı SHA, günlük kredi rezervasyonu, aynı gün ikinci çağrının engellenmesi, 7/10 günlük rotasyon raporunun sayısal etkisizliği. Canlı API anahtarı offline CI'ya verilmez. YEŞİL CI, uçtan uca canlı başarı veya gerçek model üstünlüğü kanıtı **değildir**.

## Açık işler
1. Resmî fikstür kaynaklarını otomatik 7/10 günlük tüm kupa ve lig yarışmalarından besleme.
2. Sabit geçmiş 96 maçın sonucu ve yeni 100 maçın sonucu ayrı değerlendirme otomasyonu.
3. Her iki mobil raporun 2.6.2 tam 17 bölüm kapsamıyla karşılıklı denetimi.
4. Bağımsız ücretli/harici otomasyonların olası The Odds API kullanımı burada garanti altına alınamaz.
