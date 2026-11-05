# 5 Kasım 2026 UEFA Avrupa Ligi — maç öncesi 5 kapsam içi fikstür ön analizi

**Hazırlık:** 5 Kasım 2026, maçlardan önce. **Kapsam:** Kullanıcının kararı gereği UEFA'da iki tarafın da 9 üst-lig havuzunda bulunması şartı. İngiltere Championship bu kapsamda Avrupa için hariç. **Bu bir T−60 matematik / EV raporu değildir.**

**Asıl UEFA 2026/27 fikstür ve ilk 3 hafta sonuç kaynağı:** https://www.uefa.com/uefaeuropaleague/news/02a8-2174cafa5bb6-82bbc20c9b92-1000--2026-27-europa-league-all-the-league-phase-fixtures-and-re/

**UEFA Matchday 4 resmî ön incelemesi:** https://www.uefa.com/uefaeuropaleague/news/02aa-21f10ec08a8c-d0499acdffe2-1000--europa-league-matchday-4-briefing-five-sides-look-to-main/

| Türkiye KO | UEFA ID | Maç | 3 Avrupa maçı ev: G-B-M, gol | 3 Avrupa maçı dep: G-B-M, gol | Ön araştırma |
|---|---:|---|---|---|---|
| 20:45 | 2050121 | Crystal Palace – Hoffenheim | 1-1-1, 8:5 | 1-0-2, 5:5 | İki takımda da gol üretimi ve yenilen goller görülüyor; KG / 2.5 için matematik kontrolü yapılmalı |
| 20:45 | 2050115 | Real Sociedad – Lyon | 1-1-1, 8:3 | 2-0-1, 5:6 | Sociedad'ın 6-0 deplasman galibiyeti ortalamayı yukarı çekiyor; tek maç uç değeriyle favori ilan edilmez |
| 23:00 | 2050114 | AZ Alkmaar – Juventus | 2-0-1, 6:2 | 2-1-0, 9:3 | Juventus'un hücum profili güçlü ama AZ'nin de iki galibiyeti var; 1X2 tek yön şart değil |
| 23:00 | 2050111 | Leverkusen – Marseille | 3-0-0, 8:0 | 0-0-3, 1:6 | UEFA son üç maç eğilimi Leverkusen'i belirgin destekliyor; oran/EV yokken resmî değer önerisi yapılmaz |
| 23:00 | 2050123 | Celta – Union SG | 1-0-2, 3:4 | 2-1-0, 8:1 | Union SG'nin daha olumlu Avrupa formu var; lig gücü ve güncel veri ile denge testi şart |

Resmî maç sayfaları:
- https://www.uefa.com/uefaeuropaleague/match/2050121--crystal-palace-vs-hoffenheim/
- https://www.uefa.com/uefaeuropaleague/match/2050115--real-sociedad-vs-lyon/
- https://www.uefa.com/uefaeuropaleague/match/2050114--az-alkmaar-vs-juventus/
- https://www.uefa.com/uefaeuropaleague/match/2050111--leverkusen-vs-marseille/
- https://www.uefa.com/uefaeuropaleague/match/2050123--celta-vs-union-sg/

## T−60 kontrol
- **19:45 TSİ:** Crystal Palace – Hoffenheim, Real Sociedad – Lyon
- **22:00 TSİ:** AZ – Juventus, Leverkusen – Marseille, Celta – Union SG
- Makine için ayrı `experiments/263/europe/t60_requests/<slot>.json` dosyaları ilgili zaman diliminde resmî UEFA tekil maç sayfası kontrolünden sonra oluşturulmalı. Şimdi erken açmak süre penceresini bozabilir.
- GitHub T−60 kilidi, **M0 ve deneysel M0+Elo** olasılıklarını üretir; bunlar ulusal B/C2/C3/M4 dört-model kabul motoru değildir.
- Bu 5 maçta hesaplanmış T−60 yüzdeler, orijinal SHA-kilitli tahmin, ilk 11 doğrulaması, iddaa/Nesine karşı fiyatları ve matematiksel EV henüz mevcut değildir: bunlar **boş bırakılır**.
- İlk 11 zamanında tam teyit edilemezse **NOT_CONFIRMED** ve kıyaslamaya devam; oyuncu/istatistik uydurulmaz.
- **Celtic – Beşiktaş** kapsam dışıdır: İskoç ligi çalışma havuzunda yer almaz. Beşiktaş hakkında kanıtsız UEFA yüzdesi zorlanmaz.
- Bu hazırlık pilot kaydı veya tavsiye değildir; maç başlamadan önce ayrıca mühürlenmiş deneysel tahmin gerek.
