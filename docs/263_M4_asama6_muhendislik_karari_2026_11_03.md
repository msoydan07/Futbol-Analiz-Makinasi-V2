# M4 GELİŞTİRME — AŞAMA 6 / TEK MÜHENDİSLİK KARAR RAPORU
**Tarih:** 3 Kasım 2026 · **Karar:** ARAŞTIRMA KAPANDI / MODEL TERFİSİ YOK / BAĞIMSIZ İLERİ DOĞRULAMA BEKLEMEDE

## Ana soru ve yanıt
M4'e daha eski sezon, zaman ağırlığı, iç/dış saha etkisi veya xG eklemek C3'e göre güvenilir tahmin iyileşmesi gösterdi mi? **Şimdiye kadarki kanıtla hayır.** M4'ü kötü model olarak kesin ilan etmek de mümkün değil. 2026/27 maçları görülmüş geliştirme verisidir, yeni bağımsız test değildir.

## Altı aşamanın kesin durumu
| Aşama | Kanıt | Karar |
|---|---|---|
| 1 — 2024/25 kaynak | 10 ligde 3.576 sonuç, kaynak / playoff ayrımı | Kabul |
| 2 — izole tarihsel havuz | 3.498 normal, 78 playoff; eski 4.413 korunur | Kabul; üretime ekleme yok |
| 3 — hata profili | C3/M4 ortak 873, geçmişi olmayan takım profili | Kabul; nedensellik kanıtı değil |
| 4 — toplu 10 kol | 873 ortak maç; 7/7 regresyon kapısı | Kabul; aday terfisi yok |
| 5 — gerçek xG | 2.155 kayıt; 289 tarihsel xG uygunluk adayı, 0/289 kanıtlı geçmiş xG-vintage | As-of kapısı BLOKE; ayrı ileri snapshot araştırması |
| 6 — mühendislik seçimi | Bu rapor, mevcut önkayıtlı B/C2/C3/M4 pilotu | Yeni model terfisi RED; ileri test BEKLEMEDE |

## C3 ve kilitli M4: *aynı* 873 daha önce görülmüş maç
| Ölçüt | C3 | M4 | Tercih / yorum |
|---|---:|---:|---|
| 1X2 doğru / toplam | 450/873 (%51,55) | 449/873 (%51,43) | C3 sayısal olarak önde; fark küçük |
| 1X2 log-loss (düşük iyi) | 0,997131 | 0,999336 | C3 sayısal olarak önde |
| Çok sınıflı Brier (düşük iyi) | 0,594649 | 0,595900 | C3 sayısal olarak önde |
| KG log-loss | 0,682632 | 0,685210 | C3 sayısal olarak önde |
| 2,5 Alt/Üst log-loss | 0,685175 | 0,690650 | C3 sayısal olarak önde |
| 1,5 ve 3,5 gol için eş kapsamlı ölçüt | Bu kapanış raporunda doğrulanmış değer yok | Aynı | **Ölçülmüş gibi iddia etme** |

C3−M4 1X2 log-loss farkı **−0,002205**; tarih bloklu %95 bootstrap aralığı **[−0,00663; +0,00205]**, sıfırı kapsıyor. Küçük yön farkı istatistiksel üstünlük kanıtı değildir. Kapsam yalnız eşleşmiş 873'tür; 880 toplamı veya 1.549 xG Poisson maçıyla karıştırma.

## Aşama 4'ün kontrollü denemeleri
- **Takıma özel saha etkisi (F001):** C3 log-loss 0,99713 → 0,99685; isabet %51,55 → %52,12. Farkın tarih-blok güven aralığı sıfırı içeriyor; KG ve 2,5 pazarlarında bozulma var. **TERFİ YOK.**
- **C3 + 2024/25 sezonu (F100):** 1,00004 log-loss. C3'ün 0,99713 seviyesinden kötü.
- **Kilitli M4 + 2024/25 (L100):** 1,00247 log-loss. M4 0,99934 seviyesinden kötü. Yeni gelen / önceki sezonda kendi lig geçmişi bulunmayan 268 maçta daha belirgin kötüleşme gözlendi; bu alt grup keşifseldir.
- 2025/26 gelişim aşamasında daha eski veri fayda sağlamış görünürken 2026/27 görülen değerlendirmede yön değiştirdi. **Her yeni sezon otomatik geçmiş ekle veya ağırlığı artır kararı yok.**

## Aşama 5 xG — doğru ve yanlış iddiaları ayır
- 2.155 xG kaydının **maç kimliği ve skor eşleşmesi** yapıldı; bu xG'nin maç öncesinde hangi sürümünün var olduğunu kanıtlamaz.
- Önceki 1.549 maçlık gol-Poisson vs xG-Poisson karşılaştırmasında xG lehine ortalama 1X2 log-loss farkı 0,003576; blok %95 belirsizlik aralığı **[−0,006465; +0,013838]**. 2026/27 290 maçta xG kötüleşti. **Bu doğrudan M4+xG testi değildir** ve geçmiş xG-vintage belirsizliği taşır.
- 873 C3/M4 maçından 289'u iki takıma da ≥5 geçmiş iç/dış saha xG içeriyor; ama 289 maç için **0 kanıtlı bağımsız geçmiş sağlayıcı sürümü** var. Bu, verinin gerçekte geçmişte bulunmadığı anlamına gelmez; kesin ileri koşullarda geçmiş test iddiası bloke demektir.
- Yeni özel snapshot kodu ve 11 sentetik güvenlik testi hazır, fakat gerçek veri edinme/izin incelemesi ve **haricen doğrulanmış** zaman damgası henüz tamam değil. xG matematik modeline otomatik entegre edilmez; public GitHub'a ham veri yeniden yüklenmez.
- Eskiden `understat-xg-pilot` Actions artifact'inde ham CSV yayımlanmış; erişim ve yeniden dağıtım koşulları ayrıca giderilmelidir. Sorun bu raporla otomatik çözülmez.

## Ön kayıtlı 100 maçlık ileri pilot — bundan sonraki doğru deney
1. Kullanıcının adını verdiği, **gerçekten gelecekte** oynanacak kapsam içi *yerel lig* maçları resmî kaynaktan doğrulanır.
2. B, C2, C3 ve M4 **aynı maç önü veri kesimi** üzerinde ayrı ve tek seferlik hesaplanır; uygun olmayan model `UNAVAILABLE` yazabilir. Tahmin dosyası kickoff **öncesi Git commit ve hash** ile mühürlenir; maç sonunda değiştirilmez.
3. **25 maçta** yalnız dosya bütünlüğü, erişilebilir veri ve operasyonel hatalar kontrol edilir. *Hiçbir model yeniden ayarlanmaz.*
4. **100 maçta** önkayıtlı tek nihai değerlendirme: aynı maç 1X2 isabet, log-loss, Brier, KG ve 2,5 Alt/Üst, lig/kalibrasyon ve tarih bloklu güven aralıkları. Ek 1,5/3,5 ancak aynı kayıt verisi varsa ayrıca raporlanır.
5. M4 ancak bağımsız yeni maçlarda, yeterli ortak kapsamada tutarlı ve anlamlı kazanç gösterirse değerlendirilir. 100 maç dahi belirsizse daha çok **yeni** kayıt; eski maçlarda hiperparametre avcılığı değil. Oran ve EV ayrıca doğrulanmadan bahis değeri iddiası yok.
6. UEFA için 3 Kasım akşamı mühürlenmiş M0/M0+Elo gölge kayıtları **AYRI** araştırmadır; yerel B/C2/C3/M4 100 maç sayacına yazılmaz.

## Dondurulmuş karar / yapılmayacaklar
- **C3 ve M4 aynı kalır;** C3'ün geçmişteki küçük avantajını kesin gelecek üstünlük diye sunma.
- F001, L100, xG kolu, kendi Elo veya diğer deneysel yardımcılar canlı üretime entegre edilmez.
- Yeni sezon, rakip gücü, saha etkisi ve geçmiş veri için ikinci-üçüncü test döngüsü başlatılmaz.
- 2026/27 retrospektif test verisinin görülmüş olması gizlenmez; bağımsız final diye pazarlanmaz.
- İlk 11 olmayınca maç analizi otomatik durmaz; açıklanmamış 11 uydurulmaz.
- 100 maç pilotu yeni maçlar gelene kadar ilerlemez; **sıradaki değerli iş kanıtlı ileri kayıtların birikmesidir**.

## Dayanaklar
- [Aşama 3 tek hata profili](263_M4_asama3_880_eslesmis_hata_raporu_2026_11_03.md)
- [Aşama 4 tek toplu test sonucu](263_M4_asama4_tek_toplu_karsilastirma_sonuc_2026_11_03.md)
- [Aşama 5 873/xG kesişimi](263_M4_asama5_873_xg_kesisim_kabul_2026_11_03.md)
- [Aşama 5 xG as-of/lisans kapısı](263_M4_asama5_xg_asof_lisans_kabul_2026_11_03.md)
- [Gelecek xG snapshot katmanı](263_M4_asama5_gelecek_xg_ozel_snapshot_2026_11_03.md)
- [B/C2/C3/M4 önkayıt pilot sözleşmesi](../experiments/263/M4_PILOT_PROTOCOL.md)

**HÜKÜM:** Altı aşamalı araştırma planının mevcut kanıta dayalı mühendislik kararı tamamlandı. Model performansının gerçek gelecekteki nihai hükmü **BEKLEMEDE**. Bu noktadan sonra yeni geçmiş model denemesi **yok**.
