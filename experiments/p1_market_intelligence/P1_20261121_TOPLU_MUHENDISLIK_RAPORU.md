# P1 İlk Mühendislik Kabulü — 21 Kasım 2026

## Kapsam
`experiment/263-toplu-karsilastirma` araştırma dalındaki aktif kararlar ve kullanıcı PDF arşivi incelendi. Ana 2.6.3, M4/C3, v4 ve eski SHA kayıtları değiştirilmedi. P1 ayrı araştırma dalındadır.

## Uygulama
P0: Her pazar için oransal/additive/power marj arındırma. P1: Üç pazarın ortak KL uyumuyla bağımsız iki-Poisson ters modeli. Tek tercih ve farklı aileden alternatif; kaynak ve marj belirsizliği açık.

## Kullanılabilir kanıt
21 Kasım ikinci PDF arşivinde 12 maç kaydı vardı; 7'sinde ilk PDF'den aktarılan üç pazarın bütün fiyatları var; 5'inde Alt/Üst eksik. 7 set, **ön maç PDF bağımsızca yeniden doğrulanmamış arşiv transkripsiyonlarıdır**. Sonuç skoru eklenmeden betimsel hesap yapıldı.

| Maç | P0 ana tercih | P1 ana tercih | P0–P1 en büyük pazar farkı (puan) |
|---|---|---|---:|
| Manchester City–Fulham | MS 1 %69,15 | MS 1 %69,32 | 0,25 |
| Millwall–QPR | KG Var %59,22 | KG Var %58,29 | 2,02 |
| Norwich–Cardiff | 2.5 Üst %71,39 | 2.5 Üst %71,35 | 1,91 |
| Southampton–Derby | MS 1 %68,48 | MS 1 %68,59 | 0,15 |
| Alavés–Deportivo | 2.5 Alt %57,22 | 2.5 Alt %57,17 | 1,78 |
| Amed–Rizespor | KG Var %60,88 | KG Var %60,14 | 1,91 |
| Galatasaray–Samsunspor | MS 1 %82,13 | MS 1 %82,15 | 0,31 |

**Teknik sonuç:** İlk 7 tam fiyat setinde P0 ve P1'in ana tercihleri aynı. Bunun nedeni P1'in fiyatları açıklayan bir matematik modeli olmasıdır; **P1'in daha isabetli olduğu henüz gösterilemedi**. Özellikle favori oranlarında marj arındırma yöntemi büyük fark oluşturabilir (Galatasaray ilk MS piyasasında yöntemler arası maksimum ~10,9 puan fark); bu nedenle hangi yüzdeye güvenileceği tarihsel sonuç kalibrasyonuyla sınanmalıdır.

**Amed–Rizespor gözlemi:** Sabah doğrudan piyasa referansı MS 1 %50,8 iken yedi olay arasındaki doğrudan piyasa zirvesi **KG Var %60,9** çıktı. Bu, P1'in maç sonucunu bildiği anlamına gelmez; geçmiş yenilgiden sonra geriye dönük yöntem üstünlüğü üretmedik.

## Veri ve karşılaştırma kararı
Doğrulanmış tarihsel ilk PDF zamanı + yedi gerçek oran + resmi sonuç bağları henüz yeterli olarak kanıtlanmadığı için **P0/P1/M4-C3/Hibrit Brier-log-loss değerlendirmesi yapılmadı**. Brier ya da isabet yüzdesi uydurulmadı. Kod skor bileşenlerini hesaplamaya hazırdır; veri seti gerçek maç öncesi olarak bağımsız doğrulandığında tek kör holdout testi gerekir. Hibrit denemesi ancak karşılaştırma gerekçelendirirse yapılır.

## Kabul
- Kod: **Yerel 8 deterministik test geçti**; gerçek 7 fiyat setinde hesaplandı.
- Pazar uyumu: **Betimsel**; model-gol beklentileri gerçek xG değil.
- Gelecekteki maçları öngörme üstünlüğü: **DOĞRULANMADI**.
- Ana 2.6.3'e geçiş: **HAYIR**.