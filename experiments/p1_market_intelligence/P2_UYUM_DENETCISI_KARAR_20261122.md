# P2 — Üçüncü Makine (P0 ile M4/C3 uyum denetçisi)

Tarih: 22 Kasım 2026. Dal: experiment/p1-market-intelligence-20261121.

## Sözleşme: yeni tahmin yok

- Ana 2.6.3: MS 1/X/2 için M4; KG Var/Yok ve 2.5 Alt/Üst için C3. Mevcut model-first v4 kararından yedi olayın en yüksek gerçekleşme olasılıklı ana tercihi. Önceden mühürlenmiş karar, SHA ve alternatif korunur.
- P0: Kullanıcının **ilk** iddaa.com PDF'sindeki MS, 2.5 ve KG oranlarını üç **ayrı** pazar içinde marjdan arındırır. Yedi olay yüzdesini gösterir; yedi olay birbirini dışlayan tek dağılım değildir.
- P1: Aynı oranlara bağımsız Poisson uyduran **piyasa yeniden ifadesi**. Bağımsız futbol verisi içermez; araştırma için saklanır.
- P2: Sadece ana makinenin SHA'lı main_candidate.market ve calibrated_probability alanlarını P0'daki **aynı olayın** marjdan arınmış yüzdesiyle karşılaştırır. Ayrıca P0'ın zirvedeki seçimi de aynı mı diye işaretler. Yeni hibrit yüzde ve yeni seçim üretmez.

## Başlangıç uyum göstergesi

Betimsel UYUMLU etiketi için **iki şart birlikte** gerekir:
1. Ana makinenin zirvedeki tercihi, P0'ın yedi olay içindeki zirvedeki tercihiyle aynı olmalı.
2. P0'ın **aynı olaya** verdiği yüzdeyle model yüzdesinin mutlak farkı **en çok 5 yüzde puanı** olmalı.

Aksi hâlde UYUMLU_TAHMIN_BULUNAMADI; seçili piyasa grubu eksikse P0_SAME_MARKET_UNAVAILABLE. 3/5/7 yüzde puanı sınırları aynı raporda yalnız duyarlılık amaçlı görünür. Bu eşikler **sonuçlarla doğrulanmamıştır**; risk ya da isabet garantisi değildir.

Örnek: model MS1 %62, P0 aynı MS1 %59; P0'ın en yüksek olayı da MS1 ise betimsel uyum var. P0 KG Var'ı daha yüksek buluyorsa yüzdeler yakın olsa da zirve tercihleri uyuşmaz.

## Güvenlik ve kaynak

- Önce imzalı, model-first ana kararın SHA'sı ve yedi olayda seçilen maksimum doğrulanır.
- Yeni maçta orijinal PDF SHA'sı, ilk-PDF kayıt SHA'sı, forecast SHA'sı, resmi fikstür kimliği (lig/ev ID/deplasman ID/tarih/başlama saati) ve PDF'nin modelden ve KO'dan önceki zamanı kontrol edilir.
- Yalnız iddaa.com ilk kullanıcı PDF'si; **ikinci PDF fiyatları, ağdan odds yeniden çekme, Pinnacle, lisanslı xG yok.** Eksik oran doldurulmaz.
- Eski arşivdeki ilk oran transkripsiyonları ayrı orijinal mühür SHA'sıyla eşleştirilebilir. Bunların özgün PDF baytları repo içinde bulunmadığından **bağımsız canlı fiyat kanıtı değildir**.
- Bu yan süreç B/C2/C3/M4 modellerini veya üretim dalını değiştirmez; bahis ya da kârlılık yetkisi vermez.

## İlk PDF imzalı oturumunda çalıştırma

    python experiments/p1_market_intelligence/p2_market_alignment.py --session-file /tmp/iddaa_first_model_session.json --output /tmp/p2_morning_alignment.json

İsteğe bağlı tam-yedi-oran P1 araştırma gölgesi:

    python experiments/p1_market_intelligence/p2_market_alignment.py --session-file /tmp/iddaa_first_model_session.json --include-p1-research --output /tmp/p2_with_p1_shadow.json

21 Kasım'daki ilk fiyat arşivi üzerinde salt-okunur geçmiş gözlem:

    python experiments/p1_market_intelligence/p2_market_alignment.py --repo-root . --archive-dir experiments/263/second_pdf_commentary_archive_263/2026-11-21 --output /tmp/p2_historical_descriptive.json

## İlk kabul durumu

- 21 Kasım arşivi: 12 fiyat kaydı, 7 tanesinde tam MS/KG/2.5 ve SHA-karar bağlantısı, 5 kayıt 2.5 eksik olduğu için dışarıda.
- GitHub P1 isolated market research CI kapsamında P2 hash, kaynak, zaman, karşılaştırma ve oturum testleri.
- P0/P1'nin 2.131 maçlık 22 Kasım denetiminde, 1.066 maçlık testte P0 olasılık kalitesi Brier/log-loss açısından daha iyi; P1'in bir ekstra doğru tercihi istatistiksel üstünlük değil. Tarihsel 1xBet kapanış veri kaynağını iddaa olarak sunmuyoruz.
- Üretim seçimine terfi: **HAYIR**. Yeni, bağımsız P2 yan raporu: **EVET**. Gerçek maç sonuçlarında uyum eşiklerinin doğruluğu: **HENÜZ GÖSTERİLMEDİ**.
