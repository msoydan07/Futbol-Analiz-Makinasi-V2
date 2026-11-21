# P1 — 21 Kasım 2026 | Kaynak genişletme ve eşleşik belirsizlik denetimi

**Kapsam:** Bağımsız P0/P1 araştırma dalı. Ana 2.6.3 M4/C3, karar v4, aktif on lig, kullanıcının ilk/ikinci PDF akışı ve SHA mühürleri **değişmedi**.

## 1) Kapanış piyasa uzlaşısı: aynı maçlarda eşleşik denetim

**Çalıştırma:** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44945735718 (**başarılı**). GitHub Actions, lisanslı OddsIntel örneğini commit `622bd876667ce1d1b6e831e25b3a2b4ed5e1f9fc` üzerinden bir kez geçici olarak indirdi; arşiv CSV'yi GitHub'a kopyalamadı. Tam yedi oranlı **3626/4468**; ilk **3091** maç öğrenme, son **535** maç test; test **yalnız 19–22 Ekim 2026** (4 takvim günü).

| Yalnız son 535 test maçında | P0 (piyasa uzlaşısı) | P1 (ters Poisson) |
| --- | ---: | ---: |
| Brier (3 pazar makro) | **0.514211** | 0.514637 |
| Log-loss (3 pazar makro) | **0.772732** | 0.773557 |
| 7 adaydan en yüksek olasılıklı tercih isabeti | **336 / 535** | 332 / 535 |

**Eşleşik fark, P1 − P0:**
- Brier: **+0.0004263** (olumlu değil). Takvim günü blok bootstrap (%95, 2000 tekrar): **−0.0000078 ile +0.0012293**. Sıfırı içeriyor.
- Log-loss: **+0.0008249**. Aynı blok bootstrap: **+0.0001381 ile +0.0023282** (P0 yönünde; **yalnız dört gün** olduğu için farklı dönemlere genellenemez).
- Ana tercih isabet farkı **−0.75 yüzde puanı**. Aynı 535 maçta yalnız **14 ayrışan isabet**: P0 doğru/P1 yanlış **9**; P1 doğru/P0 yanlış **5**. Eşleşik kesin McNemar testi **p = 0.424** (gün bazlı kümelenme için düzeltilmemiş). **P1 veya P0 lehine kalıcı isabet üstünlüğü kanıtı yok.**
- Sıcaklık kalibrasyonunda da P0 az farkla önde (holdout Brier **0.513956** vs P1+kal **0.514449**). Parametreler son dört güne bakmadan ilk 3091 maçtan öğrenildi.

**Kritik sınır:** Fiyatlar bir tek bahis şirketinin marjlı açılış oranları değil, **zaten marjı alınmış birkaç şirketin kapanış uzlaşı fiyatları**. Tek kaynak, 13 gün ve heterojen 435 organizasyon. Kaynak fiyatlarının gerçek maç öncesi gözlem zamanları bağımsız olarak doğrulanmadı. Bu deney normal iddaa PDF akışında otomatik kalibrasyon veya para kazanma beklentisi yaratmaz.

## 2) Gerçek tek bahis şirketi + yedi ham fiyat: birinci kaynak adayı

**[Footiqo ücretsiz tarihsel veritabanı](https://footiqo.com/database/)** ve [Premier League Odds sekmesi](https://footiqo.com/database/leagues/england-premier-league/) 1xBet kaynaklı kapanış fiyatlarını açıkça **MS 1/X/2, 2.5 Alt/Üst, KG Var/Yok** olarak listeliyor; aynı maçın sonucu skor tablosunda aynı `id` ile mevcut. Sitede geçmiş sezonlar ve CSV/Excel **manuel export** düğmeleri bulunuyor.

**Gözle doğrulanan ham fiyat örneği:** Arsenal–Coventry, 21.08.2026, MS (1.20,7.97,13.80); 2.5 Üst/Alt (1.54,2.53); KG Var/Yok (2.22,1.66). Üç pazarın bahisçi marjı sırasıyla yaklaşık **%3.13, %4.46, %5.29**. Bu, önceki OddsIntel fair-consensus örneğinden farklıdır. Arsenal 3-0 skorunu TNT Sports kayıtları da doğruluyor: https://www.tntsports.co.uk/football/premier-league/2026-2027/arsenal-coventry-city_mtc21883135/live.shtml . Diğer örnek Hull–Manchester United 22.08.2026 2-0 sonucu kulüp sitesiyle örtüşüyor: https://www.manutd.com/en/matches/mens-team/hull-city-v-manchester-united-premier-league-20260822 . Birkaç skor örneği genel veri bütünlüğünün ispatı değildir.

**Kullanım izni şartı netleştirildi (08.10.2026):** https://footiqo.com/dataset-licence/ — Siteye uygun resmî **manuel CSV/Excel dışa aktarımı ve özel, ticari olmayan modelleme/geri test** serbest. **Programla scraping, otomatik export veya toplu site çıkarımı yazılı izin olmadan yasak**; ham verileri kamu GitHub deposuna koymak yasak. https://footiqo.com/terms-of-use/ . Ayrı ücretli 50 maçlık örnek değil; sitenin **ücretsiz kamu lig tablosu** araştırma için öncelikli. Hangi lig/sezon satırlarının eksiksiz yedi fiyatı olduğunu, export dosyasını fiilen elde etmeden söylemek mümkün değil.

## 3) Teknik karar ve sonraki kabul ölçütü

- Artık P1 tarihsel araştırmasında **10 lig / üç sezon / asgari 1000 maç dayatması yok**; nitelikli çok tarihli geçmiş maç olması yeterli.
- P1 için tercih edilen birinci kohort: `1xBet / Footiqo / pre-match closing / aynı maç-kimliği / aynı yedi ham fiyat / resmî manuel export`.
- İddaa ve 1xBet fiyatlarını, önceden marjı kaldırılmış uzlaşı fiyatlarını, açılış ve kapanışı **tek fiyat kaynağı gibi karıştırma**.
- Her bağımsız fiyat arşivinde kaynağın hakları, maç öncesi açıklaması, eksik değer, eşleme ve sonuçlar kontrol edilmeli. **Tek maçlık gerçek as-of imza**, sadece sitede `closing` yazmasıyla kanıtlanmaz.
- Güncel adımda **yeni 1xBet satırları indirilmedi veya test edilmedi**. Kaynak sayfasına otomatik bot bağlanmayacak. Kullanıcı veya kendisinin açıkça yetkilendirdiği normal manuel export üzerinden alınmış CSV gelirse mevcut P1 kabul/test katmanı kullanılabilir.
- M4/C3'ye herhangi bir yeni model terfisi yapılmadı. 13-gün örneğinden otomatik üretim kalibrasyonu yapılmayacak.

**Sonuç:** Tek bahis şirketi + yedi ham fiyat içeren **izinli manuel export kaynağı bulundu**. 3626-maçlık konsensüs çalışmasına eşleşik istatistiksel denetim eklendi; kayda değer ve genellenebilir P0/P1 üstünlüğü henüz kanıtlanmadı. Eksik kalan gerçek ham 1xBet CSV ve bağımsız zaman/doğruluk kontrolüdür.
