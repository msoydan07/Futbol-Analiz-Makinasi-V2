# 2.6.3 — Rakip gücü ve gol pazarları: ilk toplu mühendislik sonucu (10 Kasım 2026)

**Durum:** `RESEARCH_COMPLETE_FOR_THIS_SINGLE_BATCH / PRODUCTION_UNCHANGED / NEW_SOURCE_PROVISIONAL`.

## 1. Kaynak ve yazılım güvenliği

- Önceden sınırlı araştırma için kabul edilmiş **4.518** tam skor, **10 lig**, SHA256 `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`.
- Çalışan `experiment/263-toplu-karsilastirma` M4 matematiği, B/C2/C3, kilit, mühürler, LITE, kasa, Pinnacle kotası ve `main` değişmedi.
- 10 ligde goller, tarih, kanonik takım kimlikleri var. Şut ve isabetli şut kapsaması **9 ligde %100**, `ENG2`'de **%98,74**. İstatistik alanlarının dolu olması sonuçların tek tek haricen doğrulandığını kanıtlamaz.
- Veri arşivinin her ligde son skoru **1–3 Kasım 2026** aralığında; 10 Kasım bazında **7–9 gün gecikme**. `xG`, pas konumu, pres/PPDA, diziliş, oyuncu/rotasyon, pozisyonun maç içi skor durumuna göre ayrılması bu kaynak CSV'sinde yok. **Bunların hiçbirini şuttan varmış gibi üretme.**
- Sahip kabulü 4518 satır için **tam bağımsız skor doğrulaması değildir**. Şutların sağlayıcıdan kaynaklanan tanım farkları (ör. Serie A'nın bazı yılları) ayrıca göz önüne alınır.

## 2. Rakip gücü analizi: mevcut M4 neden tamamen yanlış değil

- Mevcut M4 **rakibin hücum/savunma etkisini, iç-dış saha ve zaman aşımını** zaten öğreniyor. Bunun üzerine ikinci bir “güç çarpanı” eklemek çift sayım doğurabilir.
- Bu araştırma, motoru değiştirmeyen **yalnızca geçmiş maçları kullanarak yürüyen** lig-içi Elo proxy'sini (1500 başlangıç, ev +65, K=18) **tarihsel takım güç farkı segmentlerine** ayırdı. Aynı gün sonucu sonraki aynı gün maçı için kullanılmadı.
- 4.518 maçın **85**'inde ev sahibi en az 150 Elo daha güçlüydü: ortalama ev/deplasman golü **2,75 / 0,75**, 2,5 Üst **%64,7**, KG Var **%48,2**. +50 ila +150 güçlü ev sahibi **744** maç: toplam gol **2,13 + 0,96**, 2,5 Üst **%62,9**, KG Var **%57,0**. Bu ayrım, favorinin gol atmasıyla iki takımın gol bulmasının farklı riskler olduğunu vurgular.
- Elo nitel taktik etiket değildir: rakibin Beşiktaş'a karşı kapalı oynayacağını veya önde basacağını göstermez. Pres/alan kullanımı/oyun durumu için kanıtlı olay verisi gerekir; güncel 10 ligde tam olay verisi mevcut kaynakta yok.

## 3. M4 ve iki ortak-skor hipotezi — tek toplu retrospektif

Kaynak: eski arşiv içinden 2026/27 **985** skor; **984** maçta kilitli M4, aynı geçmiş **hafta başı** kesimi ile geçerli λ verdi. **1** maç M4 λ üretemedi ve ortak paydaya eklenmedi. Veri dönemi önceki araştırmalarda zaten görülmüştür: bu **bağımsız kör test değildir**.

Hipotezler önceden sabit:
- `DC_FIXED_RHO_NEG008`: Dixon–Coles benzeri yalnız 0–0/0–1/1–0/1–1 dağılımını değiştirir. Matematiksel olarak 2,5 ve 3,5 üstü **değiştirmez**.
- `BIVARIATE_FIXED_SHARED012`: gol beklentisinin bireysel marjinlerini koruyarak en fazla 0,12 ortak Poisson şoku ekler. Bu 2,5 golü de değiştirir.
- İkisi de kendi doğru toplamı %100 olan 1-X-2, KG ve gol çizgisi olasılığı verir; parametreler 2026/27 sonucuna göre ayarlanmadı.

| Brier (düşük iyi) | Orijinal M4 | DC -0,08 | Ortak-gol 0,12 |
|---|---:|---:|---:|
| MS 1-X-2 | **0,592469** | 0,593498 | 0,593404 |
| KG Var/Yok | 0,245660 | 0,245137 | **0,244928** |
| 1,5 Alt/Üst | 0,164989 | **0,164349** | 0,166244 |
| 2,5 Alt/Üst | **0,248558** | 0,248558 | 0,249043 |
| 3,5 Alt/Üst | 0,241554 | 0,241554 | **0,240759** |

**Karar:** KG ve bazı gol çizgileri için küçük keşifsel iyileşme var ama tüm pazarların ortak olasılık kalitesi ve MS birlikte iyileşmedi. **Model terfisi YOK.** Üstelik geçmiş pazar modelleri ve bu dönem başka araştırmalarda incelendiğinden tarih bloklu bootstrap aralıkları yeni bağımsız doğrulama yerine geçmez.

## 4. Daha önemli keşif: sezon gol ortamında farklılık

M4'ün 984 maçlık 2,5 Üst ortalama tahmini **%53,28**; aynı maçların gözlenen 2,5 Üst oranı **%60,57**. KG Var ortalama tahmini **%52,99**; gerçekleşen **%56,10**. Bu fark verinin yeniden doğrulanması, mevsimsellik, takım değişimi ve modelin geçmiş gol seviyesi ile açıklanabilir; bir hafta sonucu üzerinden sabit +%7,3 puan eklenmez.

Ayrıca toplam geçmiş veride 2025/26 ile mevcut 2026/27 golleri arasında bazı liglerde belirgin fark var; ör. İtalya Serie A 2,5 Üst **%45,8 → %61,0**, Belçika **%49,2 → %65,2**, İngiltere Championship **%50,7 → %61,2**. Bu fark tek başına kalıcı taktik değişim veya kaçınılmaz gelecekteki Üst avantajı değildir.

## 5. Yeni kaynak eşleştirmesinde gerçek ilerleme

Kullanıcının “eksik veriyi tamamla” isteği için mevcut 2026/27 Football-Data CSV'leri bir kez **hafif, özel araştırma kapsamındaki** erişimle kontrol edildi. Ham veri dışarı yayımlanmadı. Sitenin kullanım sınırları: https://football-data.co.uk/contact.php

- **10/10 ligde**, geçmiş 2026/27 CSV'sindeki `source_row` + tarih + skor + MS sonucu **tüm uygun eski kaynak satırlarında birebir eşleşti**. Eşleşen eski kaynak satırları: BEL1 89, ENG1 90, ENG2 156, ESP1 109, FRA1 81, GER1 72, ITA1 100, NED1 99, POR1 90, TUR1 90.
- Arşivin son skor tarihinden sonra **99 tamamlanmış maç adayı** tespit edildi. Lig dağılımı: BEL1 10, ENG1 10, ENG2 15, ESP1 10, FRA1 9, GER1 9, ITA1 10, NED1 9, POR1 8, TUR1 9.
- 99 adayda veri sağlayıcısının eski kulüp adı → kabul edilmiş kanonik takım kimliği eşlemesi geçici olarak çözülebildi. **Ancak maçların resmî federasyon skor/kimlik onayı, as-of kaynak güveni ve yayın/yeniden kullanım hakkı tamamlanmadan** 99 satır mevcut 4.518'e **eklenmedi**. Kaynak başvurusu art arda tekrarlanmadı.
- Bu önemli bir teknik engeli çözüyor; **“99 yeni resmî maç kesin doğrulandı” denemez.**

[Hafif güncel kaynak preflight kaydı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-data-source-preflight-20261110/research/opponent_goals/reports/current_source_preflight_20261110.json)

## 6. Kalan işler — bitmiş işi tekrarlama yok

1. 99 aday için sağlanan geçici kimlik bağlantısını kulüp/federasyon maç kimliği ve gerçek skor kaynaklarıyla **resmî olarak teyit edip**, yeniden kullanım haklarına uygun, tazelik damgalı *ayrı* kaynak kabulü hazırlamak. Eskisini asla sessizce değiştirme.
2. **KG ve Üst/Alt'da** aynı hafta-gününde hangi güç farkı ve veri kalitesi koşullarında daha fazla hata yapıldığını, gerçek yeni maçların bağımsız mühürlü sonucuyla izlemek. 2,5 Üst'te görülen sezon sapması öncelikli izleme konusu.
3. Rakip oyun kimliğinin gol çıkışını nasıl değiştirdiği için **gerçek olay/taktik verisinin güncel 10 lig kapsamını ve kullanım hakkını** teyit etmeden pres/oyun tarzı için numerik formül eklememe.
4. Yeterli yeni kanıt varsa ortak skor dağılımında **KG + 1,5/2,5/3,5 + MS** kalitesini birlikte iyileştiren ayrı araştırma adayını karşılaştır; eski mühürler, ana motor ve oranlar sabit.

**İşletim hükmü:** Mevcut M4 kullanılmaya devam; bu turda yapılan bağımsız veri-kapsam ve skor-dependence denetimleri başarılı. Kaynak köprüsünde ilerleme var, ancak güncel veri henüz üretime kabul edilmedi. Yeni model başarısı veya bahis kârı kanıtlanmış değildir.

## Kanıt

- [10 lig SHA/envanter + geçmiş-güç bantları](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-opponent-goals-20261110/research/opponent_goals/reports/source_and_opponent_inventory_20261110.json)
- [984 maç bütünlüklü KG/Üst/Alt karşılaştırması](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-opponent-goals-20261110/research/opponent_goals/reports/goals_weekly_2026_27_exploratory.json)
- [10 lig toplu test GitHub Actions](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42778696371)
- [Güncel kaynak kimlik testi GitHub Actions](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42779550632)
