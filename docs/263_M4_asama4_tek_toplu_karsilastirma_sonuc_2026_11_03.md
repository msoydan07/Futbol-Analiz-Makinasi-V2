# M4 aşama 4 — 10 kollu tek toplu ablasyon SONUCU
**3 Kasım 2026 · SONUÇ: RETROSPECTIVE_RESEARCH_ONLY · MODEL TERFİSİ YOK**

## Kaynak ve yöntem
- **Dondurulmuş 4.413 maç:** SHA256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`. GitHub Actions kaynak `41251343847`.
- **2024/25 ek havuzu:** 3.576 maç. Birincil deneyde 3.498 normal lig maçı, 78 play-off/final maçı ayrı duyarlılık analizi. Git blob `26aaa482fedfa8aee3ca147878332e41cbeb4f46`.
- Orijinal matematik kodları: `experiments/263/exp_263_batch.py` (C3 Ridge=6, Git blob `ad0c620080aa98fd3ab339535f0f2824b823e586`) ve `experiments/263/m4_integrated.py` (M4 sabit 360 gün/4/48, Git blob `645d907e8f5f38faaed4763ca557802cea766bc4`).
- Veriler ve kod GitHub'daki [tek salt-kaynak dışa aktarma işlemi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41691600044) ile aynı sabit sürümden alındı (SUCCESS). Bu Actions **model çalıştırmadı**.
- Toplu on kol **tek defa** orijinal modeller ithal edilerek offline çalıştırıldı; Python kodu, çalışma girdileri, tam eşleşmiş maç CSV'si ve JSON sonuçları bu sohbetteki indirilebilir ZIP'te paketlendi. Kaynak kod burada GitHub dosyası olarak henüz yer almıyor; bu belge yalnız sonucu kaydeder.
- Kesim her maçta `tarih < hedef maç tarihi`. 2025/26 geliştirme hedefi **2.389**, eski 2026/27 değerlendirme hedefi **880**; aynı **873** maçta on kol birden tahmin verdi.
- Eski testle **7/7 regresyon eşitlik kontrolü BAŞARILI:** C3 873, M4 880, ortak 873, C3 log-loss 0,9971; M4 tüm 880 log-loss 1,0012, ortak M4 log-loss 0,9993.

## Ana sonuç — aynı 873 eski 2026/27 maçı
**Düşük log-loss/Brier daha iyi.** F kodlarında 1. basamak 2024 geçmişi, 2. zaman ağırlığı, 3. takıma özel saha; Ridge=6. L000 eski M4, L100 eski M4+2024, Ridge=4.

| Kol | 1X2 log-loss | 1X2 isabet | KG log-loss | 2.5 log-loss | C3'e karşı tarih-blok %95 |
|---|---:|---:|---:|---:|---|
| **F000 (C3)** | 0,99713 | 450/873 = %51,55 | 0,68263 | 0,68518 | referans |
| F100 (+2024) | 1,00004 | 451/873 = %51,66 | 0,68954 | 0,68496 | [−0,01199; +0,00748] |
| F010 (+360g) | 0,99795 | 445/873 = %50,97 | 0,68271 | 0,68482 | [−0,00301; +0,00156] |
| F110 (+2024+360g) | 0,99894 | 446/873 = %51,09 | 0,68718 | 0,68458 | [−0,00813; +0,00527] |
| **F001 (+takım-saha)** | **0,99685** | **455/873 = %52,12** | 0,68411 | 0,68751 | **[−0,00294; +0,00365]** |
| F101 (+2024+saha) | 1,00101 | 450/873 = %51,55 | 0,69040 | 0,68658 | [−0,01271; +0,00587] |
| F011 (+360g+saha) | 0,99821 | 452/873 = %51,78 | 0,68419 | 0,68789 | [−0,00505; +0,00261] |
| F111 (tüm üç faktör) | 1,00016 | 444/873 = %50,86 | 0,68844 | 0,68757 | [−0,01016; +0,00467] |
| **L000 (kilitli M4)** | 0,99934 | 449/873 = %51,43 | 0,68521 | 0,69065 | [−0,00663; +0,00205] |
| L100 (M4+2024) | 1,00247 | 444/873 = %50,86 | 0,68967 | 0,68982 | [−0,01301; +0,00277] |

**C3'ten numerik olarak en düşük 1X2 log-loss F001'de (−0,00028), fakat farkın %95 aralığı sıfırı içeriyor.** F001'in KG/2.5 hata metriği C3'ten daha kötü; **güvenilir, pazarlar arası iyileşme gösterilemedi**. F001 terfi ettirilmez.

## 2025/26 gelişim ile 2026/27 arasındaki fark
- 2025/26'da **10 modelin tamamının** tahmin ürettiği 2.367 ortak maçta: C3 **1,02161**, C3+2024 (F100) **1,01543**; C3+2024+360 gün (F110) **1,01335**; M4 **1,02614**, M4+2024 (L100) **1,01750** log-loss.
- Buna karşılık eski 2026/27'de: C3 **0,99713**, F100 **1,00004**; M4 **0,99934**, L100 **1,00247**. Yani fazla geçmişin katkısı **döneme göre yön değiştiriyor.**
- **Nedensellik kanıtlanmadı:** Bu fark mevsim geçişi, eski takım gücünün değişmesi, kaynak/lig dengesi ve model düzenlileştirmesi ile bağlantılı olabilir. Sadece gözlem yapıldı, ayar değiştirilmedi.

## 2026/27 yeni takım ayrıştırması (ortak 873)
- En az bir takımın 2025/26 aynı lig geçmişi yok: **268 maç**, C3 1,02891; M4 1,03771; M4+2024 1,05307.
- İki takımın da 2025/26 aynı lig geçmişi var: **605 maç**, C3 0,98305; M4 0,98234; M4+2024 0,98005.
- **Yorum (keşifsel):** Eski geçmişi modele herkese aynı şekilde eklemek, özellikle lige yeni gelen takımların maçlarında olumsuz görünüyor. Ayrım nedensel test değildir; 2026/27 görüldükten sonra gruplar seçilmiştir.
- 2024/25'teki 78 play-off maçını eklemek: F111 log-loss 1,00184 → 1,00264; L100 1,00466 → 1,00549 (880 kendi kapsamı). Çok küçük ve kötü yönde fark; play-off'lar zorunlu ana geçmişe katılmayacak.

## Net mühendislik kararı
1. **Yeni 2024/25 verisini mevcut M4'ün eğitimine otomatik ekleme.** Daha fazla veri otomatik olarak daha isabetli tahmin üretmedi.
2. **Mevcut C3 ve kilitli M4 değişmez.** F001'in çok küçük avantajı belirsiz ve KG/2.5 pazarlarında kötüleşme var; yeni aday terfi etmez.
3. Bir sonraki deney hipotezi: *takımın yeni/yerleşik oluşunu ve yakın dönemdeki veri güvenini dikkate alan geçmiş aktarımı*; bu eski 2026/27 sonuçlarına bakılarak sayısal ağırlık seçilmemeli.
4. xG ayrı 5. aşamada ve yalnız gerçek doğrulanmış veri olan maçlarda sınanır. Gol tahmin modellerinin hatası xG olmadan bütünüyle açıklanamaz.
5. Bütün bu veriler daha önce görülmüş tarihlerdir. **Bağımsız nihai doğrulama için yeni ve başlama öncesinde kayıt altına alınmış maçlar şart.** Ana dal, canlı M0/C3/M4 ve Galatasaray–Stuttgart UEFA T−60 mühür kaydı değişmedi.

**Aşama 4 SONUÇLANDI; 5. aşama xG karşılaştırması henüz çalıştırılmadı.**
