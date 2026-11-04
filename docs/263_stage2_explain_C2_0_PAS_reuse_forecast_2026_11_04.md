# 2.6.3 — T2'nin %100 PAS nedeni ve tekrar çalıştırmadan alternatif deney

İlk toplu 880 as-of model/gol/KG deneyi [run 41836437930](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41836437930) **BAŞARILI**. Ağustos–Eylül 587 / Ekim 293. Gerçek tespit:
- Sıkı C2 T0: 89/293 aday, 204 PAS, seçimin 68'i 1,5 Üst, 21'i 3,5 Alt. Seçilmiş olay Brier'i 0.209055, aynı olay lig bazı 0.191152 (**daha kötü**).
- Esnek C2 T1: 105/293 aday, 188 PAS, 80'i 1,5 Üst, 25'i 3,5 Alt. Brier 0.191618, aynı olay bazı 0.175925 (**daha kötü**).
- Kalibrasyonlu T2: 0/293 aday, 293 PAS. Bunun nedeni kalibrasyon eşiği değil, **Ağustos–Eylül C2 veri kapsamı = 0**. Ekimde bile 105 C2 mevcut ve 188 yok.
- Test değerlendirmesinde model kapsamları B 212/293, C2 105/293, C3 293/293, M4 293/293.

## İkinci aşama kararı (ayrı algoritma teşhisi)

**880 tarihi tahmini tekrar çalıştırma.** İlk job'ın SHA ve as-of etiketli CSV'sini indir; yalnız aynı dosyadaki M4/C3 erken sezon tam kapsama ile DEV (587) market-bazlı shrinkage öğrenip Ekim (293) risk–coverage değerlendirmesi yap. İki sürüm: basit eşiğe göre seçim; ve ek DEV Brier skill >0 şartı. Sadece tanı, C2 yerine otomatik deneysel model geçirme yok.

Bu deney 1,5 Üst'ün yüksek yüzde ile tekelleşmesini, ne zaman 2,5 Üst'ün kendi bazına göre güçlü olduğunu, modelin bazın ötesine bilgi üretip üretmediğini ölçer. Tek başına PAS'ı düşürmek başarı değildir.

2026/27 Ekim sonuçları daha önce de incelendiğinden bağımsız gizli test değil. Modeller, orijinal C2, S1/S2, main ve ileri pilot değişmez. Tarihli gerçek bahis fiyatı olmadığı için EV/ROI yok.