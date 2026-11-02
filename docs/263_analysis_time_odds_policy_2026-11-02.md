# 2.6.3 — Analiz anı oranı kuralı (2 Kasım 2026)

## Kullanıcı kararı (esas)
- Maçın başlamasına yaklaşık bir saat kala kullanıcı **analiz et** dediğinde o anda güncel gerçek pazar oranlarını kontrol et.
- **Analiz sırasında tespit edilip doğrulanan oran tek referanstır.** Daha önce 1,50 olup 1,40'a düşmesi veya analizden sonra değişmesi geçmiş analizi değiştirmez.
- Raporda seçimin oranı, kaynak/site, kaynak URL'si, **kontrol zamanı (TSİ)** ve analiz zamanı gösterilir; rapordaki tahmin yüzdeleri bu oran nedeniyle yeniden hesaplanmaz.
- İlk 11 resmi olarak açıklanmışsa kullan; açıklanmamışsa bu **analizin engeli değildir**, yalnız doğrulanamayan kadro etkisini belirt.
- Canlı oran kaynağı yoksa **DOĞRULANAMADI** yaz; tahmini oran uydurma.
- Gerçek oran kontrolünü kod bir başlık/boolean bayrakla kendi kendine ispatlayamaz; kaynak harici teyit edilmelidir.

## Uygulanan teknik kural
- Yalnız maç başlamadan ve **analiz zamanından en fazla 10 dakika önce** doğrulanmış fiyat kabul edilir. Bu teknik tazelik üst sınırıdır, bir 'sabah sabit oran' ya da 'kapanış oranı' değil.
- Doğrulanmış tek seçim fiyatı gösterilir; fakat tam karşılıklı fiyat yoksa marjsız piyasa, EV onayı ve B sınıfı hesaplanmaz.
- MS 1/X/2 için aynı siteden aynı zamanlı üç karşı fiyat, KG ve gol alt/üst çizgileri için aynı siteden iki karşı fiyat gerekir. Çifte şansın 1X/X2/12 oranlarını normal 1X2 gibi normalize etmek yanlıştır; tek seçim oranı gösterilir ama marjsız üstünlük/B doğmaz.
- Oran olmadan A olasılık adayı olabilir; A/B/C aday statüsü ile resmî güven sınıfı ayrı kalır. Bağımsız model güvenilirliği kanıtlanmadıysa `official_class=None`.
- Analiz anındaki fiyatın daha sonra değişmesi **analiz çıktısını otomatik güncellemez**. Sonradan tekrar analiz istenirse o farklı bir analiz anıdır; geçmiş fiyatı ona taşınmaz.
- **Bu değişiklik yalnız A/B/C ve oran açıklama modülüdür**; forward/pilot kayıtları, `main`, matematik motorları ve yarınki Salı güncellemesi değiştirilmez.

## Rapor alanları
`analysis_time_utc`, `price.checked_at_utc`, `price.source`,
`price.source_url`, `price.decimal_odds`, `price.break_even`,
`price.no_vig` (yalnız tam karşı fiyat), `EV` (yalnız tam karşı fiyat) ve
`price_policy`. Pilot kaydı oluşturulmaz.
