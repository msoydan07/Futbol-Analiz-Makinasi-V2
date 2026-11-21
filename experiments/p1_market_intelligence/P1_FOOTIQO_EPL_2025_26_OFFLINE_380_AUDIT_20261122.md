# P1 — Premier League 2025/26 | Kullanıcı bilgisayarında 380 maçlık P0/P1 çevrimdışı tarama

**Rapor tarihi:** 22 Kasım 2026 (Türkiye). **Girdi:** kullanıcının kendi Windows bilgisayarında `P1_KONTROL_ET.py` çalıştırarak ürettiği yalnız toplu `P1_TOPLU_KONTROL_RAPORU.txt`. Ham Footiqo Excel dosyaları **kamu GitHub deposuna kopyalanmadı**.

**Çevrimdışı rapor SHA-256:** `f4ed87e02a45fe7283326de8d038713f0011ddff1e5cccc60f7f92543e8cb39d`. Bu yalnızca rapor bütünlük izidir; orijinal oranların maç öncesi yakalanma zamanı için kanıt değildir.

## Kabul edilen sonuç (yerel programın bildirimi)

| Ölçüm | Sonuç |
| --- | ---: |
| Oran tablosu satırı | 380 |
| Sonuç tablosu satırı | 380 |
| Yedi fiyatı bulunan | 380 |
| ID/tarih/takım/lig/sezon eşleşip skorla hesaplanan | 380 |
| Sonucu eksik / ret | 0 / 0 |
| MS ev sahibi/beraberlik/deplasman | 162 / 104 / 114 |
| P0 ana tercih isabeti | **226/380 (%59.47)** |
| P1 ana tercih isabeti | 223/380 (%58.68) |
| P0 makro Brier | **0.529962** |
| P1 makro Brier | 0.530450 |
| P0 makro log-loss | **0.793779** |
| P1 makro log-loss | 0.794603 |
| Aynı ana tercih | 340/380 |

**Mühendislik yorumu:** P0, bu tek-sezonluk **geriye dönük** kontrolün isabet ve proper-score sayılarında küçük farkla önde. **Hiçbir istatistiksel üstünlük kanıtı, kalibrasyon öğrenimi veya canlı sistem terfisi** değildir. Yedi sonuç üç ayrı tam pazar ailesidir, tek 7'li ayrık dağılım değildir.

**Kaynak/zaman notu:** Footiqo, fiyatları 1xBet kapanış fiyatları olarak **beyan eder**, ancak maç öncesi fiyatın bağımsız gözlem zaman damgası doğrulanmış değildir. Yalnız toplu kullanıcı TXT'si görülmüştür; bu oturumda 380 ham XLSX satırı bağımsız satır-satır incelenmemiştir. Kullanıcı dosyaları sistemine aktarmadan kaynak ve lisans koşulları ayrı değerlendirilmelidir.

**Dosya adı ayrıntısı:** yerel raporda `Odds_2025_26.xlsx.xlsx` ve `Scores_2025_26.xlsx.xlsx` görünüyor; Python gerçek XLSX dosyalarını okuyabilmiş, bu nedenle çift uzantı sonucu bozmamış; gelecekte dosya uzantısı görünüm ayarı önerilir.

**Sıradaki tek operasyon:** ayrı klasörde Premier League **2024/25** tam-sezon Odds + Scores resmî manuel Excel dışa aktarımı, aynı 7 oran/sonuç kontrolünden geçirme. Sonrasında farklı lig ve tarih bloklarında ayırarak araştırma kalibrasyonunu öğrenme, ileri tarihli bağımsız holdout üzerinde denetleme. Uygun veri hakları ve kullanım kapsamı korunur.

**Ana 2.6.3/M4/C3, 10-lig kapsamı, SHA maç önü mühürleri ve karar katmanı aynen kalır.**