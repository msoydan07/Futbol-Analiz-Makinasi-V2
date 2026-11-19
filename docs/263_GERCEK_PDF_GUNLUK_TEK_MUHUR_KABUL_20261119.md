# 2.6.3 — Gerçek ilk iddaa PDF'si: 19 Kasım son kabul hazırlığı

**Kontrol tarihi:** 19 Kasım 2026.  
**Dal:** `research/263-13-lig-22-havuz-20261113`.  
**Kısa sonuç:** İlk PDF için güncellik/tek günlük mühür güvenlik bariyeri kodlandı ve CI **SUCCESS**; bugünün kullanıcı PDF'si mevcut olmadığından **gerçek uçtan uca maç günü kabulü YOK**.

## Gerçek kullanıcı dosyası kontrolü

- Library'de bulunan son gerçek iddaa.com kullanıcı bülteni: **11 Kasım 2026** yüklemesi, kaynak metadata: `D:20261111144622+00'00'`.
- Kaynak PDF SHA256: `dda75bed54c6cb3f43b0db4a21331703a5d1351612e8030b172399712b812578`.
- PyMuPDF ile yeniden incelendi: **3 sayfa, 30 fikstür satırı, 28 adet 14-slot fiyat dizisi, 2 adet 13-slot eksik fiyat dizisi**. Eksik iki satırda fiyat konumunun tahminen kaydırılması yasak.
- **10 etkin lig için uygun bugüne ait satır yok**. Bu dosyadan tahmin, sahte PAS, SHA mühür veya güncel iddaa fiyatı üretilmedi; dosya baytları GitHub'a yüklenmedi.
- Bu raporda belirtilen PDF, **bugün için geçerli ilk PDF'nin yerine konulamaz**. Kullanıcıdan bugünün gerçek Chrome yazdır PDF'si gelmeden gerçek uçtan uca kabulü olmuş denemez.

## Bu turda uygulanan ekstra güvenlik

- Yeni `experiments/263/private_4618_first_pdf_day_guard_263.py`:
  - Kaynağı / zaman damgasını doğrular; PDF'nin Türkiye yerel tarihinde bugüne ait olmasını ister.
  - Geçmiş gün/gelecek tarih/saat damgası, kapsam dışı lig, okunamayan fiyat dizisi, uygun bugünkü maç yokluğu veya yinelenen fikstürde fail-closed davranır.
  - Aynı gün **ilk PDF SHA'sına özgü atomik yazılabilen kilit** oluşturur. Başka PDF SHA aynı gün sabah bir daha hesap çalıştıramaz: `SECOND_PDF_CANNOT_CREATE_ANOTHER_MORNING_SEAL`.
  - Aynı ilk PDF'nin **hiç mühür oluşturmamış** başarısız denemesi `private_4618_retry_guard_263.py` ile yeni klasörde güvenle tekrar denenebilir.
- Araştırma girişi `private_4618_iddaa_model_first_one_step_263.py` bu güncellik + günlük SHA kilidini **veri sağlayıcı indirilmeden ve model çalıştırılmadan önce** uygular. Eski `forward_quad.py`, ana M4, 96 pilot ve üretim otomasyonları değiştirilmedi.
- Yeni `test_private_4618_first_pdf_day_guard_263.py`: **14 sentetik güvenlik testi**, geçerli gün, önceki gün, kötü fiyat hizası, yanlış kaynak, yinelenen maç, sahte zaman, ikame PDF SHA, bozuk kilit ve güvenli aynı SHA tekrar kullanımını içerir.
- GitHub Actions [44565761699](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44565761699): **SUCCESS**; Python compile, kontrat testleri, gerçek orijinal matematik modül importları ve eski kod koruma kontrolleri geçmiştir. Bu başarı **private 4.618 CSV ve yeni gerçek iddaa PDF ile tam model koşusu değildir**.

## Değişmeyen sözleşme ve kesin kalan kabul

D-ODDS-001: **ilk PDF sabah bir tek mühür**, ikinci PDF ilk 11/odds farkı için **yorum-only**, tahmin/PAS/mühür değişmez.

D-MARKET-006: **Oran yalnız piyasa beşinci referansı; hiçbir yüzdeyi veya market seçimini belirlemez.** Yeni günlük kilit fiyat kullanarak market seçimi yapmaz, yalnız ilk PDF'nin kimliği/tarihini korur.

**Açık gerçek kabul:** Uygun tarihli ve içinde ilgili lig maçı bulunan *yeni* kullanıcı PDF'si → resmî fikstür doğrulaması → 4.618 özel skor + maç önü as-of kaynak güncelliği → B/C2/C3/M4 → model-only ana/alternatif/PAS ve SHA → piyasa karşılaştırması → okunabilir PDF raporu; ardından gerçek ikinci kullanıcı PDF'siyle **sadece** append-only yorum kontrolü. Ayrıca 4.618'den sonra tamamlanan maç varsa güncel append-only veri sürümü gerekir; eski SHA dondurulmuş kalır.

**Teknik sınır:** PDF fiyat sütunu eksik olan bir satır, mevcut ilk-PDF araştırma hattında analiz için ayrıca durduruluyor; bu bir **kanıt/format güvenlik bloku**, piyasa yüzdeleriyle model seçimi değildir. İstenirse ileride sözleşmeye uygun, fiyatı olmayan maçlarda modeli ayrı çalıştıran kaynak-doğrulamalı rota hazırlanabilir; henüz uygulanmış sayılmaz.

**Durum:** Günlük kimlik/mükerrer mühür güvenliği **BİTTİ ve CI yeşil**; canlı maç önü **BEKLİYOR: yeni tarihli kullanıcı ilk PDF'si**.
