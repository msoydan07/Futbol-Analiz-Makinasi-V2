# P1 — 2.131 maç / 37 hafta | Kalibrasyonun nihai istatistiksel denetimi

**Denetim tarihi:** 22 Kasım 2026. **Araştırma dalı:** `experiment/p1-market-intelligence-20261121`. **Girdi:** Kullanıcının yerel, toplu `P1_KALIBRASYON_TOPLU_RAPOR.json` raporu. **SHA-256:** `cdacbe36b5eb16a6f92d9f61b8935cd0496868c9d0567b4e71547dd917498f34`. **Ham oran/fikstür satırları kamu GitHub'a taşınmadı.** Canlı M4/C3, 2.6.3 ve mühürler değişmedi.

## 1. Doğrulanan iç tutarlılık ve tarihler

- 6 lig-sezon klasöründen kabul **2.131**, `all_record_count=2131`; toplam `files[].accepted=2131`.
- Eğitim **2024/25: 1.065** (Almanya 305, İngiltere 380, İspanya 380), en geç **2025-05-25**; test **2025/26: 1.066** (Almanya 306, İngiltere 380, İspanya 380), en erken **2025-08-15**. Tarihler ayrı; **bu özetin içerdiği veri dışında as-of bağımsız doğrulama yok**. Almanya eski sezondaki 305/306 farkının sebebi JSON'da açıklanmaz; sağlayıcıdaki tek bir satır eksikliğini dışarıdan doğrulamadan kesin hata ilan etmeyin.
- Test ligleri toplamı **1066**, lig bazında P0/P1/P0_cal/P1_cal isabetleri ayrı ayrı **671/672/674/675** ve ağırlıklı Brier ölçümleri raporun global metrikleriyle uyuşuyor.
- Kaynağın beyanı `1xBet` `closing`; bağımsız timestamp sertifikası **yok**. Bu veri kamuya açık depoya kopyalanmaz, ticari kullanıma aktarılmaz.

## 2. 1.066 test maçında ana sonuç

| Araştırma varyantı | Doğru ana tercih | Brier ↓ | Log-loss ↓ |
|---|---:|---:|---:|
| P0 | 671/1066 (%62.9456) | 0.513458 | 0.773906 |
| P1 ters Poisson | 672/1066 (%63.0394) | 0.514496 | 0.775335 |
| P0 + yalnız 2024/25'ten sıcaklık | 674/1066 (%63.2270) | **0.513380** | **0.773737** |
| P1 + yalnız 2024/25'ten sıcaklık | **675/1066 (%63.3208)** | 0.514476 | 0.775304 |

Katsayılar: P0 **MS 1.04, O/U 1.04, KG 1.02**, P1 **MS 1.00, O/U 1.04, KG 1.04**. **Test sonuçlarına göre bu parametreler yeniden ayarlanmamıştır.** P0'daki kalibrasyon etkisi ΔBrier −0.0000785 ve Δlogloss −0.0001689; P1'de ΔBrier −0.0000194 ve Δlogloss −0.0000311. Her ikisinde ana tercih +3. Fark çok küçük.

## 3. Haftaya göre eşleşik bootstrap, 37 takvim haftası, 2500 tekrarlama

Tüm `delta` değerleri **ikinci model eksi birinci model**. Hata ölçülerinde **pozitif** fark, ikinci modelin daha kötü olduğu anlamına gelir.

| Karşılaştırma | Δ Brier (%95 CI) | Δ log-loss (%95 CI) | Δ ana isabet oranı (%95 CI) |
|---|---|---|---|
| P1−P0 | +0.0010376 (**−0.0000001, +0.0021099**) | +0.0014294 (**−0.0001081, +0.0029678**) | +0.0009381 (**−0.0086207, +0.0110599**) |
| P0kal−P0 | −0.0000785 (**−0.0003625, +0.0001978**) | −0.0001689 (**−0.0005379, +0.0001756**) | +0.0028143 (**−0.0027523, +0.0084112**) |
| P1kal−P1 | −0.0000194 (**−0.0002698, +0.0002402**) | −0.0000311 (**−0.0003085, +0.0002600**) | +0.0028143 (**−0.0009355, +0.0069170**) |
| **P1kal−P0kal** | **+0.0010967 (+0.0001965, +0.0020783)** | **+0.0015673 (+0.0001324, +0.0030414)** | +0.0009381 (**−0.0083411, +0.0107212**) |

**Kesin yorum:** Her iki model için ayrı kalibrasyonun iyileştirmesi **CI=0 içeriyor**; öğrenilen sıcaklıkları otomatik üretime almak için kanıt yetersiz. Kalibre P0, kalibre P1'e göre bu veride Brier ve log-loss'ta test-belirli CI'ları sıfırdan pozitif olan farkla önde; **isabet farkı istatistiksel kanıt göstermiyor**. `2025/26` sezonu önceki betimsel karşılaştırmalarda zaten görüldüğünden, bu daha sonra “hiç görülmemiş kör model seçimi” gibi sunulamaz. 37 hafta tek bir dönemdir; sonuçları diğer bookmaker, sezon veya gerçek iddaa akışına otomatik genelleme.

## 4. Lig ve pazar ayrımları

| Lig, 2025/26 | N | P0 / P1 ana isabet | P0kal / P1kal ana isabet | P0kal / P1kal Brier |
|---|---:|---|---|---|
| Bundesliga | 306 | 197 / 197 | 199 / 197 | **0.496443 / 0.497613** |
| LaLiga | 380 | 248 / 252 | 247 / 254 | **0.510049 / 0.512026** |
| Premier League | 380 | 226 / 223 | 228 / 224 | **0.530349 / 0.530506** |

- **Kalibrasyonun mutlak etkisi:** Almanya'da P0 Brier **0.496882 → 0.496443** iyileşti; İspanya'da **0.510302 → 0.510049** iyileşti; İngiltere'de **0.529962 → 0.530349** kötüleşti. P1'de İngiltere **0.530450 → 0.530506** kötüleşti. Bu nedenle lig farkları dikkate değer ama tek sezonla lig özel katsayı türetmeye gerek yok.
- **Kalibre pazar Brier:** MS **P0 0.582551 vs P1 0.584070**; 2.5 Alt/Üst **P0 0.475165 vs P1 0.474688** (P1 ufak üstün); KG **P0 0.482423 vs P1 0.484672**. Pazara özel anlamlılık CI'sı yok; pazar bazlı terfi yapılmaz.
- **Favori yüzde aralıkları:** P0 MS %70–80 grubu **72 maçta ortalama %74.93**, fiili **%83.33**; %80–90 grubu yalnız **25 maç**. KG P0 %50–60 grubu **783 maçta ortalama %54.70**, gözlenen **%57.34**. Ancak favori binleri modelden modele ve sıcaklık sonrası maç üyesi değiştiği için gözlenme farkları model avantajını doğrudan ölçmez. %80 üzeri küçük sayıları abartma.

## 5. Karar

1. **P0**, bağımsız P1 araştırmasında olasılık kalitesi için **referans yöntem** olarak kalır.
2. **P1** araştırma karşılaştırması olarak saklanır. Ters Poisson'un marjdan arındırılmış fiyatlara kayda değer artı bilgi kattığına dair kanıt yok.
3. **Kalibrasyon katsayıları araştırma çıktısıdır; üretime aktarılmaz.** Etki CI'ları sıfırı içeriyor. Test dönemi daha önce incelendiği için gelecek gerçekten yeni sezon/hafta mühürleriyle değerlendirme tercih edilir.
4. **Yeni Excel indirmek şimdilik gerekli değil.** Bir sonraki yararlı adım mevcut bültenlerde aynı maç önü oranlarını gerçek zaman damgasıyla P0/P1 için ayrı mühürlemek, daha sonra yorumlanabilir out-of-time test kurmaktır; ana karar v4 aynen kalır.
5. **Kârlılık, pozitif beklenen değer, gerçek bahis başarısı ve ligler arası kesin taşınabilirlik** bu rapordan çıkarılmaz.

**Veri tabanlı nihai ifade:** P0 olasılık kalitesinde daha iyi gözlemlendi; P1'in bir fazla isabeti üstünlük sağlamıyor; kalibrasyonun katkısı kanıtlanmadı. Ana 2.6.3 sistemde yapılacak değişiklik **yok**.
