# Manuel piyasa fiyatı talebi — kullanıcı / doğrulayıcı kılavuzu

**Bu klasöre örnek JSON KOYMAYIN**: yalnız gerçek kaynak sayfasından, maçtan önce kontrol edilmiş yeni istekler eklenmelidir. Yanlışlıkla atılan örnek istek CI'yi boşuna çalıştırır. Bu README yalnız şemayı anlatır.

Ön koşul: `forward_quad_263/YYYY-MM-DD/<24hex>.json` içinde gerçekten **maçtan önce commit edilmiş**, doğru fikstür için dörtlü B/C2/C3/M4 tahmini olmalı. Şu anda bu dalda henüz böyle bir gerçek kayıt yok. Bu nedenle gerçek oran talebi eklemeyin, önce pilotun güncel veri ve resmî fikstür kapısını tamamlayın.

Yeni istek dosyası yalnız `experiments/263/market_quote_requests/YYYYMMDD_istek01.json` şeklinde *yeni* commit olarak eklenir. İstek formatı:

```json
{
  "schema": "263_manual_market_quote_request_v1",
  "forecast_path": "forward_quad_263/2026-11-06/0123456789abcdef01234567.json",
  "source_url": "https://www.nesine.com/gercek-ilgili-mac-sayfasi",
  "source_domain": "nesine.com",
  "reviewer": "Gercek_kaynak_kontrolunu_yapan_kisi",
  "reviewed_at_utc": "2026-11-06T16:00:00+00:00",
  "observed_at_utc": "2026-11-06T16:01:00+00:00",
  "visible_source_note": "Sitede görünen ilgili maç adı, lig, MS 1/X/2 ve kontrol edilen bahis çizgileri",
  "market_prices": {
    "MS": {"MS1": 1.76, "MSX": 3.82, "MS2": 2.78},
    "KG": {"BTTS_YES": 1.85, "BTTS_NO": 1.90},
    "GOALS_2.5": {"UNDER_2.5": 1.80, "OVER_2.5": 1.92}
  }
}
```

**Bu örnek rastgele/temsili sayılardır, canlı fiyatlar değildir; kopyalayıp göndermeyin.**

Kurallar: `observed_at_utc` gerçek okunma anı UTC, en fazla 10 dakika önce; kaynak insan tarafından gerçekten gözlenmiş ve saha/maç kimliği kontrol edilmiş olmalı. Her bir pazarın **tüm karşı seçimleri** aynı sitenin aynı anındaki fiyatları olmalı. Fiyat bulunmayan pazarı kaldırın; kalanlar en az bir tam pazar içermeli. Farklı bookmaker oranlarını birleştirmeyin. `iddaa.com > nesine.com > bilyoner.com > mackolik.com` kaynağa erişim önceliği sürer; daha iyi görünür EV için sonradan sağlayıcı seçmeyin.

İşlem başarırsa dosya `experiments/263/market_quotes_locked/YYYY-MM-DD/<24hex>.json` altına bot tarafından *yeni* SHA'lı kayıt olarak commit edilir; başarısız denemeler ayrı rapora yazılır. Her durumda GitHub bot push zamanının gerçek KO'dan **önce** olduğu ayrıca kontrol edilmelidir; bu araç tek başına bağımsız canlı kaynak kanıtı sunmaz. Salt-okunur piyasa karşılaştırması için uygun bir girdi oluşturur. S1/S2 bahis onayı veya gerçek para emri vermez.

**Mevcut pilot engeli:** `data/quad_accepted_263/extended_history.csv` ve `source_acceptance.json` henüz mevcut değil. Sırf oran toplamak için bu kalite kuralını atlamayın.
