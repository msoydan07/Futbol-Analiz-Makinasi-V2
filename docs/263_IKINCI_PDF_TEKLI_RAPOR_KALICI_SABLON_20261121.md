# 2.6.3 — İKİNCİ PDF / KALICI ONAYLI TEKLİ MAÇ RAPORU

**Karar tarihi:** 21 Kasım 2026  
**Karar ID:** D-OPER-006, önceki D-OPER-005 raporlama kararını genişleterek yerine geçer (toplu sabah kart şablonu değişmez).  
**Kullanıcı onayı:** Önceki yanlış sunum reddedildi; yeniden hazırlanmış `21_Kasim_2026_Championship_1530_Onayli_Tekli_Mac_Raporu.pdf` ve esas referans `Bundesliga_3_Tekli_Mac_Raporu_Simetrik_v5.pdf` düzeni ikinci PDF için kalıcı tercih edildi.

## Zorunlu tekli sunum

Kullanıcı aynı maçların ikinci iddaa PDF'sini gönderdiğinde **toplu 6 kart düzeni, eski genel inceleme tablosu veya serbest bir özet** gösterme. Birden çok maç varsa tek **çok sayfalı PDF** üret: **her maç bir tam A4 dikey sayfa**, aynı simetrik dört yuvarlatılmış kutu ve aynı hizalar. İstenirse her maçın ayrı PDF'si de yan çıktı olarak üretilebilir. Kanonik kullanıcıya sunulan PDF **`tekli_rapor.pdf`** olmalıdır.

1. **MAÇ BİLGİSİ:** Ev / deplasman adı, lig, tarih ve Türkiye maç saati.
2. **ANA TAHMİN:** `ANA TERCİH | BİZİM % | PİYASA % | FARK` başlıkları hizalı. Sabah mühürlü v4 ana tercih/alternatif/yüzde hiç değişmez; alt satırda **Alternatif** kırmızı. Buradaki `PİYASA %` sabah **ilk PDF** marjsız piyasa oranıdır, `FARK` ilk piyasa ile sabah model yüzdesinin farkıdır.
3. **ORAN KARŞILAŞTIRMASI:** Aynı hizada `MS 1/X/2`, `2.5 ALT/ÜST`, `KG VAR/YOK` için ilk ve son iddaa oranları; sağ sütunda **ANA ORAN** (ilk → son), **ORAN FARKI**, **YENİ FARK** (sabit bizim % eksi ikinci PDF marjsız piyasa %). Son ikisi kırmızı.
4. **YORUM:** Tek, bütünlüklü futbol değerlendirmesi. Kaynaklı kadro / sakatlık / ilk 11 / taktik / rotasyon bilgisi varsa neden olabileceği ihtiyatla değerlendirilir. Doğrulanamıyorsa açıkça belirtilir; ilk 11, neden veya sonuç **uydurulmaz**.

**Görünüm:** A4 beyaz zemin; Arial'e yakın Arimo ya da uygun Unicode sans font, siyah yazı, ince açık gri yuvarlak kutu kenarları, yalnız farklar ve alternatif kırmızı; dengeli ve simetrik. Üste "Bundesliga / TEKLİ MAÇ YAYINI", "model özeti" veya ilave gereksiz bölüm ekleme. Bir maçta piyasa verisi eksikse `VERİ YOK / —`; hiçbir fiyat / model yüzdesi uydurulmaz.

## Uygulama ve güvenlik sözleşmesi
- Kanonik hesap/çizim: `experiments/263/iddaa_pdf_approved_layout_263.py::render_singles(review, target_dir, bundle_pdf=...)`.
- İkinci PDF işlemi: `experiments/263/iddaa_pdf_last_review_263.py::process`.
- Kanonik **kullanıcı raporu:** `last_football_review/tekli_rapor.pdf`, üç maç varsa üç sayfa.
- Yan çıktılar: `last_football_review/tekli/tekli_01.pdf`, vb.
- Eski `review.pdf` teknik denetim artifaktı olarak tutulabilir; **kullanıcıya dönen `pdf_report` alanına atanamaz**.
- **Sadece ikinci kullanıcı iddaa PDF'si**, sabah SHA ve isteğe bağlı **kaynaklı** XI bilgisiyle yorum; oranlar beşinci referans, yeni tahmin/model fit/karar seçimi/mühür yok.
- İç test/regresyon koruması: karar indeksindeki `D-OPER-006` ve kanonik bundle rotası fail-closed guard tarafından doğrulanır. Canlı uçtan uca kabul ayrı C statüsüdür.

**Not:** Bu kural tüm 10 kapsam ligine ve gelecekteki ikinci PDF'lere uygulanır. Kullanıcı açıkça farklı tasarım istemedikçe şablon değişmez.
