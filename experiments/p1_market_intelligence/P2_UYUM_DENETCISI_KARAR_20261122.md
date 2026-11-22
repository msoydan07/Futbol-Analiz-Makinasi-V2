# P2 — Üçüncü Makine (P0 ile M4/C3 uyum denetçisi)

Tarih: 22 Kasım 2026. Dal: experiment/p1-market-intelligence-20261121.

## Sözleşme: yeni tahmin yok

- Ana 2.6.3: MS 1/X/2 için M4; KG Var/Yok ve 2.5 Alt/Üst için C3. Mevcut model-first v4 kararından yedi olayın en yüksek gerçekleşme olasılıklı ana tercihi. Önceden mühürlenmiş karar, SHA ve alternatif korunur.
- P0: Kullanıcının **ilk** iddaa.com PDF'sindeki MS, 2.5 ve KG oranlarını üç **ayrı** pazar içinde marjdan arındırır. Yedi olay yüzdesini gösterir; yedi olay birbirini dışlayan tek dağılım değildir.
- P1: Aynı oranlara bağımsız Poisson uyduran **piyasa yeniden ifadesi**. Bağımsız futbol verisi içermez; araştırma için saklanır.
- P2: **İki bağımsız zirve kararını** yan yana koyar: (A) ana makinenin SHA'lı 7 olay içindeki kendi en yüksek kararı; (B) P0'ın üç tam pazarından bağımsız seçtiği kendi en yüksek kararı. **Önce olay kodu aynı mı? Yalnız aynıysa iki makinenin kendi zirve yüzdeleri yakın mı?** Model tercihine P0'ın verdiği yardımcı yüzdeyi ana karşılaştırma yerine kullanmaz. Yeni hibrit yüzde ve yeni seçim üretmez.

## Başlangıç uyum göstergesi

Betimsel UYUMLU etiketi için **iki şart birlikte** gerekir:
1. Ana makinenin zirvedeki tercihi, P0'ın yedi olay içindeki zirvedeki tercihiyle aynı olmalı.
2. Şart 1 sağlanmışsa **ana makinenin kendi zirve yüzdesi** ile **P0'ın kendi zirve yüzdesi** arasındaki mutlak fark **en çok 5 yüzde puanı** olmalı. Şart 1 sağlanmadıysa yüzdeler karşılaştırılmaz; `yüzde farkı = —`.

Şart 1 sağlanmazsa `TERCIHLER_FARKLI`; şart 1 sağlanır ama yüzdeler yakın değilse `YUZDELER_UZAK`; iki şart sağlanırsa `UYUMLU`. **Herhangi bir piyasa grubu eksikse**, yedi olayın gerçek piyasa zirvesi bilinmediğinden `P0_SEVEN_MARKETS_INCOMPLETE` (`-` ile ana tercih fiyatlanmamışsa `MODEL_TOP_CHOICE_NOT_OFFERED_IN_PDF`). Böyle bir durumda P0'ın zirvesi ve iki şart `DEĞERLENDİRİLEMEDİ` olarak kalır, eksik sayı uydurulmaz. 3/5/7 yüzde puanı sınırları aynı raporda yalnız duyarlılık amaçlı görünür. Bu eşikler **sonuçlarla doğrulanmamıştır**; risk ya da isabet garantisi değildir.

Örnek: Ana makinenin **kendi zirvesi MS1 %62** ve piyasanın **kendi zirvesi MS1 %59** ise 3 puan farkla betimsel uyum var. Piyasanın zirvesi **KG Var %60** ise, ana MS1 %62 ile farklı olaylar olduğundan **yüzde farkı hesaplanmaz**, yalnızca `TERCIHLER_FARKLI` bildirilir.

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

## Geçmiş kayıtlar ve yeni iki şartlı format

21 Kasım ilk fiyat arşivinde tam yedi piyasası bulunan 7 kayıttan 4'ü iki zirve kriterine göre betimsel uyumlu, 3'ü değil. Eski tasarımın "model tercihi için P0 yüzdesi" sütunu **yeni üçüncü makine ekranında kullanılmaz**. Yalnız iki **bağımsız lider** gösterilir; farklı liderlerde yüzdeler arası fark sütunu boş olur.

22 Kasım'daki **araştırma** örneği (özgün PDF GitHub koşucusunda yeniden açılmadı, resmî mühür olarak sunulmaz):

| Maç | Ana makine kendi zirvesi | P0 kendi zirvesi | Şart 1 | Şart 2 | P2 |
|---|---|---|---|---|---|
| Erzurumspor–Göztepe | MS2 %52,72 | 2.5 Alt %55,30 | HAYIR | BAKILMAZ | TERCIHLER_FARKLI |
| Konyaspor–Beşiktaş | KG Var %54,91 | MS2 %60,30 | HAYIR | BAKILMAZ | TERCIHLER_FARKLI |
| Kasımpaşa–Alanyaspor | KG Var %52,40 | KG Var %52,74 | EVET | EVET (0,34 puan) | UYUMLU |
| Trabzonspor–Eyüpspor | MS1 %85,54 | P0 yedi seçenek zirvesi belirlenemiyor (MS1 `-`) | DEĞERLENDİRİLEMEZ | BAKILMAZ | MODEL_TOP_CHOICE_NOT_OFFERED_IN_PDF |

**Not:** P0 ve P1 aynı oran verisinin farklı matematiksel ifadeleridir. Ana P2 kıyasının piyasa tarafı P0'dır, P1 ayrı araştırma göstergesidir. 5 puan eşiği tarihsel başarıya göre doğrulanmış değildir.

## 22 Kasım ek kararı: iddaa'da '−' görülen favori seçim

Kullanıcının Trabzonspor–Eyüpspor ekranında **MS1 `-`**; MSX **8.21**, MS2 **16.50**. Bu durum sayfada **seçenek oranının yayımlanmaması** olarak kabul edilir. Bunun nedeninin favorinin büyük üstünlüğü olduğu, platformun genel eşiği veya bilinçli oran kısıtı olduğu **kaynak veriden kanıtlanamaz**.

- PDF parse edilen **14 slot** yapısını yine kesin korur. Literal `-` varsa ilgili seçim `not_offered_pdf_market_keys` içine, fiyatı görünen ama grup tamamlanmamış diğer karşılıklar `partial_quoted_prices_no_no_vig` içine eklenir. Kayıt SHA ile korunur.
- Örnekte MS 1/X/2 üçlüsü **tam olmadığı** için MS marketinin no-vig olasılığı hesaplanmaz. MSX/MS2'nin görünen fiyatları kayıtlı kalır; MS1 fiyatı/yüzdesi **türetilmez**.
- KG ve 2.5 Alt/Üst'ün kendi iki karşılıkları tam ise P0 hesapları sürer. P1 yedi fiyatı gerektiriyorsa araştırma analizi açıkça **tam fiyat yok** etiketlidir.
- M4/C3'ün önceden oluşturulmuş MS1 tahmini bu piyasa eksikliğinden **etkilenmez**.
- P2'de modelin ana olayı PDF'de `-` ile fiyatlanmamışsa **MODEL_TOP_CHOICE_NOT_OFFERED_IN_PDF**; diğer tam pazarların model/P0 karşılaştırmaları yine ayrı listelenir. Asla bu gözlemi bir yenilgi, model hatası, UYUMLU ya da sahte tam-yedi-market başarısı gibi sunmaz.
- Bir başka grupta fiyat eksikse, tam yedi olay üzerinden küresel tepe bilinmediğinden `P0_SEVEN_MARKETS_INCOMPLETE` korunur. Sahte pozitif uyum etiketi verilmez.
- Bu bir **araştırma dalı kod düzeltmesidir**; mevcut ana mühürler ve onaylı üretim değiştirilmedi.

Doğrulama: [22 Kasım unquoted-favorite CI: 53 P0/P1/P2 testi + 1 ilk-PDF kaynak anomali testi + 5 model-köprüsü testi, başarı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/45005090400).

## 22 Kasım ek güvenlik denetimi — MS1 ile sınırlı DEĞİL

Fiyatlanmamış (`-`) seçim kuralı **MS1, MSX, MS2, 2.5 Alt, 2.5 Üst, KG Var, KG Yok** için aynıdır. Favorinin ev/deplasman olmasına göre istisna yaratılmaz. Yalnız ilgili fiyat grubunun piyasa olasılığı boş kalır; tamamlanmış başka gruplar hesaplanır; ana M4/C3 SHA/tercih korunur. Oran verilmeme sebebi kaynakta açıkça açıklanmıyorsa **uydurulmaz**.

Denetim: yedi farklı fiyatlanmamış seçim için gerçek PDF-first fiyat-snapshot yolu ve yedi farklı ana-model seçim türü için P2 karşılaştırması ayrı alt testler olarak denendi. [GitHub tek kabul koşusu: 54 P0/P1/P2 + 2 PDF kaynağı + 5 model köprüsü testi, toplam 61 test başarılı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/45005264328). Üretim dalı değiştirilmedi.

## Nihai düzeltme — 22 Kasım iki bağımsız zirve kararı

P2 kodunun `_align` fonksiyonu artık önce ana modelin zirve seçimini, ardından **ana seçime bakmadan** P0'ın yedi sonuç içindeki bağımsız zirvesini belirler. `condition_1_same_top_choice` şart 1, `condition_2_top_probabilities_close` şart 2'dir. Farklı seçime ait yüzdeler karşılaştırılmaz: `signed_gap_pp` ve `absolute_gap_pp` null olur; ikinci şart null olur. Fiyatı tam olmayan piyasalarda P0 küresel zirvesi uydurulmaz; şartlar null olur. Tam kaynak SHA, orijinal model tahmini ve mühür değişmez. Canlı üretime henüz aktarılmaz.
