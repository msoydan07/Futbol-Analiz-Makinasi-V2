# Tekli ikinci rapor — sade ekran tasarımı

Tarih: 22 Kasım 2026 | Tasarım prototipi, üretim entegrasyonu değil.

## Onay için kullanıcı düzeni

Maç başlığı: takımlar + maç saati. Altında iki **eşit ve simetrik kutu**.

| ANA TERCİH | ALTERNATİF |
|---|---|
| KG Var · %52,40 | 2.5 Üst · %50,30 |
| İlk oran: 1,64 | İlk oran: 1,73 |
| Son oran: 1,65 | Son oran: 1,73 |
| Fark: +0,01 | Fark: 0,00 |

Altında **tek geniş MAÇ YORUMU bölümü** (ilk 11, sakatlıklar, forma giren oyuncular, rakip gücü, futbol içi olası nedenler ve fiyat değişiminin doğrulanabilir yorumu). Yorum futbol verilerinden dayanak olmadan neden uydurmaz.

**Bu ikinci ekranın dışında bırakılacaklar:** tam yedi fiyatlı iddaa oran tablosu, P0 yüzdeleri, P2 uyum sütunları, model özet kutusu, teknik kontrol maddeleri.

Görsel tercihler: beyaz zemin, siyah metin, kırmızı alternatif ve fark, geniş aralıklar, simetri, Arial benzeri yazı tipi; mobil ekranda rahat okunsun.

**Değişmez kural:** Sabah ilk PDF'den mühürlenen ana ve alternatif tercih/yüzdeler değişmez. Son oran ikinci PDF / sonraki gözleme ait zaman damgalı ayrı veri olarak saklanır. Fark = son ham iddaa oranı - ilk ham iddaa oranı; eksik ham fiyatları uydurulmaz. Model yüzdesi ile iddaa oranı birbirine karıştırılmaz.

## Örnek ekranın veri sınırlaması

Kasımpaşa–Alanyaspor örneğinde ilk iddaa PDF'si ve kullanıcının sonraki ekran görüntüsünde görülen KG Var 1,64 -> 1,65, 2.5 Üst 1,73 -> 1,73 kullanılmıştır. Bu ikincil görüntü **resmî ikinci PDF mührü** değildir. Yorum yalnız örnek ve gözlenen sınırlı değişimdir.

Örnek tek sayfalık PDF: `uc_makine_ikinci_rapor_tasarimi_v1.pdf` (konuşma çıktısı; GitHub'a yüklenmedi). Bu belge yalnız tasarım sözleşmesidir. Mevcut otomatik PDF üreticisi henüz bu tasarımla değiştirilmemiştir.
