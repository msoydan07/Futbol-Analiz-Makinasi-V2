# 2.6.3 — Sabah SHA -> güvenilir maç sonu değerlendirmesi: teknik bağlantı

9 Kasım 2026 • deney dalı • `main`, M4 ve LITE değiştirilmedi.

## Kalıcı gerçeklik ve veri sınıfı
- Sabah fixtür kapısı ve B/C2/C3/M4 sonuçları geçmişte 8 Kasım'da 40 kayıt için çalıştı ve Git SHA ile kalıcı saklandı. Bu kayıtların içerikleri değiştirilmedi.
- Maç sonu `sabah_postmatch_new100_263.py` **yalnızca gerçek insan teyitli resmi sonuç JSON'larını** değerlendirir ve kaynak kabul dosyası olmadan 0 resmî sonuç gösterebilir. Bu kural **korunuyor**.
- Yeni `postmatch_csv_bridge_263.py`: 2026/27 sezonu için 10 ligin **ücretsiz** football-data.co.uk CSV'lerini salt okunur indirir; maç tarihini, takım kimliğini sadece daha önce doğrulanmış ad eşlemelerini kullanarak ve SHA ile eşler. Tam zaman sonucu yoksa, iki maç çakışırsa, skor-FTR çelişirse veya canlı kaynak ulaşılamazsa kaydı **bekletir**.
- 8 Kasım'ın önceden webden araştırılmış maç sonuçları ile harici CSV skoru aynıysa ikinci araştırma kanıt sınıfı `TWO_SOURCE_RESEARCH_CONCORDANT_NOT_OFFICIAL` olur. Aksi halde `WEB_REVIEW_CONFLICT`, skorlanmaz. Sadece CSV ile bulunan kayıt `CSV_ONLY_PROVISIONAL` statüsündedir.
- Dış CSV, federasyonun resmî sonucu değildir. Bu katman **0 bağımsız federasyon doğrulaması**, **0 insan teyidi** üretir. Resmî statü için mevcut ayrı resmî sonuç kaydı ve yetkili inceleme gereklidir.
- Model ve bahis pazarları aynı kalır. Oran API çağrısı ve Pinnacle kredisi **0**. Yanlış skor eğitim verisine girmez.

## Çalışma zinciri
1. Önceden mühürlü `forward_morning_263/YYYY-MM-DD/*.json` kayıtları (B/C2/C3/M4) ve kaydedilmiş sabah batch kimliği okunur.
2. Kaynak CSV'de açık `FTHG/FTAG/FTR` görülür, kimlik + tarih eşleşir, maç bitişinden en az 90 dakika geçmiş olur.
3. Yalnızca eşleşen tahminlerin MS, KG, 1.5/2.5/3.5 Alt-Üst Brier/log-loss ve isabeti **geçici araştırma** olarak hesaplanır.
4. GitHub `263-postmatch-csv-bridge-readonly.yml` yeni mühür veya dosya güncellemesinde otomatik devreye girer. Çıktı GitHub Actions artefaktıdır; hiçbir tahmin/sonuç/kalibrasyon dosyası overwrite yapılmaz.
5. İnsan tarafından resmî sayfada skor kontrol edilerek ayrı `sabah_postmatch_inputs` içine düzgün kanıt yazılırsa **mevcut** `263-sabah-new100-postmatch-readonly.yml` otomatik hesaplar. Resmî kanıt dosyası olmadan resmî pilot başarı sayısı arttırılmaz.

## Planlı operasyon için açık gerçek sınır
GitHub `schedule` olayı varsayılan dalda çalışır. Bu yeni kod deney dalında, `main`e dokunulmadı. Dolayısıyla yalnız yeni mühür push'u veya ilgili kod değişikliğiyle yapılan kontrol, **her ertesi gün kendiliğinden zamanlanmış** sayılmaz. Sabah veya sonuç otomasyonunda zamanlanan ikinci kontrol ayrıca bağlanmalıdır; bu belge veya yeşil test kendi başına zamanlayıcı değildir. Açık teknik iş bu otomatik tekrar çağrısının güvenli biçimde eklenmesidir.

**Kabul:** Proje kesintisiz yeni pilot beklemez; mevcut kilitli M4 ile analiz yapar. Sonuç sınıfları ayrılır, hatalı kanıtla model seçimi yapılmaz.
