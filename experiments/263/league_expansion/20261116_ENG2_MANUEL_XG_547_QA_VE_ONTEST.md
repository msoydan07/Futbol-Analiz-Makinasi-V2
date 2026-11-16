# ENG2 xG elle giriş — 16 Kasım 2026, salt-okunur QA ve ön test

**Durum:** ARAŞTIRMA/ÖN SONUÇ. Kullanıcı 16 Kasım 2026 tarihinde `263_xg_90_MAC_KONTROL_EDILDI_20261115(3).xlsx` dosyasını sağladı. Orijinal Excel, ana M4, 10 liglik üretim, B/C2/C3/M4 kodu, mühürlü tahminler **değiştirilmedi**. Bu araştırma tek başına model kabulü veya eğitim izni değildir.

## Workbook QA
- `EKSIK_2025` içinde ENG2 **547/547** çift taraflı xG değeri sayısal dolu. Hepsinin kayıtlı URL alan adı `www.xg-edge.com` (ama URL ile maç eşleşmesi mutlaka denetlenmelidir).
- `EKSIK_2026` ENG2 **41/41** çift taraflı xG; 39 URL `www.fotmob.com`, 2 URL `xg.football`.
- `ESKI_459_KONTROL` ENG2 **129** daha önce dolu çift taraflı xG: 5'i 2025/26, 124'ü 2026/27. 547 yeni 2025/26 + 5 eski = 552 ayrı maç; aynı sağlayıcı **değil**.
- Yeni 547 maçta skor biçimi, xG 0–15 aralığı, maç ID ve lig kimliği düzeyinde incelenen temel kontroller geçiyor. **6 satırın kayıtlı URL'sinin takım ve tarihi Excel'den farklı** olduğu saptandı. Bu altı Excel xG çifti de yanlış maçın değerini içeriyordu. Diğer 541 satırda URL takım/tarih kuralına uyum var; **tüm değerlerin internetten satır satır doğrulandığı anlamına gelmez.**

## Düzeltme önerisi — orijinal Excel'i değiştirmeden
| EKSIK_2025 satırı | Maç | Excel ev/deplasman xG | Kaynak xG | Doğrulama |
|---|---|---|---|---|
|1608|Middlesbrough–Sheffield United, 30 Aug 2025|0.35/0.10|1.09/0.44|https://xg-edge.com/championship/middlesbrough-vs-sheffield-united-2025-08-30|
|1564|Sheffield Wednesday–Bristol City, 13 Sep 2025|1.50/2.06|0.83/1.39|https://xg-edge.com/championship/sheffield-wednesday|
|1252|Birmingham–Portsmouth, 1 Nov 2025|1.74/0.12|3.11/0.23|https://www.xg-edge.com/championship/2025/results?page=9|
|1204|West Brom–Oxford, 8 Nov 2025|1.13/1.29|1.61/0.95|https://www.xg-edge.com/championship/2025/results?page=8|
|829|Oxford–Bristol City, 17 Jan 2026|0.83/0.61|1.20/0.44|https://www.xg-edge.com/championship/2025/results?page=5|
|544|Watford–Ipswich, 24 Feb 2026|0.84/2.78|1.68/1.12|https://www.xg-edge.com/championship/watford-vs-ipswich-town-2026-02-24|

## İlk güncel pilot değildir: dış örneklem ön test
- Veri: yalnız kullanıcı Excel'indeki 547 ENG2 2025/26 satırı; 6 kimlik/hatalı xG özel çalışma kopyasında kaynakla düzeltildi; `ESKI_459_KONTROL` içindeki 5 farklı sağlayıcılı 2025/26 kayıtları **aynı sağlayıcı testine eklenmedi**.
- 283 maç 01.01.2026 tarihinden önce; daha sonraki 264 maçta **her hedef tarihten ÖNCEKİ** aynı lig verileri ile bir geçmiş gol ortalamalı model, bir geçmiş xG ortalamalı model, bunların beklenen gollerinin %50–%50 karışımı değerlendirilmiştir.
- Basit Poisson prototipi: ev takımı iç saha atak, deplasman takımı dış saha savunma, deplasman atak, iç saha savunma; k=5 global lig ortalamasına küçültme. Her tarih için yalnız eski maçlar.
- **BU TEST GERÇEK M4'ÜN SHA-KİLİTLİ PİLOTU ÜZERİNDEKİ TEST DEĞİLDİR.** B/C2/C3/M4 model sürümüne göre birebir performans iddiasında bulunmayın; basit kontrollü araştırma karşılaştırmasıdır.
- Brier (düşük daha iyi), gol temelli vs %50 karma: 1-X-2 **0.640797 vs 0.635597**; BTTS **0.249272 vs 0.249620**; O2.5 **0.252181 vs 0.250705**.
- Log-loss, gol vs karma: MS **1.058191 vs 1.051186**, BTTS **0.691568 vs 0.692308**, O2.5 **0.697991 vs 0.694885**.
- 61 maç gününü örnekleme birimi alan 1800 tekrarlı tarih kümeli bootstrap. Gol Brier – karma Brier farkının yaklaşık %95 aralıkları: MS **[-0.00418,+0.01640]**, BTTS **[-0.00467,+0.00391]**, O2.5 **[-0.00343,+0.00650]**. Üçünde de **sıfır içeriyor**; kesin kazanç kanıtı yok.
- Kısıtlar: kayıtlar 16 Kasım itibarıyla görülen xG revizyonlarını içerebilir, geçmiş zamanın gerçek mühürlü xG sürümü olmayabilir; yeni promosyon ligleri, 2026/27 FotMob–xg.football kaynak geçişi ve eksik güncel sezon maçları bu denemede temsil edilmez; testte yüzdeleri optimize edip sonradan seçmedik.

## Veri hakkı ve sonraki iş
xgEdge şartlarında veri üçüncü taraf sağlayıcının malı olarak anılır ve toplu kopyalama/yeniden yayımlama kısıtlanır: https://www.xg-edge.com/terms . Kullanıcının bireysel araştırma çalışma kopyası kamuya GitHub'a yüklenmemiştir. M4'e veri göndermeden önce lisans, data lineage, as-of ve aynı mühürlü kohort koşulları değerlendirilir.

**Ön karar:** Kullanıcının yeni el girişlerini çöpe atmaya gerek yok; 6 kayıt düzeltme istiyor, veri faydası için küçük sinyaller var fakat eşik geçilmiş değil. Ana M4 ve tüm mühürler sabit kalır.
