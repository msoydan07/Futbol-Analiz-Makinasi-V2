# Tekli ikinci rapor — üç tercihli sade ekran tasarımı v2

Tarih: 22 Kasım 2026 | **Güncel tasarım kararı**. Araştırma prototipidir, ana otomatik PDF üretimine henüz uygulanmadı.

## Kullanıcı düzeltmesi: Piyasa kendi tercihiyle bulunmalı

İkinci maç raporunda **sırayla üç eşit sütun** göster:

| ANA TERCİH | ALTERNATİF | P0 PİYASA |
|---|---|---|
| **KG Var** | **2.5 Üst** | **KG Var** |
| %52,40 | %50,30 | %52,74 |
| İlk oran: 1,64 | İlk oran: 1,73 | İlk oran: 1,64 |
| Son oran: 1,65 | Son oran: 1,73 | Son oran: 1,65 |
| **Fark: +0,01** | **Fark: 0,00** | **Fark: +0,01** |

Altında tek geniş **MAÇ YORUMU**. Yorum, ilk 11, sakatlıklar, doğrulanmış güncel takım bilgileri, güç farkı ve fiyat değişimleri üzerine tek parça açıklama yapar; doğrulanmamış fiyat değişimi nedenini uydurmaz.

### Kesin tasarım ve matematik kuralları

- Ana tercih ve alternatif, sabah mühürlü M4/C3 kararına ve yüzdelerine aittir; ikinci oranlardan **değiştirilemez**.
- P0 kutusunda **ana tercihin P0 yüzdesi değil**, P0'ın **sabahki ilk PDF'deki yedi pazar seçeneğinden bağımsız belirlediği kendi en yüksek tercihi ve kendi yüzdesi** bulunur. İkinci PDF sadece bu sabah seçiminin son iddaa oranını sağlar. P0'ın sabah kararı son oranlardan yeniden üretilmez.
- Her sütunda **ilk oran, son oran, fark = son - ilk**. Oran farkı yüzde farkı değil, ham ondalık iddaa oran farkıdır.
- İki veya üç sütun aynı tercih kodunu gösterebilir; bu durumda oran satırlarının tekrar etmesi doğaldır ve yeni bağımsız bilgi gibi yorumlanmaz.
- Tam yedi seçenekli iddaa oran tablosu, P2'nin koşul/uyum kutusu ve model özeti ikinci raporda **yer almaz**. P2 karşılaştırması birinci toplu raporda kalır.
- Eksik veya yayımlanmamış fiyat varsa ilgili hücre `—` olur; asla sayı türetilmez. P0 tam yedi olasılık arasındaki en yüksek seçimi doğrulanamıyorsa piyasa tercihi de **Belirlenemiyor** şeklinde gösterilir.
- Beyaz arka plan, siyah yazılar, Arial benzeri font, simetrik üç sütun, yalnız **alternatif** ve **fark** kırmızı. Telefon ekranında okunabilir, tek sayfalık düzen.

## Görsel prototip ve kaynak sınırı

Görsel: `ikinci_rapor_ana_alternatif_piyasa_v2.pdf` (bu sohbetin çalışma dosyası). Kasımpaşa–Alanyaspor örneğinde sabah araştırma kararı ve geçmiş iddaa görüntüsündeki ilk/son oranlar kullanıldı; **resmî ikinci PDF kaydı değildir**.

Bu belgede tasarım kararı güncellenmiştir; repo içindeki canlı 2.6.3 PDF üretim koduna, önceden mühürlenmiş tercihlere veya üretim otomasyonuna müdahale edilmedi.
