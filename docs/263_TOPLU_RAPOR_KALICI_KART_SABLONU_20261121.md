# GEÇERLİ KALICI TOPLU RAPOR — 22 Kasım 2026 V3

**Önceki dört-sütun şablon, kullanıcının son onayıyla yürürlükten kalktı.**
D-OPER-006 kapsamında onaylı görsel sunum. Ana hesaplama ve mühürlere dokunulmaz.

## Kanonik işlem
İlk iddaa PDF'si: `experiments/263/iddaa_pdf_one_step_263.py`.
Kullanıcıya dönülecek dosya: `<processing_folder>/toplu_analiz_onayli.pdf`.
Kodun varsayılan üreticisi: `experiments/263/iddaa_pdf_approved_layout_263.py::render_batch`.

## Her maçın tek kartı — üç simetrik sütun

| ANA MAKİNE | P0 | P2: UYUMLU |
|---|---|---|
| KG Var | KG Var | Oran: 1,64 |
| %52,40 | %52,74 | Fark: 0,34 puan |

- ANA MAKİNE: M4/C3'ün **yedi olay içindeki kendi bağımsız lideri** ve kalibre/karar yüzdesi.
- P0: İlk kullanıcı iddaa PDF'sinden üç tam grup içinde komisyonsuzlaştırılmış **kendi bağımsız lideri** ve yüzdesi.
- P2: Yalnız iki lider olay aynıysa aradaki yüzde farkının geçici 5 puan yakınlık eşiğini kontrol eder; **UYUMLU**, **FARKLI**, **YÜZDELER UZAK** veya **ORAN EKSİK** yazar. `Şart 1/Şart 2` kelimeleri raporda yoktur.
- Üçüncü sütunda sıralama: **P2 durumu → P0 liderinin orijinal iddaa oranı → uygun olduğunda yüzde puan farkı**. Farklı olayların yüzdeleri çıkarılmaz.
- Kart altında **Alternatif** (kırmızı). Altı maç A4 sayfa başına; maç/saat/numara üst satır; beyaz zemin, siyah yazı, ince simetrik çerçeve, Arial benzeri Unicode font; yalnız fark ve alternatif kırmızı.
- Piyasa oranı yayımlanmamışsa (MS1/MSX/MS2/2.5/KG) uydurulmaz; yedi piyasa olayının lideri kesin belirlenemiyorsa P0 ve P2 `— / ORAN EKSİK` gösterir.
- Oransız new100 raporunda **aynı kart geometrisi** kullanılır, P0/P2 fiyat bilgisi yoktur. Mühürlü ana karar değişmez.
- Tam teknik tablo `futbol_263_iddaa_oranli_rapor.pdf` ayrı denetim yan dosyasıdır, varsayılan kullanıcı ekranı değildir.
- Önceki tamamlanmış PDF/SHA dosyaları değiştirilemez, yeniden yazılamaz. Yeni girişler yalnız bu V3 sunumu kullanır.

## Kabul sınırı
GitHub Actions: `.github/workflows/263-three-machine-two-reports-v3.yml`.
Testler sentetik/yerel kaynaklarla gerçek render yollarını doğrular; canlı maç isabetini doğrulamaz.
