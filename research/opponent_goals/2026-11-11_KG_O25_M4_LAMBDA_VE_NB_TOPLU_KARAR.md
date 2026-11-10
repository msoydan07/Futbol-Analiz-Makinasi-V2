# Futbol 2.6.3 — KG/2.5 Üst gol ortalaması vs dağılım testi ve mühendislik kararı
**11 Kasım 2026 · Salt araştırma · M4 ana matematik ve eski SHA tahminler değişmedi.**

## Hipotez
- H1: Bazı maçlarda beklenen toplam gol λ biraz düşük/ yüksek hesaplanıyor olabilir. M4 λ_ev ve λ_dep birlikte **×0,95 veya ×1,05** yapılarak *yalnız deney*.
- H2: Gol ortalamaları doğru ama ayrı ayrı Poisson'un sabit varyansı az kalıyor olabilir. M4 λ değişmeden bağımsız negatif binom marjinalleri `alpha=0,10` veya `alpha=0,25` ile *yalnız deney*.
- Daha önceki 984 maçlık Dixon–Coles/ortak gol şoku deneyleri **tekrarlanmadı**. Negatif binom, ortak gol şoku değildir; yalnız tek takım gol sayısının varyansını değiştirir.

## Kaynak ve metodoloji
- 4.617 sonuçluk değişmez dosya SHA kontrol edildi; **4.518 özgün maç değişmemiş, 99 yeni sonuç mevcuttur**.
- **2026/27 sonuçları (99 dahil) hiçbir şekilde model eğitiminde, hipotez ayarında veya ölçümde kullanılmadı.** Yalnız 2025/26 geliştirme sonuçları ve M4'ün önceden kilitli 360 gün/4/48 parametreleri.
- 10 ligde M4, 2025/26 **3 önceden mevcut tarih kesitinde** fit edildi; her fold için maçlar yalnız *kesit tarihinden önceki* sonuçlarla eğitildi; sonra sabit fit ile sonraki maçlarda performans ölçüldü.
- **701 aynı maç**, 30 lig×kesit fit; 1 maç tüm adaylar için ortak güvenli λ aralığı dışında tutuldu; 41 farklı maç günü.
- Her aday aynı **KG Var, 2,5 Üst ve MS Brier/logloss** üzerinde değerlendirildi. Brier için **aday eksi orijinal M4 negatifse daha iyi**. Tarih bazlı bootstrap belirsizliği raporlandı; eski geliştirme döneminde seçilmiş M4 kullanıldığı için bu bootstrap bağımsız ileri doğrulama değildir.
- [Gerçek GitHub toplu test — 6/6 PASS](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42909826085)
- [Tekrar çalıştırılabilir gerçek veri araştırması](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-goals-marginal-dispersion-20261111/research/opponent_goals/goal_distribution_challenger_263.py)

## M4 başlangıç durumu
| Metrik | Tahmin | Gerçekleşen |
|---|---:|---:|
| KG Var | %49,72 | %55,06 |
| 2,5 Üst | %50,28 | %54,21 |

Orijinal 701 maç Brier: **KG 0,254245; 2,5 Üst 0,257141; MS 0,600433**. Bu rakamlar *genel tahmin isabet yüzdesi değildir*; aynı döneme ait gelişim verisi tanımıdır. Toplam gol gerçekleşen eksi beklenen **+0,085 gol/maç**; toplam gol saçılım kalıntısı **+0,284**. Sabit yeniden ayar yapmak için tek başına yeterli değildir.

## Beş seçenek tek karşılaştırma
| Aday | Δ KG Brier | Δ 2,5 Üst Brier | Δ MS Brier | Karar |
|---|---:|---:|---:|---|
| Mevcut M4 | 0 | 0 | 0 | Korunacak referans |
| λ ×0,95 | +0,002926 | +0,002830 | −0,000196 | **Ret**: KG ve Üst kötü |
| λ ×1,05 | −0,001768 | −0,000959 | +0,000467 | **Sadece ileri araştırma adayı**, MS hafif kötü |
| Bağımsız NB α=0,10 | +0,002827 | −0,000376 | −0,000553 | **Ret**: KG kötü, Üst kazancı çok küçük |
| Bağımsız NB α=0,25 | +0,009164 | −0,000104 | −0,000396 | **Ret**: KG belirgin kötü |

### Gün bloklu keşifsel aralıklar — aday eksi orijinal M4
- λ ×1,05 KG Brier: **[−0,003647, +0,000096]**; 2,5 Üst: **[−0,003119, +0,001329]**; MS: **[−0,000118, +0,001129]**. Üç aralık da 0'ı kapsıyor.
- NB α=0,10 KG: **[+0,000646, +0,004970]**: bu örnekte KG kötüleşmesi sıfırdan ayrışıyor.
- NB α=0,25 KG: **[+0,004228, +0,014128]**: daha büyük kayıp.
- Bunlar nihai güven aralıkları veya üretim terfi eşiği değildir; 41 günün içindeki maçlar bağımsız tarihler gibi alınmamıştır.

## Karar
**Ana M4, B/C2/C3, MS, KG/Üst yüzdeleri, mevcut maç önü SHA mühürleri, 4.617 kaynak ve otomasyonlar DEĞİŞMEYECEK.** Herhangi bir yeni hesaplamayı üretime almak için henüz delil yok.

Bu tablo `lambda×1,05` seçeneğini **yalnızca 9 Kasım sonrası gerçek ve önceden mühürlü maçlarda**, **eski new100 maç sonrası izleyicisinin içinde** sabit karşılaştırma adayı yapmaya yeterli *araştırma hipotezi* verir. Yeni pilot açılmayacak, eski 6–8 Kasım tahminleri tekrar skora sokulmayacak, aday maç öncesi kullanıcı yüzdelerini değiştirmeyecek. Gerçek ileri sonuçları gelince KG ve 2,5 Üst'te tutarlı iyileşme ve MS güvenliği birlikte kontrol edilecek.

**Reddetme gerekçesi:** Gol varyansını tek başına artırmak KG Var için güçlü bir iyileştirme göstermedi. M4'teki beklenen gol yanlılığının devam edip etmediğini önce yeni ve bağımsız sonuçlarla öğrenmeliyiz; bugün otomatik düzeltme bilimsel olarak erken olur.
