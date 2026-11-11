# M4 rakip savunmasının ağırlığı — 10 liglik kronolojik karşılaştırma
**11 Kasım 2026 | araştirma dalı: `research/263-away-defence-shrink-timeholdout-20261111`**

## Hedef ve yöntem

Önceki **702 maçlık geliştirme dönemi** araştırmasında M4'ün rakibin deplasman savunma gücünü biraz fazla keskin uygulayabileceği bulunmuştu. Aynı dönemde ağırlık seçip tekrar aynı maçlarda başarı ölçmek yerine, önceki üç geliştirme ölçüm diliminin **bitişinden sonraki**, kesişmeyen tarih dönemini kullandık:

- **Tek eğitim anı:** `2026-04-06`; M4, 2025/26 sezonundan yalnız bu tarihten **önceki** maçlarla, lig başına bir kez fit edildi.
- **Değerlendirme dönemi:** **6 Nisan–31 Mayıs 2026**, 10 ligde **635 farklı maç**, **42 farklı maç günü**. Önceki 702 araştırma maçıyla **sıfır tarih çakışması**.
- **Üç önceden tanımlı seçenek:** Deplasman savunma katsayısının M4 ev gol beklentisine etkisi mevcutta **1,00**, adaylarda **0,75** ve **0,50**. Alternatifler takım savunmasının eğitim dönemindeki lig katsayısı ortalaması etrafına yaklaştırılmasıyla uygulandı. **Deplasman beklenen golü ve diğer katsayılar değişmedi.**
- **Aynı maçların MS/KG/2.5 Üst Brier ve logloss** sonuçları karşılaştırıldı; yalnızca 90 dakikalık geçerli maçlar, zaman kesiti sonrası.
- **2026/27 sonuçları, 99 sonuçluk tamamlanmış arşiv, eski mühürlü 96 pilot, 984 Dixon–Coles deneyi analiz veya aday seçimi için kullanılmadı.**
- Daha sonraki bu dönem, söz konusu 702 maçtan **kronolojik olarak ayrıdır**; fakat aynı 2025/26 sezonundandır. Bu yüzden bütün araştırmalardan bütünüyle izole **prospektif kör test** olarak adlandırılmamalıdır.

[Gerçek GitHub Actions — **9/9 başarılı**, 635 maçın zaman-kesitli toplu testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42966131592). Eski başarısız ilk deneme yalnız **sentetik üç takımlı testin** gereksiz 10 takım alt sınırından kaynaklandı; gerçek 10 liglik hesap testi ilk denemede de geçti. Test sınırı düzeltildikten sonra aynı matematik ve tam regresyon seti başarılı oldu.

## MS, KG, 2.5 Üst — aynı maçlarda gerçek fark

Brier hatası **küçüldükçe daha iyi**. Aday − orijinal M4 değeri **negatifse iyileşme**:

| Pazar | M4 başlangıç Brier | 0,75 ağırlık Brier / fark | 0,50 ağırlık Brier / fark |
|---|---:|---:|---:|
| KG Var | 0,247015 | 0,246270 / **−0,000745** | 0,245849 / **−0,001166** |
| 2.5 Üst | 0,250540 | 0,249508 / **−0,001032** | 0,248919 / **−0,001621** |
| MS 1X2 | 0,625057 | 0,624500 / **−0,000557** | 0,624703 / **−0,000354** |

Her üç pazarda her iki adayda ortalama Brier hatası azaldı. Ancak **tüm pazar iyileşmelerinin tarih-bloklu keşifsel %95 aralıkları sıfırı içeriyor**:

| Aday | KG farkı aralığı | 2.5 Üst farkı aralığı | MS farkı aralığı |
|---|---|---|---|
| 0,75 | [−0,001870; +0,000414] | [−0,002261; +0,000176] | [−0,002766; +0,001715] |
| 0,50 | [−0,003424; +0,001133] | [−0,003996; +0,000750] | [−0,004850; +0,004228] |

Sonuç: Bu **635 maç**, üç pazar için kesin üstünlük veya güvenilir bahis kazancı göstermiyor.

### Ev sahibinin gol beklentisi açısından

M4 ev gol kare hatası **1,4547**, 0,75'te **1,4280**, 0,50'de **1,4138**. 0,75'in kare hata farkı **−0,02671**, gün-bloklu %95 aralık **[−0,04329; −0,00829]**. Ev sahibi mutlak gol hatası **0,9632 → 0,9569**; fark için keşifsel aralık **[−0,01221; −0,00097]**. Bu **tarihsel veri üzerinde ev gol beklentisi uyumuna dair daha güçlü bir işaret**, ama sırf ev golü daha iyi diye KG/MS kazancı ispatlanmış olmaz. Ayrıca varyant **önceki araştırma sinyalinden** türetildiği için bu tek ileri dönem de tam bağımsız kanıt değildir.

## Önceki rakip-savunma hatası bu yeni tarihlerde de devam etti mi?

Evet, ama daha küçük:

- Modelde güçlü deplasman savunmasına karşı ev sahibinin **gerçekleşen − beklenen** golü: **+0,152** (199 maç).
- Modelde zayıf deplasman savunmasına karşı: **−0,122** (223 maç).
- Fark: **+0,274 gol**. Önceki 702 maçta fark **+0,420** idi. Yön aynı kaldı, büyüklük düştü. Karşılaştırmadaki grup, haricî Elo değil, dondurulmuş M4 kendi deplasman savunma katsayısıdır.

## Lig tutarlılığı — 0,75 savunma ağırlığı

| Lig | KG Brier Δ | 2.5 Üst Brier Δ | MS Brier Δ |
|---|---:|---:|---:|
| ENG1 | −0,000991 | −0,001590 | −0,000793 |
| ENG2 | −0,000219 | −0,001829 | −0,001315 |
| GER1 | +0,002811 | +0,000923 | −0,006536 |
| ESP1 | +0,000913 | +0,002632 | −0,001228 |
| ITA1 | −0,001423 | −0,000232 | +0,001788 |
| FRA1 | −0,000023 | −0,001952 | −0,000585 |
| NED1 | −0,000577 | −0,002110 | +0,004666 |
| TUR1 | −0,002095 | +0,001638 | +0,000694 |
| POR1 | −0,005606 | −0,005226 | +0,000900 |
| BEL1 | −0,000533 | −0,003651 | −0,002265 |

0,75 ağırlık ile **KG 8/10 ligde**, **2.5 Üst 7/10 ligde**, **MS 6/10 ligde** daha düşük hataya sahip. Bu oranlar lig başına sınırlı örnek içerir (45–81 maç); tüm liglerde geçerli yeni bir katsayı politikası anlamına gelmez. Özellikle GER1, ESP1 KG/Üst kötüleşmesi var.

## Teknik güvenlik, karar ve sıradaki iş

**Mühendislik kararı:**

1. **Kullanıcıya gösterilen M4 yüzdeleri, B/C2/C3, ana `main`, aktif `experiment/263-toplu-karsilastirma`, mevcut mühürler ve odds/PDF KESİNLİKLE değişmedi.**
2. Savunma etkisinin yumuşatılması fikrini **reddetmiyoruz**: aynı yönde ikinci tarih bloğu ve ev gol MSE kazanımı, onu teknik olarak araştırmaya değer kılıyor.
3. **0,75 ağırlık**, 0,50'ye göre daha temkinli ve ligler arasında daha dengeli bir tek **gölge aday** olarak ayrı tutulabilir. Bu bir üretim ayarı veya bahis önerisi değildir.
4. Güncel gerçek maç önü mühürleri oluştuğunda, bu tür savunma ağırlığı adayının **maç önü parametreleri de tarihli ve değişmez kaydedilerek** (sonuç sonrasında güncel fit'ten geriye dönük savunma katsayısı çekerek değil) bağımsız bir karşılaştırma yapılması gerekir. Bu koşul sağlanmadan geriye dönük `0.75` yüzdesi üretip model kazancı ilan etmeyiz.
5. 99 maçlık skor kayıt arşivini ve daha önce biten pilotları yeniden açmak yok; **yeni pilot sayımı / model terfisi yok**.

**Kısa karar:** Rakip savunması etkisinin M4'te fazla sert olabileceği iki ayrı tarih bloğunda desteklendi. Fakat KG/2.5 Üst ve MS için nihai üstünlük kanıtlanmadığından **M4 olduğu gibi kalacak**. Tek ihtiyatlı araştırma adayı 0,75; sonraki doğrulama yeni gerçek maçların zamanında kilitlenmiş rakip katsayılarıyla yapılmalı.
