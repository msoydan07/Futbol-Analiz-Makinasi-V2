> **GEÇMİŞ / YÜRÜRLÜKTEN KALKMIŞ TASARIM (20 Kasım).** Kullanıcının 22 Kasım 2026'da onayladığı V3 artık kalıcıdır. Güncel kaynak: `docs/263_TOPLU_RAPOR_KALICI_KART_SABLONU_20261121.md` ve `docs/263_IKINCI_PDF_TEKLI_RAPOR_KALICI_SABLON_20261121.md`; mevcut aktif karar: `docs/263_AKTIF_KARARLAR.json` D-OPER-006. Aşağıdaki tarihsel dört-sütun/dört-kutu talimatları gelecekteki PDF üretiminde kullanılmaz.

# 2.6.3 — Kullanıcının onayladığı günlük PDF rapor ekranları

**20 Kasım 2026 kesin görünüm ve normal işleyiş.** Bu bir yeni model,
yeni karar veya ayrı bir matematik katmanı değildir. Yalnız mevcut
SHA-korumalı kararların kullanıcıya sunum biçimidir.

## 1. Sabah / öğlen: lig bazlı toplu PDF

- Kullanıcı iddaa.com aynı lig maçlarını PDF olarak, mümkünse tablo
  yakın çekim görseliyle yollar. **Sayısal oran kaynağı PDF'dir**; görsel
  yalnız okunurluk ve çapraz kontrol içindir.
- Normal giriş: `experiments/263/iddaa_pdf_one_step_263.py`.
- Çıktının **kullanıcıya varsayılan gösterilecek yolu**:
  `<processing_folder>/toplu_analiz_onayli.pdf`.
- A4 beyaz zemin, Arial'e yakın Arimo, siyah yazı; sadece **fark** ve
  **alternatif** kırmızı. Bir sayfada 6 maç; birden çok lig/tarih ayrı
  sayfada, 7. maç ek sayfada.
- Kart: **maç + TSİ saat**, **Ana Tercih | Bizim % | Piyasa % |
  Fark (yüzde puan)**, en altta **Alternatif** ve **ana iddaa oranı**.
- `Bizim %`: imzalı model-first kararının aynı pazar için kullandığı
  uzman model olasılığı; geçmiş gerçekleşme düzeltmesiyle karıştırılmamalı.
- `Piyasa %`: yalnız aynı iddaa PDF'sindeki **tam pazar grubunun**
  komisyonsuz/no-vig oranından; eksik tarafta `—`.
- Seçim oranlara göre yeniden yapılmaz. Teknik blok varsa yüzde/tercih
  uydurulmaz; `TEKNİK ENGEL`, gerçek model PAS ise `MODEL PAS` yazılır.
- Eski ayrıntılı teknik PDF mevcut dosyada kalır ve receipt/SHA ile
  saklanır. Onaylı rapor da ayrı SHA ile denetlenir.

## 2. Maç saatine yakın: kullanıcı seçtiği maç için ikinci PDF

- Kullanıcı resmî ilk 11'ler açıklandıktan sonra ikinci iddaa PDF'sini
  gönderir; kullanıcı özellikle hangi maçı görmek istediğini bildirir.
- Normal giriş: `experiments/263/iddaa_pdf_last_review_263.py`,
  aynı sabah tamamlanan oturumun altına inceleme olarak ekler.
- Çıktı: `<processing_folder>/last_football_review/tekli/tekli_XX.pdf`;
  `approved_match_index` takım adlarını + başlangıç saatini + tam
  dosya yolunu eşler, böylece istenen 1-2 maçın PDF'si doğrudan gösterilir.
- Yalnız **eşleşmiş, maç başlamadan alınmış ikinci iddaa oranı**
  bulunan maç için tekli PDF üretilebilir.
- A4 tek sayfa, tam simetrik sağ/sol kenarlı **dört kutu**:
  1. **Maç Bilgisi:** iki takım, lig, tarih, TSİ saati;
  2. **Ana Tahmin:** ana tercih, sabahki Bizim %, sabahki Piyasa %,
     sabahki fark; alternatif hemen altında;
  3. **Oran Karşılaştırması:** aynı satırda ilk ve son oranlar,
     sağda **Ana Oran (ilk → son), Oran Farkı ve Yeni Fark**;
  4. **Yorum:** bölünmeden tek doğal Türkçe paragraf; oran artışı/düşüşü,
     kaynaklı ilk 11/gelişmeler ve ilişkinin yalnız olası olduğu açıkça
     belirtilir. Kaynak yoksa uydurma yorum veya kesinlik iddiası yok.
- İkinci PDF **tahmin, model yüzdesi, alternatif, sabah mührü veya
  olasılıkları değiştirmez**; oranlar yalnız yan yana kıyaslanır.
- Kaynaklı ilk 11 gözlemleri, kodun internetten bağımsız doğrulaması
  yapılmış gibi gösterilmez. Oran hareketinin kesin sebebi iddia edilmez.
- **Model Özeti yok.** Tüm kutular aynı sol/sağ hizada.

## 3. Kesin dosyalar ve bakım

- Sunum kaynağı:
  `experiments/263/iddaa_pdf_approved_layout_263.py`
- İlk PDF bağlantısı:
  `experiments/263/iddaa_pdf_one_step_263.py`
- İkinci PDF bağlantısı:
  `experiments/263/iddaa_pdf_last_review_263.py`
- Test:
  `experiments/263/test_iddaa_pdf_approved_layout_263.py`
- GitHub CI:
  `.github/workflows/263-approved-user-report-layout.yml`

**Sınırlamalar:** Tasarım onayı model doğruluğuna kanıt değildir.
İlk 11 kaynaklı veri kullanıcıdan veya güvenilir açık kanıttan gelmedikçe
rastgele futbol faktörü anlatılmaz. Kullanıcıdan gelen ekran görüntüsünden
oranı PDF yerine sessizce değiştirmez. Eski SHA kayıtları güncellenmez.
