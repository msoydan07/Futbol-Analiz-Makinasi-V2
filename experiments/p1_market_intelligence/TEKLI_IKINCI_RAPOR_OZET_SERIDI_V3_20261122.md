# İkinci rapor tasarımı v3 — 7 seçenek özet şeridi

Kullanıcının 22 Kasım 2026 ekran görüntüsünde siyah çizgiyle belirttiği alan için düzen.

## Nihai görsel prototip

Mevcut üç sabit kartın (ANA TERCİH, ALTERNATİF, P0 PİYASA) hemen altında ve MAÇ YORUMU kutusunun hemen üzerinde üç satırlık simetrik özet:

```
Tercihler       MS 1    MS X    MS 2    | Üst    Alt    | Var    Yok
Yüzdeler (P0)   %49,70  %26,28  %24,02  | %50,00 %50,00 | %52,74 %47,26
Oranlar (son)   1,71    3,30    3,72    | 1,73   1,73   | 1,65   1,82
```

- Bu özetin **yedi yüzdesi P0'a aittir**. M4/C3 yedi olasılığı gibi gösterilmez. Ana ve alternatifin kendi model yüzdeleri üstteki kartlarda durur.
- P0 yüzdeleri **ilk iddaa PDF'si** referansından; oranlar **son tarih damgalı kullanıcı gözleminden** alınır. Gözlemdeki oranlar resmî ikinci PDF mührü değildir.
- Seçenek başlıklarının sırası her satırda aynı: MS1/MSX/MS2, 2.5 Üst/Alt, KG Var/Yok. Ortada hafif dikey ayırıcı bulunur, sekiz ayrı kutu oluşturulmaz.
- Ham oranlar yüzdeye çevrilmez, no-vig yüzdeleri tam karşıt pazar olmadan hesaplanmaz. Yayımlanmayan fiyat `—` kalır.
- Ana/alternatif/P0 üst kutularında ilk/son oran/fark olduğu gibi kalır; özet şeridi ile maç yorumunun arasındaki boşluk korunur.
- Tipografi: beyaz zemin, siyah metin, Arial benzeri DejaVu Sans; yalnız alternatif ve fark kırmızı.
- Tek sayfalık PDF örneği konuşmada kullanıcıya sunuldu: `ikinci_rapor_tercihler_yuzdeler_oranlar_v3.pdf`. Repo'ya PDF dosyası yüklenmedi, sadece karar kaydı yapıldı.

**Uygulama sınırı:** V3 görsel prototip ve tasarım kararıdır. Araştırma kodundaki P2 ve ana SHA mühürleri değiştirilmedi; otomatik ana PDF raporlayıcıya henüz entegre edilmedi.
