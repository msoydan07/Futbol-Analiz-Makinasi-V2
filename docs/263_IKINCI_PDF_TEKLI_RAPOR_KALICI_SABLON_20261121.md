# GEÇERLİ KALICI İKİNCİ PDF TEKLİ RAPOR — 22 Kasım 2026 V3

**Önceki dört geniş kutulu ekran, kullanıcının açık onayıyla bu tasarımla değiştirildi.**
Karar D-OPER-006 sunum ekidir; eski futbol kararları ve SHA'lar korunur.

## Kanonik işlem
İkinci orijinal kullanıcı PDF'si: `experiments/263/iddaa_pdf_last_review_263.py::process`.
Varsayılan kullanıcı dosyası: `<processing_folder>/last_football_review/tekli_rapor.pdf`.
Ayrı maç yan çıktıları: `last_football_review/tekli/tekli_XX.pdf`.
Tek renderer: `experiments/263/iddaa_pdf_approved_layout_263.py::render_singles`.

## Tek maç, tek A4 sayfa

Başlık: **Ev - Deplasman, gün ve TSİ maç saati**.

Üstte **üç aynı boyda kutu**:

| ANA TERCİH | ALTERNATİF | P0 PİYASA |
|---|---|---|
| KG Var %52,40 | 2.5 Üst %50,30 | KG Var %52,74 |
| İlk oran: 1,64 | İlk oran: 1,73 | İlk oran: 1,64 |
| Son oran: 1,65 | Son oran: 1,73 | Son oran: 1,65 |
| Fark: +0,01 | Fark: 0,00 | Fark: +0,01 |

Ardından tek hizalı **üç satırlık özet şeridi**:
- **Tercihler:** MS 1 | MS X | MS 2 | Üst | Alt | Var | Yok
- **Yüzdeler:** ilk PDF'den P0'ın yedi marjsız yüzdesi (var olan tam gruplar).
- **Oranlar:** ikinci kullanıcı PDF'sinin yedi son **ham iddaa oranı**.

En altta tek büyük **MAÇ YORUMU** kutusu. Yalnız kaynaklı ilk 11/sakatlık/kadro veya ölçülen fiyat değişimi konuşulur; doğrulanmayan nedeni veya lineup olayı uydurulmaz.

### Değişmez mühür kuralları
- Ana tercih, alternatif, her ikisinin sabah yüzdesi ve **P0'ın kendi sabah en yüksek tercihi** ilk PDF'nin imzalı kaynak zincirinden gelir.
- İkinci PDF, seçim veya model yüzdelerini değiştiremez; sadece son ham oranları ve futbol yorumunu değiştirir.
- Üç kutunun her birinde `Fark = son oran − ilk oran` ham ondalık oran farkıdır, P2 yüzde puanı farkı değildir.
- İkinci ekranda **P2 denetim kutusu, teknik şart metni, yedi fiyatlı geniş bahis tablosu ve model özet bloğu** gösterilmez.
- Eksik iddaa fiyatı veya yedi olay P0 lideri için kanıt yoksa `—/BELİRLENEMİYOR`; sayı uydurulmaz.
- Beyaz zemin, siyah ana metin, kırmızı alternatif ve farklar, ince simetrik çizgiler, Arial benzeri Unicode font.
- Mevcut `review.pdf` teknik denetim artifaktıdır ve kullanıcıya kanonik `pdf_report` olarak ASLA sunulmaz.
- Önceki SHA'lı raporlar tekrar üretilmez, yeniden mühürlenmez; bu görsel sürüm yalnız bundan sonraki yeni PDF oturumlarında geçerlidir.

## Kabul
`.github/workflows/263-three-machine-two-reports-v3.yml` ile iki gerçek render çağrısı, veri bütünlüğü ve çoklu maç bundle sınanır. Canlı maç doğruluk kanıtı değildir.
