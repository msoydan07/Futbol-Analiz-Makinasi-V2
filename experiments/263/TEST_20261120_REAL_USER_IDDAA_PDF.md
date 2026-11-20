# 2026-11-20 — İlk GERÇEK kullanıcı iddaa PDF'siyle 2.6.3 üretim kabul denemesi

**Amaç:** İki aşamalı maç günü için ilk kullanıcı PDF'sinin hatasız alınıp model üretimine geçip geçmediğini ölçmek. Bu bir veri toplama / kaynak kabulü ve saha hata tespitidir; geçmiş pilotun yeniden yapılması değildir.

**Kaynak:** kullanıcının 20 Kasım sabahında verdiği `20.11.pdf`; PDF **yalnız yerel özel alanda** işlendi, GitHub'a veya dış bahis sitelerine yüklenmedi. Kaynak SHA256:
`ab3d08978f964d8b2f211de0db2738b1f3629512a0674e81c8a4070942997ca0`.
Gerçek PDF metadata zamanı `2026-11-20T07:18:46+00:00` = `10:18:46 Europe/Istanbul`.
29 sayfada veri bölümü sayfa 1-2, kalanların çoğu boş baskı alanı / iddaa footer.

**Düzeltilen kullanıcı formatı sorunu:** İlk beş 'Öne Çıkanlar' maçı normal `20:00\\nEv - Deplasman` bloğu değil; zaman `Bugün\\nHH:MM`, takımlar `Ev\\nDeplasman` olmak üzere **ayrı dikey bloklar**. Orijinal eski ayrıştırıcı bu satırları okuyamıyordu. Yeni ayrıştırıcı koordinat uyumlu üç blok + 14 sabit fiyat slotunu şart koşar; kaymış fiyatı tahmin etmez, normal satırları bozmaz.

**Gerçek kullanıcının değiştirilmemiş PDF'siyle tekrarlanan okumada:** 24 okunur normal + öne çıkan fikstür satırı, yalnız **2 kapsam ligi maçına eşleşen**:
- `FRA1`, 20 Kasım 22:45 TRT: **Troyes — Le Havre**, MS `2.00/3.12/2.96`, Alt/Üst 2.5 `1.73/1.73`, KG Var/Yok `1.58/1.90`; tüm fiyatlar tek kaynak PDF'den.
- `ESP1`, 20 Kasım 23:00 TRT: **Athletic Bilbao — Espanyol**, MS `1.34/4.11/5.99`, Alt/Üst 2.5 `1.82/1.65`, KG Var/Yok `1.82/1.65`.
- Türkiye **1. Lig** (Süper Lig değil), Almanya **2. Bundesliga** (1. Bundesliga değil) ve diğer kapsam dışı maçlar dahil edilmedi.
- İspanyol PDF adları `Athletic Bilbao` → zaten kayıtlı `Athletic Club`, `Espanyol` → zaten kayıtlı `RCD Espanyol de Barcelona` için yalnız ad varyantları eklendi; yeni takım UUID'si veya fuzzy tahmin yok.

**Resmî maç doğrulaması:** İlk gün yerel denemesinde önceden bağımsız **web üzerinden doğrulanmış** kaynaklar, `iddaa_pdf_session.one_step(official_lookup=...)` callback'ine test girdisi verildi. Bu bağlamda **otomatik resmi adaptörün başarılı çalıştığı iddia edilmez**. Kaynaklar:
- Ligue 1 organizatörü `https://ligue1.com/fr/articles/l1_article_5839-`, Troyes–Havre 2026-11-20 20:45 CET = 22:45 TRT.
- LaLiga `https://www.laliga.com/en-ES/clubs/athletic-club/next-matches`, Athletic–Espanyol 2026-11-20 21:00 CET = 23:00 TRT.

**Gerçek kritik engel:** Yalnız erişilebilir eski, SHA `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`, **4.413 maç** kabul edilmiş tarihsel CSV ile yapılan ilk PDF denemesinde:
- FRA1 geçmiş son tarih `2026-10-26`; 20 Kasım için **25 gün eski**.
- ESP1 geçmiş son tarih `2026-10-26`; **25 gün eski**.
- Sıkı 10 günlük kaynak tazeliği ve `freshness_gap_guard_263.py` bunu `StaleLeagueData: GAP_EXCEEDS_LIMIT_REQUIRES_REFRESH` olarak bloke etti.
- **2 doğrulanan fikstür, 0 imzalı M4/C3 forecast, 0 model-first seçim, 0 yeni SHA maç önü tahmin mühürü.** Kesinlikle bahis PAS'ı veya model performansı kararı değildir. Daha yeni kabul edilmiş bir veri kopyası bu yerel test için sağlanmamıştı; bütün uzaktaki olası güncel kaynakların bulunmadığı iddia edilmez.

**Önemli rapor düzeltmesi:** Eski rapor kodu model hiç çalışmamışken yanıtı yanlışlıkla `ANA: PAS` yazabiliyordu. Bunu `ANA: TEKNIK ENGEL (PAS DEGIL)` yaptık; eksik veri = modelin bilinçli PAS'ı değildir. Bu ayrım regresyonla korunuyor.

**Sonuç / hazır olma:**
- A: gerçek PDF özgün SHA, sütun/kapsam/isim çözümlemesi **başarılı**.
- B: dış resmî sayfa **manuel web teyidi** başarılı; GitHub'un otomatik resmî adaptörü bu yerel ilk testte **kanıtlanmadı**.
- C: tarihsel veri tazeliği **engelli**; M4/C3 üretilmemiş, model-first tercihi yok.
- D: ikinci İddaa PDF / XI sahada henüz sınanmadı.
- GitHub testleri, synthetic highlighted satırlar ve önceki PDF model-first/ikinci PDF regresyonu yeşil, **canlı kabul testi başarılı denemez**.
- Ana M4/C3 denklemi, xG politikası, 96/40 eski mühürlü arşiv, eski SHA kayıtları **değişmedi**; yeni xG girişi yok.
- Sıradaki tek somut engel: **gerçek güncel, kaynağı kabul edilmiş FRA1/ESP1 maç sonucu veri kesitini** çalıştırılabilir ilk-PDF makinesine vermek; mevcut 4.413 ham eski kesitiyle yüzde üretmek yok.

Bu kayıt eski D-ODDS-001/D-MARKET-006/D-C3-CAL-010 kararlarını değiştirmez.
