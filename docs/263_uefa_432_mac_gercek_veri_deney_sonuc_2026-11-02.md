# 2.6.3 — UEFA 432 maç: puan durumu / maç haftası gol etkisi deneyi

**Tarih:** 2 Kasım 2026 (analiz geçmiş UEFA sezonlarına aittir).
**İş:** Şampiyonlar Ligi ve Avrupa Ligi maçlarında, sadece takımın ligdeki gol
ortalaması yerine Avrupa'ya özgü rakip/gol geçmişi + puan + maç haftası
göstergelerini kullanmak gol tahminini gerçekten iyileştiriyor mu?

## Kısa mühendislik kararı

**Mevcut Avrupa tahminlerine hiçbir gol/tempo katsayısı ekleme.**
Gösterilen maç bağlamı raporlanabilir ama bu verilerle A/B/C, değer onayı
veya model terfisi yapılamaz. Bu deneyde puan ve maç haftasını eklemek
ayrı tutulan 2025/26 Şampiyonlar Ligi sezonunda gol tahminini kötüleştirdi.

B, C2, C3 ve M4'ün mevcut matematiği, 10 ligli otomatik haftalık veri hattı,
ana dal ve 100 maçlık pilot bundan etkilenmemiştir.

## Veri doğrulama ve kapsam

- Açık kaynak: openfootball/champions-league, sabit commit
  abfaeddc2ee3d14f99ecc163c9ddb46cb4d67cef.
- **2024/25 CL lig aşaması:** 144 tamamlanmış maç, 470 gol (3,264).
- **2024/25 EL lig aşaması:** 144 tamamlanmış maç, 408 gol (2,833).
- **2025/26 CL lig aşaması:** 144 tamamlanmış maç, 487 gol (3,382).
- Toplam: **432 maç**. 36 takım x 8 maç, 18 maç x 8 hafta,
  yinelenmeyen takım-maç kimliği ve gol toplamları kodda kontrol edildi.
- UEFA resmî toplam kanıtı:
  CL 2024/25 ve 2025/26:
  https://www.uefa.com/uefachampionsleague/news/02a2-1fd452956166-e9ccaec7d032-1000--league-phase-delivers-again-more-goals-more-competitiveness-/
  EL 2024/25:
  https://www.uefa.com/uefaeuropaleague/news/0295-1cf1a1ba73b4-c67c43530524-1000--uefa-europa-league-2024-25-league-phase-in-numbers/
- **Sınırlama:** Maç bazındaki 432 açık kaynak satırının her biri ayrı resmî
  UEFA maç sayfasıyla doğrulanmamıştır. UEFA toplamlarıyla eşleşme,
  maç bazlı %100 doğruluk sertifikası değildir. 2025/26 EL eksik olduğu
  için ayrı UEFA EL ileri sezon holdout iddiası yoktur.

## Maç haftasına göre gözlenen gol sayıları

| Turnuva/sezon | İlk 4 hafta, 72 maç | Son 4 hafta, 72 maç |
|---|---:|---:|
| CL 2024/25 | 3,069 gol/maç | 3,458 gol/maç |
| CL 2025/26 | 3,417 gol/maç | 3,347 gol/maç |
| EL 2024/25 | 2,778 gol/maç | 2,889 gol/maç |

Birinci ve ikinci CL sezonunun son haftalara göre farkı aynı yönde
değil. **Her Avrupa maçı temkinli geçer / son haftalar daima daha açık
geçer** diye kural koymak desteklenmiyor. Tanımlayıcı ilişki nedensellik değildir.

## Önceden sabitlenen üç deneysel referans

- BASE_COMPETITION_ONLY: 2024/25 eğitiminde turnuva genel gol oranı.
- STRENGTH_PROXY: BASE + yalnız önceki UEFA maç haftalarından
  iki takımın puan/averaj farkı ve geçmiş toplam gol oranı.
- STRENGTH_PLUS_POINTS_PHASE: STRENGTH_PROXY + maç haftası,
  son haftalar (6–8), puan farkı ve düşük puanlı tarafın UEFA PPG'si.

Bu deneyler, B/C2/C3/M4 motorlarına **yerine geçen yeni kabul edilmiş
modeller** değildir. Ülkeler arası takım güçlerini yerel lig güç
dereceleriyle kalibre etmiş gerçek bir rakip güç motoru da değildir.
Veri sadece maçtan ÖNCEKİ UEFA maç haftalarından kullanıldı; aynı
hafta veya sonraki gol/puan/averaj girdi olarak kullanılamaz.

**Geliştirme 2024/25 CL+EL (288); tek mühürlü dış değerlendirme 2025/26
CL (144).** Katsayılar / cezalar 2025/26 sonuçlarına göre yeniden seçilmedi.

### Dış sezon sonuçları — 2025/26 CL, 144 maç

| Referans | Poisson log-loss (düşük iyi) | 2,5 Üst Brier (düşük iyi) | Gol MAE (düşük iyi) |
|---|---:|---:|---:|
| BASE | **2,03157** | **0,22340** | **1,50436** |
| STRENGTH_PROXY | 2,05647 | 0,22937 | 1,53582 |
| STRENGTH_PLUS_POINTS_PHASE | 2,06198 | 0,23023 | 1,54213 |

Puan/hafta içeren son referansın maç başına Poisson log-loss farkı,
BASE'e göre **+0,03041** (kötüleşme). 8 maç haftasını blok alan
1200 yeniden örneklemeli yaklaşık %95 fark aralığı
**[+0,00835, +0,05600]**. Rakip vekili referansın farkı
**+0,02489**, aynı yöntemle yaklaşık **[+0,00665,+0,04243]**.
Yalnız sekiz maç haftası ve tek ileri sezon kullanıldığı için
bunlar farklı sezonlarda genellenen kesinlik aralıkları değildir.

Ortalama tahmin golü BASE için 3,259, STRENGTH_PROXY 3,294,
puan/hafta eklenen referans için 3,284; gerçek 3,382.

## Ne test EDİLMEDİ ve bundan sonraki kanıt eşiği

Bu çalışma (a) gerçek aynı-an maç kadrosunu, (b) rakibin gerçek
ülkeler arası Elo/UEFA katsayısını, (c) son hafta puan ihtiyaçlarının
resmî UEFA maç öncesi tüm diğer rakip ve senaryolara göre gerçek
kalifikasyon olasılığını, (d) eleme rövanşında toplam skor ve maç
durumu değişimini, (e) 2025/26 Europa League'in bağımsız sezon
verisini **test etmedi**. Mevcut veriye bakarak pozitif sonuca çıkacak
yeni katsayı ayarı veya test tekrarı yapılmayacak.

Sonraki çalışma ancak doğrulanmış yeni sezon/UEFA karşılaşma ve
gerçek pre-match puan durumu verisi elde edildiğinde yapılmalı;
aksi halde şimdi yeni model kurup kullanıcıya kayıt açtırmak doğru değil.

## Tek yürütme kanıtı

GitHub Actions: 41448740679
https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41448740679

GitHub Actions artefakt: 263-uefa-context-study-432-historical-experiment
(ayrı JSON kanıtı; GitHub artefaktları süreyle sona erer).

Güvenlik: EXPERIMENTAL_HISTORICAL_ONLY, no production promotion,
no odds, no A/B/C, no pilot ledger. 100 maçlık kayıt 0/100.
