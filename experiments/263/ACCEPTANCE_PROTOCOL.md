# 2.6.3 — tek toplu tarihsel matematik kabul testi (önceden kilitlenen protokol)

**Aşama**: matematik motoru, gerçek maç/sonuç defteri değil. `main` ve `feature/01-kimlikler` **DEĞİŞMEYECEK**.

## Dondurulan girdiler

- Dondurulmuş tarihsel kabul verisi: 4.413 maç, 10 lig, SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- Eski 1X2 kanıtı: `predictions_263.csv`, SHA-256 `e41f9fc3dd80d00714e015304ba3beb1e69f309abea5bc71ce8c71f462efdbbf`. Yalnız **C0/C1/C3** 1X2 çıktıları kullanılır; eski C2'nin 30 lig maçı kuralı varken üretilen çıktısı bu deneyde kullanılmaz.
- Dönem: 2025/26 geçmişi + o güne kadar 2026/27. Değerlendirme yalnız 2026/27. Bu dönem başka deneylerde incelendiğinden **dokunulmamış son test değildir**.
- Tarih sızıntısı: `match_date < maç günü`, gün içindeki tüm diğer sonuçlar da yasak.

## Hesaplanacak yeni adaylar

- **C2 (kanonik)**: `k=5,w=0.5, min_context=4`, yalnız 2026/27 lig referansı, önceki sezon yalnız `ρ` ön bilgisi. Şablonda olmayan 30 cari lig maçı kuralı YOK.
- **FT gol çizgileri ve KG**: yalnız C2'nin ortak bağımsız Poisson skor matrisinden. C2 vs o günün öncesindeki aynı lig olasılık frekansı (`Laplace +1`): FT 1.5, 2.5, 3.5 Üst ve KG Var.
- **İlk yarı**: ayrı Ridge-Poisson sayım modeli, geçmişte 40 lig gözlemi ve ilgili 4 ev/deplasman maçı. Karşısı aynı lig zaman-kesimli frekans baseline. Pazarlar İY 1X2, 0.5 / 1.5 / 2.5 Üst.
- **Korner (maç sonu)**: ayrı Ridge sayım + tarihsel aşırı saçılma NB; geçmiş 40 lig gözlemi ve ilgili 4 ev/deplasman maçı. Lig öncesi frekans referansı; 7.5/8.5/9.5/10.5 Üst.
- Şut, xG, Elo, Dixon–Coles, 1Y korner ve 0.Modül — GİRMEZ. Önceki başarısız testler yeniden çalıştırılmaz.

## Adil karşılaştırma, karar

- 1X2 **aynı maç altkümesi** ile C2/C0, C2/C1, C2/C3; C3/C1 yalnız eski kanıtı tekrar ÖLÇMEK için, yeniden model fit'i YOK.
- Diğer pazarlar aday ve kendi lig referansının **ikisi de mevcut** aynı maçlarda değerlendirilecek. Başarısız veri kalemi pazara özel karantinaya alınacak.
- Çok-sınıflı Brier = 3 sınıf karesel hata toplamı, ikili Brier ayrı ölçekte. Log loss p `[0.001,0.999]` sınırı **şablon 2.6.3 kuralı**; mevcut geçmiş raporların logloss'u bundan dolayı birebir aynı olmak zorunda değil.
- Minimum 150 ortak maç, log loss en az +0.005, Brier kötüleşmesin, gün bazlı 750 örnek bootstrap %95 aralık alt sınırı >0: yalnız **retrospektif sinyal**; hiçbir koşul otomatik canlı model terfisi değildir.
- Her pazarda lig kırılımı, kapsam, karantina, %95 gün bootstrap ve 5 bölmeli ikili güvenilirlik tablosu. Tek maçın farklı pazarları bağımsız gözlem olarak sayılmaz.

**Bir defa çalıştırma:** Önce sentetik yazılım kapıları, sonra aynı dondurulmuş veride yalnız yeni adayların tarihi karşılaştırması. Sonuca bakıp katsayı değiştirme ve test tekrarına girme yok. Her durumda bir JSON raporu + tarih kesimi denetim CSV + kısa karar notu.
