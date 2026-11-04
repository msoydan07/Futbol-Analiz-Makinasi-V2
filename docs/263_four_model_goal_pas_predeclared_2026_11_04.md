# 2.6.3 ön kayıt — 4 motor, gol/KG ve PAS tek toplu tarihsel karşılaştırma

Dondurulmuş 4.413 maç dosyası (SHA doğrulanacak); 2026/27 Ağustos 259, Eylül 328, Ekim 293. Geçmiş tahminler maç gününden *önce* bilinen veriyle yeniden hesaplanacak; **o gün GitHub'da kilitlenmiş tahminmiş gibi sunulmayacak**. C2 kanonik ve diğer üç model sadece rakip ölçüm; eski hesaplamalar değişmez.

Her modelde MS1/X/2, 1.5/2.5/3.5 Alt-Üst ve KG Var/Yok ölçülecek. Maçların ilk iki ayı (587) kalibrasyon adaylarının gelişimi, Ekim (293) değerlendirme. Ekim önceden araştırıldığından bağımsız final kanıtı değildir.

Üç önceden tanımlanmış profil: T0 %75 + stress %70, T1 %70 + stress %65, T2 yalnız DEV ile as-of aynı pazar bazına shrinkage; %63 olasılık, +3 yp lig-baz sinyali, stress %58; baz farkı+0.1 p sıralaması. Bunlar canlı S1/S2 eşiklerine aktarılmayacak. Bağımsız ikinci seçenek ancak farklı market family; aynı maçta 1,5 Üst ile 2,5 Üst iki bağımsız bahis gibi gösterilmez.

**Ölçüler:** kaç maç ana/alternatif/PAS, 1,5 Üst/3,5 Alt yoğunluğu, seçilmiş olayın kendi eski lig bazına göre Brier farkı, 11 pazarda B/C2/C3/M4'nin aynı pazar Brier/log-loss, C2 veri kapsamı. Fiyat arşivi yok: EV, S2, ROI, bahis önerisi yok. Modellerin tercih yüzdesi, güven yüzdesi iddiası değildir. Tam test çıkışı tek artifact altında.