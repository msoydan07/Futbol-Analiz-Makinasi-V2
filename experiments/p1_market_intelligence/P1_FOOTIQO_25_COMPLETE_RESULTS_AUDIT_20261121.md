# P1 — Footiqo ham yedi fiyat + tamamlanmış 25 maç sonuç denetimi

**Tarih:** 21 Kasım 2026. **Araştırma dalı:** `experiment/p1-market-intelligence-20261121`. **Üretim değişikliği:** YOK — ana M4/C3, 10 lig, 2.6.3, karar v4 ve mevcut mühürler değişmedi.

## Veri kaynağı ve sınırlar

- Kullanıcının resmî manuel dışa aktardığı Footiqo **Premier League 2026/27 Odds XLSX:** 25/25 satırda MS 1/X/2, 2.5 Alt/Üst, KG Var/Yok yedi tam fiyat. Kaynak beyanıyla **1xBet kapanış ham fiyatları**; gerçek fiyat görüntülenme/zaman damgası **bağımsız olarak mühürlenmemiştir**.
- Kullanıcının son yüklediği **Scores XLSX (2)**: 21 farklı maç, sonuç dağılımı 10 ev sahibi / 4 beraberlik / 7 deplasman. Maç ID, tarih, lig, sezon, ev/deplasman adları **21/21 tam eşleşti**; ek skor satırı yok.
- 5 Eylül 2026 tarihindeki eksik dört sonuç, webdeki kulüp/lig resmî sayfalarından bağımsız olarak tamamlandı (kullanıcı XLSX'inden gelmiş gibi gösterilmedi):
  1. Brighton – Leeds **1-1**: https://www.brightonandhovealbion.com/match-centre-table?gameId=2645217
  2. Fulham – Crystal Palace **2-3**: https://www.premierleague.com/en/match/2645219/fulham-vs-crystal-palace/commentary
  3. Nottingham Forest – Tottenham **0-0**: https://www.premierleague.com/en/news/4719837/premier-league-match-round-3-key-match-incidents-panel-outcomes
  4. Newcastle – Bournemouth **2-2**: https://www.nufc.com/2026-27html/2026-09-05bournemouth-h.html
- 25/25 maçın tam sonucu (webde doğrulanan dört dahil): **10 ev sahibi, 7 beraberlik, 8 deplasman galibiyeti**.
- **Ham kullanıcı XLSX, yedi ham oran, maç bazlı olasılıklar, kişisel dosyalar bu kamu deposuna yüklenmedi**. Ayrı özel Excel raporu yalnız sohbet dosyası olarak oluşturuldu. Footiqo veri atfı: https://footiqo.com/database/.

## Sabit P0 ve P1 sürümüyle geriye dönük karşılaştırma

P0: Her bir pazar grubunun 1/oran'larını ayrı normalize et. P1: Bu üç P0 olasılık ailesine bağımsız ters Poisson gol modeli uydur. Yedi olay üç ayrık pazar ailesidir; yedi sonuç tek dağılım değildir. Ana tercih: olasılığı en yüksek tek aday. Hata: her pazarın proper Brier ve log-loss değeri, üç pazarın makro ortalaması.

| Kohort | P0 ana isabet | P1 ana isabet | P0 Brier ↓ | P1 Brier ↓ | P0 Log-loss ↓ | P1 Log-loss ↓ | Aynı ana tercih |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Yalnız 21 kullanıcı XLSX eşleşmesi** | 12/21 (%57,14) | 13/21 (%61,90) | **0.506299** | 0.506831 | **0.767022** | 0.767328 | 19/21 |
| **4 dış skorla tamamlanan 25 maç** | 15/25 (%60,00) | 16/25 (%64,00) | **0.517116** | 0.521048 | **0.782865** | 0.788313 | 23/25 |

**Farklı ana tercihler yalnız iki maçta:**
- Sunderland – Fulham **1-0**: P0 KG Var seçti (yanlış), P1 2.5 Alt seçti (doğru).
- Newcastle – Liverpool **2-2**: P0 KG Var (doğru), P1 2.5 Üst (doğru).

Diğer 23 maçta aynı ana seçim; bu yüzden **P1'in +1 ana isabeti yalnız bir karara dayanıyor**. 21 ya da 25 maç kalibrasyon öğrenmek veya P0/P1 model üstünlüğünü istatistiksel olarak kanıtlamak için yeterli değildir. Kaynak fiyatlarının maç öncesi gerçek zamanına ait independent as-of sertifikası yok; bahis getirisi, pozitif EV, canlı sistem terfisi veya karar v4 değişimi **yok**.

## Sonuç ve sonraki veri kapısı

Kullanıcıya yeniden dört maç için export yaptırmadan kamuya açık doğrulanmış skorlarla ilk **25/25 fiyat-sonuç** karşılaştırması tamamlandı. Araştırma skalası artacaksa lig/sezon sınırlaması dayatmadan **aynı-bookmaker fiyatlı başka dönemlerin kullanıcı tarafından resmî manuel exportları** ayrı cohortlar halinde kabul edilir. **Tek küçük örnek üstünden ilave matematik, kalibrasyon veya üretim iyileştirmesi ilan edilmeyecek.**
