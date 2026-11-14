# Veri sonrası ilk model denetimi — 8 Kasım 2026 / mevcut 39 mühürlü sonuç
**14 Kasım 2026; araştırma-only; M4 dondurulmuş; yeni maç önü mührü üretilmedi.**

## Kanıt ve karşılaştırılabilirlik
- Eski `new100` 8 Kasım mühürleri: **40 adet**.
- Eski maç-sonu arşivinde **39 skor**, 1 erteleme; ertelemeden skor türetilmedi.
- 39'un SHA-kilidi, fixture/lig/başlama saati, `created_at` ve maç öncesi kaynak zamanı kontrol edildi. **B:34**, **C2:38**, **C3:39**, **M4:39** maçta mevcut. Dört modelin **aynı 33 maçta** beraber hesapladığı adil alt örneklem karşılaştırıldı.
- Sonuç kanıtı: **3 doğrudan TFF ağ kontrolü**, **36 önceki web araştırma kaydı** (22 resmî lig, 13 kulüp, 1 dış federasyon); **0 insan tarafından resmî attestasyon**. 36'sı bağımsız canlı kaynak doğrulaması olmuş gibi gösterilmez.
- Kaynak: [SHA ve kanıt düzeyine göre otomatik 39 skor raporu](./NOV8_39_OLD_SEALS_MODEL_OUTCOME_PROVISIONAL_ONLY_20261114.json); [GitHub Actions başarı testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43621736307). Sonuçlar ikinci kez internetten toplanmadı.

## Aynı 33 maçta olasılık hata karşılaştırması
Aşağıda **düşük log-loss iyidir**; başarı yüzdesi aynı 33 maç üzerinde `top1`/0.5 yön ölçüsüdür, bahis veya EV ölçüsü değildir.

| Model | MS 1X2 log-loss | MS yön doğru | KG log-loss | KG yön doğru | 2.5 Alt/Üst log-loss | 2.5 yön doğru |
|---|---:|---:|---:|---:|---:|---:|
| B | 0.927260 | 20/33 | 0.663762 | 21/33 | 0.706617 | 16/33 |
| C2 | 0.901142 | 19/33 | **0.640458** | 22/33 | 0.688458 | 20/33 |
| C3 | 0.896860 | 20/33 | 0.661900 | 17/33 | **0.672934** | 18/33 |
| M4 | **0.892151** | 20/33 | 0.662899 | 18/33 | 0.695708 | 19/33 |

Brier doğrulaması (aynı 33): MS B .545981 / C2 .533836 / C3 .526883 / **M4 .523029**; KG B .235623 / **C2 .223872** / C3 .234712 / M4 .235394; 2.5 B .255127 / C2 .247125 / **C3 .239510** / M4 .250321. Sonuç yalnız bu alt grup içindir. 1.5 ve 3.5 için değerler kaynak JSON'dadır; line seçimini yüksek olasılıklı 1.5 üstüne otomatik kaydırmak yasaktır.

## Gerçek mühendislik kararı
- Sonuçlarda **M4'ün MS olasılık kalitesi hafifçe iyi**, KG ve 2.5'te **aynı model en iyi değil**. Bu, dört-model farklı pazar karşılaştırmasının neden gerekli olduğunu gösteriyor.
- **N=33 yeterli değil**; 36 web araştırma skoru ağdan tekrar doğrulanmadığından istatistiksel üstünlük veya model terfisi kararı yok.
- Yeni pilot başlatma, eski 39 maç önünü yeniden mühürleme, M4 katsayılarını değiştirme, odds/EV getirisi uydurma veya 4.218 yeni lig skoru ile izinsiz eğitim **yapılmadı**.
- Önceki kullanım kararı olan **kilitli M4** bozulmadı. KG ve Üst için C2/C3 daha iyi görünen pazarlar mevcut; ayrı, kaynak güvenilirliği ve daha geniş ileri veriyle eşit örneklemde izlenir.
- Geçmiş maçların skoru, aynı maçın maç öncesi girdi özelliği olarak kullanılmaz.

**Sıradaki ihtiyaç:** İleriye dönük yeni maç sonuçlarının aynı SHA-mühürlü karşılıklarıyla puanlandığı, kanıt düzeyi açık bir **devam eden kayıt dizisi**; yeniden bir 96'lık ya da 100'lük pilot sayacı icat etmek değil. Kullanıcı xG manuel girişini bağımsız tamamlayabilir.
