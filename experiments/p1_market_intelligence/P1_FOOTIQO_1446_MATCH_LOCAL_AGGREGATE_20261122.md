# P1 — Footiqo tek-şirket yedi ham oran: 1.446 maçlık toplu yerel denetim

**Tarih:** 22 Kasım 2026. **Durum:** Bağımsız P0/P1 araştırması. 2.6.3, M4/C3, mühürler, canlı tahminler **değişmedi**.

## Kaynaklar ve kapsam

Kullanıcının kendi Windows bilgisayarında Footiqo resmi manuel XLSX dışa aktarımlarından üretilmiş **dört ayrı P1_TOPLU_KONTROL_RAPORU.txt** raporu. **Yeni gönderilen 3 TXT** İspanya LaLiga, Almanya Bundesliga, İngiltere Premier League 'LS/Last seasons' dosyalarına ait. Önceki ayrı kontrol İngiltere Premier League **2025/26**. Yeni LS dosyaları orijinal TXT içinde *sezon numarasını açıkça vermiyor*: önceki kullanıcı talebine göre İngiltere 2024/25, Almanya ve İspanya 2025/26 hedeflenmişti; tam sezon etiketi, yalnızca kullanıcı bilgisayarında duran XLSX/yerel JSON dosyasındaki `seasons` alanıyla kesinleşebilir.

**Kritik:** Bunlar yalnız kullanıcının bilgisayarındaki programın beyan ettiği özetler. Bu oturumda **yeni 1.066 ham satır bağımsız gözle incelenmedi**. Yerel program, 1xBet kapanış fiyatı olduğu belirtilen yedi oranı ve skoru kontrol etti; gerçek maç-öncesi fiyat zaman damgası bağımsız sertifikalı değil. Ham fiyatlar/veri bu GitHub deposuna aktarılmadı.

## Her ayrı rapor

| Kohort | Tam yedi oran/sonuç | P0 ana isabet | P1 ana isabet | P0 Brier | P1 Brier | P0 log-loss | P1 log-loss | Aynı ana |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| İngiltere 2025/26 (önceki) | 380/380 | 226 | 223 | 0.529962 | 0.530450 | 0.793779 | 0.794603 | 340 |
| İngiltere LS (yeni) | 380/380 | 227 | 232 | 0.516201 | 0.516540 | 0.775590 | 0.776154 | 350 |
| Almanya LS (yeni) | 306/306 | 197 | 197 | 0.496882 | 0.497710 | 0.754436 | 0.755852 | 269 |
| İspanya LS (yeni) | 380/380 | 248 | 252 | 0.510302 | 0.512058 | 0.769710 | 0.771756 | 354 |
| **Toplam ağırlıklı** | **1446/1446** | **898/1446 (%62.10)** | **904/1446 (%62.52)** | **0.514179** | **0.515033** | **0.774348** | **0.775550** | **1313/1446** |

**Üç yeni dosyanın kendisi:** 1.066/1.066 eşleşme; 0 ret; 0 eksik skor. P0 **672/1066 (%63.04)**, P1 **681/1066 (%63.88)**; P0 vs P1 sırasıyla Brier **0.508553 vs 0.509537**, log-loss **0.767422 vs 0.768758**.

**Hesap yöntemi:** Brier ve log-loss önce lig-sezon TXT'lerinde maç başına üç pazar makro ortalaması olarak raporlanır; toplu değerler maç sayılarına göre ağırlıklandırıldı. TXT'lerin özetleri yalnız altı ondalık hassasiyettedir. Aynı ana seçimler toplanabilir; **aynı ana tercih oranı** ve isabet sayıları, P0/P1 hatalarının bağımsız olduğu anlamına gelmez.

## Yorum ve test kapısı

- Toplamda **P1 +6 ana isabet**, ancak **P0 dört kohortun dördünde de hem Brier hem log-loss bakımından daha iyi** (küçük fark).
- Tek tek eşleşik hata/hit karşılaştırması, olasılık aralığı bazlı kalibrasyon ve tarih blok bootstrap güven aralığı **bu TXT özetlerinden çıkarılamaz**. TXT'lerden kalibrasyon katsayısı öğrenmiş gibi raporlamak yasak.
- Başlangıç için mantıklı kronolojik deney tasarımı: 2024/25 lig-sezonlarını **yalnız eğitim**, 2025/26 lig-sezonlarını **dokunulmaz test** olarak ayır. Bu tarihe göre iki dönemi gerçek XLSX/yerel çalışma dosyaları ile doğrulamadan eğitim/test iddiası yok.
- Mümkünse Almanya 2024/25 ve İspanya 2024/25 Odds + Scores resmî manuel export çiftleri toplanarak 2024/25 eğitim kohortu genişletilir. Sonra mevcut 2025/26 İngiltere/Almanya/İspanya yeni dönem testte kalır. Kullanıcı ham CSV/XLSX verilerini kamuya açık GitHub'a yüklemeyecek.
- Oran kaynağı ve lisansı: https://footiqo.com/database/ ve https://footiqo.com/dataset-licence/ ; kullanım izni ve veri yenileme koşulları takip edilir. Gerçek zamanlı iddaa kullanımına, M4/C3 veya karar v4'e **otomatik geçiş yok**.

**Sonuç:** 1.446 maçlık tek-şirket fiyatlı araştırma veri havuzu var. Yeni 1.066 maçın yerel kalite kontrolü olumlu. Henüz istatistiksel üstünlük, kalibrasyon eğitimi veya kârlılık kanıtı yok.
