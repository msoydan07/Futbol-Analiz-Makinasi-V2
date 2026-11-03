# Futbol Maç Analiz Makinası 2.6.3 — UEFA 3–5 Kasım, Aşama 4: tek toplu güncel gol veri denetimi

**Tarih:** 3 Kasım 2026 Salı. **Kapsam:** 17 resmî fikstür adayı, 34 takım, 9 üst lig.  
**Karar:** **17/17 maçın yerel lig gol, iç/deplasman, son 5 maç ve geçmiş rakip performansı girdileri kaynaktan toplanıp güvenli biçimde çıkarıldı.** Bu sadece **tanımlayıcı veri hazırlığı kabulüdür**; matematiksel tahmin, Elo→lambda veya canlı model kabulü değildir.

## 1. Tek toplu koşu, gerçek veri kaynakları

- Github Actions: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41590323827 — SUCCESS.
- **9/9 deterministik yazılım testi** başarıyla tamamlandı. Aynı işte 9 ayrı lig CSV'si yalnız **birer kere** indirildi ve 17 maçın 34 kulübüne bağlandı; geçmiş 124, 432 veya 4.413 maç deneyleri tekrar çalıştırılmadı.
- İndirilen kaynak: **football-data.co.uk, 2026/27 sezonu**. Kaynak sayfası https://football-data.co.uk/downloadm.php, 3 Kasım 2026 kontrolünde sayfa güncelleme beyanı **02/11/26**. Her indirilmiş ham CSV, SHA-256 ve gerçek UTC alım anıyla birlikte tek kanıt artefaktında korundu.
- **Arşiv:** GitHub Actions artifact ID **13209189270**, adı \`263-uefa-nov3-5-nine-league-goal-data-one-shot\`. İçinde \`stage4_goal_data_readiness.json\` (17 maçın ayrıntıları) ve \`source_csv/{E0,D1,SP1,I1,F1,N1,P1,B1,T1}.csv\` (9 özgün ham dosya) var.
- Anlık görüntünün oluşturulması: **2026-11-03 06:30:44 UTC = 09:30:44 Türkiye saati**; kaynak dosyaları **06:30:45–06:30:56 UTC** aralığında alındı. Bu üç günün 17 seçili maçının başlama saatlerinden önce.
- 9 lig dosyasındaki **812 tamamlanmış yerel lig maçı** ayrıştırıldı; hepsi doğru sezon, kulüp ve skor kontrolünden geçti. **0** bilinmeyen takım kaynak adı, **0** hatalı skor/mükerrer yönlü eşleşme. **9/9 kaynağın son tamamlanan maç günü 1 Kasım 2026**.

| Lig | Kaynak kodu | Tamamlanmış 2026/27 maç | Son tarih |
|---|---|---:|---|
| İngiltere Premier League | ENG1 / E0 | 89 | 01.11.2026 |
| Almanya Bundesliga | GER1 / D1 | 72 | 01.11.2026 |
| İspanya La Liga | ESP1 / SP1 | 108 | 01.11.2026 |
| İtalya Serie A | ITA1 / I1 | 98 | 01.11.2026 |
| Fransa Ligue 1 | FRA1 / F1 | 80 | 01.11.2026 |
| Hollanda Eredivisie | NED1 / N1 | 99 | 01.11.2026 |
| Portekiz Primeira | POR1 / P1 | 88 | 01.11.2026 |
| Belçika Pro League | BEL1 / B1 | 89 | 01.11.2026 |
| Türkiye Süper Lig | TUR1 / T1 | 89 | 01.11.2026 |
| **Toplam** | **9 lig** | **812** | |

**Nereden gelmedi?** Hiçbir xG/xGA, xG vekili, H2H, oyuncu haber/ilk 11, piyasa oranı, korner varsayımı veya onaylanmamış Elo katsayısı bu hesaplara alınmadı. Ham CSV'de başka alanlar bulunması onları matematikte kullanıldığımız anlamına gelmez.

## 2. Gerçek hesaplanan 34 takım veri kapsamı

- 34 takımın 2026/27 sezonunda **8–11 tamamlanmış yerel lig maçı** var; medyan **10**.
- Her takımın en son yerel maçının hedef UEFA gününe uzaklığı **3–5 gün**, medyan **4**. Bütün kaynak dosyaları 1 Kasım maçlarına kadar tamamlanmış güncel sonuç içeriyor.
- **34/34** için son 5 kendi lig maçı mevcut ve bu 5 maçtaki rakiplerin **o maçtan önce gözlenmiş yerel lig maç başına puanı (PPG)** hesaplanabildi: toplam **170/170 son maç rakip-PGG bağlantısı**.
- Son 5 puan bir form göstergesidir; son 5 rakip PPG'si *ülke içi, yalnız tanımlayıcı rakip zorluğu*dur. Farklı ülkelerin PPG ortalamalarını doğrudan küresel güç ölçeğine dönüştürmez.

## 3. 17 maçın özet ham karşılaştırma girdileri

**Tablo okuma:** Ev takımının kendi ligindeki **ev saha** sonuçları ile deplasman takımının kendi ligindeki **deplasman** sonuçları gösterilir. \`Ev GF/GA – Dep GF/GA\` sırasıyla kendi saha rolünde maç başına atılan/yenilen gol, iki ayrı ligi birbirine eşit ilan eden uluslararası beklenen gol veya tahmin değildir. \`Son 5 puan\` ev/deplasman takımının son 5 yerel lig maç puanı (15 üzerinden).

| UEFA maçı | Önceki yerel maç adedi Ev/Dep | Rol maç adedi Ev saha/Dep saha | Ev GF/GA – Dep GF/GA | Son 5 puan Ev/Dep |
|---|---:|---:|---|---:|
| Galatasaray – Stuttgart | 10/8 | 5/5 | 2,20/1,20 – 1,60/2,00 | 12/6 |
| Atlético Madrid – Bayern München | 11/8 | 5/4 | 2,20/0,60 – 1,75/1,00 | 15/11 |
| Barcelona – Aston Villa | 11/9 | 6/4 | 4,00/1,17 – 1,00/1,50 | 12/11 |
| Feyenoord – Inter | 11/10 | 5/5 | 2,40/1,00 – 1,80/1,20 | 11/12 |
| Manchester United – Roma | 9/10 | 4/5 | 1,50/1,75 – 2,80/1,00 | 3/11 |
| Villarreal – PSG | 11/9 | 5/6 | 1,20/1,40 – 2,50/1,17 | 7/15 |
| Fenerbahçe – Liverpool | 10/9 | 5/4 | 3,40/1,20 – 1,75/0,75 | 9/9 |
| Dortmund – Real Betis | 8/11 | 4/5 | 2,00/0,50 – 1,20/1,40 | 9/8 |
| Porto – Napoli | 10/10 | 5/6 | 2,60/0,40 – 1,50/1,33 | 15/7 |
| PSV – Club Brugge | 11/10 | 6/5 | 3,50/0,83 – 2,60/1,00 | 7/15 |
| Leipzig – Manchester City | 8/9 | 4/4 | 4,50/0,00 – 2,25/0,75 | 9/9 |
| Lens – Como | 9/10 | 4/6 | 2,25/1,25 – 2,17/1,17 | 9/13 |
| Crystal Palace – Hoffenheim | 9/8 | 4/4 | 1,50/2,50 – 1,25/2,25 | 4/6 |
| Real Sociedad – Lyon | 11/9 | 5/4 | 1,40/1,40 – 0,75/1,00 | 12/9 |
| AZ – Juventus | 11/10 | 5/5 | 1,80/1,00 – 1,20/1,20 | 4/7 |
| Leverkusen – Marseille | 8/9 | 4/4 | 2,50/1,25 – 1,75/1,25 | 9/12 |
| Celta – Union SG | 11/10 | 6/5 | 1,50/1,00 – 3,00/0,80 | 8/13 |

**Nokta atışı örneklem uyarısı:** Leipzig'in 4 iç saha maçındaki maç başına 4,50 golü, herhangi bir Avrupa rakibine karşı 4,50 gol beklentisi değildir. 4 maçlık rol örnekleminde ham sayıları uluslararası güçle karıştırmak hatalı olur. Bütün 17 maç için aynı kural geçerlidir.

## 4. Kaynak zamanı, doğrulanamayanlar ve güvenlik

1. **Bu çalışma için gerçek pre-kickoff kaynak anı var:** 3 Kasım TSİ 09:30 kaydı ve SHA'lı ham dosyalar; 17 UEFA maçının hepsi bu saatten sonra. 2025/26 tarihsel Elo çalışmasındaki **first_seen bulunmama** problemi bu yeni dosyanın 3 Kasım'da alındığını inkâr etmez. Bununla birlikte Football-Data'nın her tarihsel satırı maç oynandığı gün ilk ne zaman yayımladığını bağımsız doğruladığımız söylenemez.
2. **Tek kaynaktan tamlık:** Kaynak dosyalarının dokuzunda da iç tutarlılık ve kimlik eşleşmesi var. Bu, kulüplerin her skorunun ayrıca federasyon/FotMob gibi ikinci kaynakta teker teker doğrulandığı anlamına gelmez. Model kalibrasyonu veya sonuçların dış bağımsız doğrulaması henüz ayrı safhadadır.
3. **Sıkı maç önü kesiti:** Sadece \`2026/27\` kendi ligindeki maçlar; \`yerel sonuç günü < UEFA hedef günü\`. Aynı gün ve gelecekteki sonuçlar kullanılmadı; oynanmamış fixture sıfır gol diye kaydedilmedi. Her geçmiş rakibin PPG'si, söz konusu geçmiş maçtan önceki maçlardan hesaplandı.
4. **Kapsam:** Sadece 167 Avrupa Elo aday havuzuna giren 34 kulüp ve 9 üst lig. Championship ve Erzurumspor Elo alt kapsamına döndürülmedi; ana 10 lig veri hattı değiştirilmedi.
5. **Gölge tahmin yok:** Kaydedilmiş/tahmin edilmiş 1X2, KG, 2,5 Alt/Üst veya Poisson gol λ yok; onaysız Elo etkisi kullanılmadı; bahis veya pilot kaydı yok. \`main\`, B/C2/C3/M4, mevcut 17 bölüm değişmedi.

## 5. Tek mühendislik kararı

**AŞAMA 4 — GÜNCEL KAYNAKLI TANIMLAYICI GOL VERİSİ: TAMAMLANDI (17/17).**

Sıradaki iş **Aşama 5**: aynı 17 maçın ortak uluslararası Elo puanlarının alım zamanı ve son güncellenen maç tarihiyle doğrulanması, daha sonra haber/kadro/sakatlık/ceza/ilk 11 durumlarının **kaynaklı ve ayrı** tamamlanması. Bu aşamada ilk 11'in henüz yayımlanmaması engel değildir.

İlk matematiksel gol/olasılık kıyası ancak veri ve kimlik kontrolleri geçtikten sonra gölge deney olarak değerlendirilecek; değişmez tahmin kilidi kullanıcının talimatıyla en son safhadır.
