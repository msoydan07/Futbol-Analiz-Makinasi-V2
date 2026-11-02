# 2.6.3 — §12–14 analiz anı oranı ve tam rapor bağlantısı

2 Kasım 2026. Deney dalı: `experiment/263-toplu-karsilastirma`.

## Yapılan
- Mevcut `requested_match_runner_263.py` resmî maç kapısından geçip
  4.413 maçın sabit snapshot'ıyla eski **17 bölümlük** offline analiz kabulünü aldıktan
  sonra yeni `analysis_time_odds_abc_appendix.json` oluşturur ve aynı açıklamayı
  `model_preview.md` içine koyar.
- Ek, kanonik C2 ile 14 MS/çifte şans/KG/gol pazarı olasılığını bağlar.
  B, C3 ve M4 otomatik ana modele terfi ettirilmez.
- Gerçek canlı oran bulup doğrulama yapıldığını **iddia etmez**. Kaynak bulunmadığında
  `DOĞRULANAMADI`, EV yok, resmî A/B/C yok.
- Fikstür eşleşmesi ve zaman denetimi zorunlu; ilk 11 henüz yayımlanmadığında
  matematik durmaz. Rapor eklentisi **ne pilot tahmin kaydı ne betting ledger** oluşturur.
- Güncel veri onaylanmadan eski tam raporun kabul statüsünü 'canlı'ya çevirmeyiz.

## Bilerek yapılmayan
- Kullanıcının esas kuralı: Oran yalnız analiz anında en fazla 10 dakika eski olabilir,
  sonra değişse de önceki raporda değiştirilmez. Doğrulanmış karşı fiyatlar olmadan
  marjsız piyasa/EV ve B sınıfı oluşturulmaz.
- Canlı bahis sitelerinin otomatik kaynak adapter'i yok: gelecekte
  analiz anında kaynağa girilip bağımsız teyit edilmeli.
- Bu ek 2.6.3'ün arşiv sabit 17-bölüm offline kabulünü yeni/staged veri için
  otomatik olarak devralmaz. Yarınki 10 lig güncellemesi ayrıca kabul bekliyor.
- Pilot kayıtları 0/100; `forward_quad_263`, `main` ve eski modeller değişmedi.

## Güncel oran girdisi (2 Kasım)

`requested_match(..., quote_provider=trusted_callable)` dış fiyat adapterinin analiz anında gerçekten gözlediği fiyatı yalnız **bilgilendirme** olarak alabilir. Bu kaynak adapteri bugün otomatik site sorgusu yapmıyor; gösterilen değerlerin bağımsız kaynak teyidi rapor hazırlama sırasında ayrıca yapılmalıdır. Seçim fiyatı tek başına bulunursa görülür; karşı oran yoksa EV/marjsız fark yoktur. Bu frozen tarihsel raporunda A/B/C resmî onayı yok, pilot kaydı yok.
