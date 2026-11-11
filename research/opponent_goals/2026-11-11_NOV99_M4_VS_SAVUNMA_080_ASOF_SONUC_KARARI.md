# Futbol 2.6.3 — 4, 6, 7 ve 8 Kasım 2026: 99 sonuçta M4 vs %80 simetrik rakip savunması

**Tarih:** 11 Kasım 2026. **Kapsam:** Kullanıcının talebiyle bir defaya mahsus, daha önceden tamamlanıp arşivlenmiş 99 maçta as-of retrotest. **Mühürlü maç önü tahmini DEĞİL.**

## Mühendislik kararı

Önceden 2025/26 geliştirme döneminde seçilen tek aday **her iki takımın rakip savunma katkısını %80'e yumuşatmak**; rakip gücünü kaldırmıyor. 99/99 maça orijinal dondurulmuş M4 ve tek %80 aday uygulandı. **KG Var/Yok ve 2.5 Alt/Üst biraz iyileşti; MS 1/X/2 kötüleşti.** Henüz üretime entegrasyon için yeterli değil. **M4 ana matematiği ve kullanıcıya gösterilen yüzdeler KORUNDU.**

## Toplam 99 maçta doğruluk (birincil bilimsel ölçü Brier; top-1 ayrı açıklayıcı metrik)

| Pazar | M4 Brier | %80 Brier | Yeni − Eski Brier | M4 doğru | %80 doğru |
|---|---:|---:|---:|---:|---:|
| KG Var/Yok | 0,236732 | 0,236185 | **−0,000547** | 53/99 | **55/99** |
| 2.5 Alt/Üst | 0,249015 | 0,245631 | **−0,003384** | 52/99 | **55/99** |
| MS 1/X/2 | **0,541791** | 0,547414 | **+0,005623** | **60/99** | 57/99 |

Logloss ek çapraz kontrol: KG **0,665477 → 0,664260**; 2.5 Alt/Üst **0,690588 → 0,682958**; MS **0,921987 → 0,930510**. Brier farkı negatifse aday daha iyi; bu metrikler bahis kârını ya da başarı garantisini ölçmüyor. Her iki yöntem **aynı, tarih kesiti öncesi bilinen veriden** yeniden hesaplandı.

## Günlere göre Brier değişimi (aday − M4; negatif daha iyi)

| Tarih | Maç | KG Δ | 2.5 Alt/Üst Δ | MS Δ |
|---|---:|---:|---:|---:|
| 04.11.2026 | 4 | +0,004982 | +0,008422 | −0,002085 |
| 06.11.2026 | 10 | +0,004820 | +0,000071 | +0,008309 |
| 07.11.2026 | 43 | +0,001042 | −0,002851 | +0,005904 |
| 08.11.2026 | 42 | −0,003977 | −0,005878 | +0,005430 |

**Dikkat:** KG'deki toplam kazanç ağırlıkla 8 Kasım'dan geliyor; **4 takvim gününün yalnız birinde** KG Brier iyileşti. 2.5 Alt/Üst ise 7–8 Kasım'da iyileşti. MS, 4 Kasım dışında kötüleşti. Bu, **genel geçer üstünlük** iddiasını güçlendirmez.

## Lig bazında Brier farkları

| Lig | Maç | KG Δ | 2.5 Alt/Üst Δ | MS Δ |
|---|---:|---:|---:|---:|
| ENG1 | 10 | +0,005246 | +0,006597 | +0,008661 |
| ENG2 | 15 | +0,001518 | −0,001280 | −0,001196 |
| GER1 | 9 | −0,004973 | −0,002683 | +0,010043 |
| ESP1 | 10 | +0,001439 | −0,001605 | −0,006659 |
| ITA1 | 10 | −0,001349 | +0,000729 | +0,008621 |
| FRA1 | 9 | +0,001528 | −0,006537 | +0,001709 |
| NED1 | 9 | −0,006375 | −0,020843 | +0,001369 |
| TUR1 | 9 | +0,000535 | −0,002835 | +0,013627 |
| POR1 | 8 | −0,007364 | −0,015176 | +0,006580 |
| BEL1 | 10 | +0,001225 | +0,004443 | +0,017502 |

**KG 4/10 ligde, 2.5 Alt/Üst 7/10 ligde, MS 2/10 ligde** Brier iyileşti. Lig başına 8–15 maç var, lig özel düzeltme ya da seçerek başarı ilan etmek savunulamaz.

## Geriye dönük as-of hesap nasıl yapıldı?

1. SHA256 ile önceki 4.518 satır, yeni 4.617 sonuç CSV'si ve dondurulmuş M4 kodu doğrulandı. Arşivdeki ayrı 99 JSON kayıt Git blob SHA ile sabitlendi.
2. 99 kayıt, arşiv CSV'sine yalnız **lig + tarih + her iki takımın sabit ID'si** üzerinden benzersiz eşlendi; tüm skorlar aynı bulundu. Normal süresi tamamlanmamış bir maç eğitimden çıkarıldı.
3. **31 lig×gün** M4 fit'i; her biri ilgili maç gününden **kesinlikle önce** oynanan sonuçlarla. 99 maçın o günkü veya daha geç sonuçları ilgili fit'e alınmadı; geçmiş tarihte oynanan 99 maç sonraki günlerin fit'inde kullanılabilir. Bu günlük yeniden eğitim, geriye dönük as-of ilkesiyle uyumlu, ancak canlı öncesi mühürlü eski M4 ile *aynı şey değil*.
4. M4'ün 2025/26 geliştirme döneminde kilitlenen **half-life=360, ridge_shared=4, ridge_venue=48** parametrelerine dokunulmadı. Tek aday %80 **önceden** 2025/26 deneyiyle seçilmişti; bu 99 sonuçla yeniden ağırlık aranmadı.
5. **99/99** maç hesaplanabildi, **0** kimliği bulunmayan takım, **0** güvenli aralık dışı sonuç, aynı maçların KG/Alt-Üst/MS Brier ve logloss değerleri eşleştirildi.
6. Sonuç kaynakları karışık: **28** birincil sayfa ve sağlayıcıyla uyumlu, **28** doğrudan lig/kulüp skor sayfası, **43** ikincil kaynak ve kısmi resmî kontrol. **Bağımsız resmî sağlayıcı maç ID doğrulaması yok.**
7. Test maçları sonuçlandığından, burada **gerçek zamanlı maç öncesi SHA mühürleri yok**. Bu 99 maç için sonradan oluşturulan sonuçlar *asla mühürlü pilot* sayılmaz.
8. Toplam **yalnız dört farklı gün** olduğundan kümelenmiş örneklem için güvenilir bağımsız gün bootstrap belirsizlik aralığı vermiyoruz. Ayrıca 99 sonuç şimdi bir kez incelendiği için bunları gelecekte yeni katsayı optimize edip yine kör testmiş gibi kullanmak yanlış olur.

## Karar

- **%80 simetrik savunma adayını** yalnız araştırma olarak koru; KG/2.5 Alt/Üst kazancı çok küçük ve gün/liglerde dengesiz; MS'nin Brier ve top-1 doğruluğu kötüleşiyor. **Üretime alma.**
- 99 maçlık bu geriye dönük karşılaştırmayı **tamamlanmış tek çalışma** olarak kapat. Yeni oran, gelişim katsayısı, lig-özel optimizasyon, post-hoc yeniden deneme veya yeni pilot açma.
- Artık **gerçekten yeni günlerde, maçtan önce SHA ile kilitlenen** M4 ve sabit aday yan yana toplanırsa, gelecekte yalnız yeni sonuçlarla gelişme test edilebilir.
- Ana GitHub `experiment/263-toplu-karsilastirma` dalı, M4 motoru, eski tahmin SHA'ları, skorlu 99 arşiv, telefon ekranı ve bahis hesapları **DEĞİŞMEDİ**.

## Denetlenebilir kanıt

- [GitHub Actions — 99/99 aynı maç, 31 as-of fit, 6/6 test yeşil](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42982622449)
- [Tek çalıştırmada as-of 99 karşılaştırma kodu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-nov99-defence-080-asof-backtest-20261111/research/opponent_goals/nov99_opponent_defence_080_asof_backtest_263.py)
- Actions artifact `263-99-nov4to8-2026-asof-m4-vs-defence080-retrospective-only`: tam **99 maçın iki ayrı olasılık tablosu, Brier/Logloss ve galip tahminleri**, lig/gün özetleri.

**Sonuç:** Eski sonuçlar adayın KG ve 2.5 Alt/Üst için dikkat çekici bir fikir olduğunu desteklese de MS'yi zayıflattığını ve kazancın kararsız olduğunu ortaya koydu; değişmeyen ana makine şu an doğru karar.
