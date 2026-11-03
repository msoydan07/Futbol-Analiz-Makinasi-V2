# Futbol Maç Analiz Makinası 2.6.3 — UEFA 3–5 Kasım 2026 / AŞAMA 5 TOPLU KABUL RAPORU

**Tarih:** 3 Kasım 2026, Türkiye saati.  
**Tek çalışma:** Önceden kaydedilmiş beyondELO ve 9 lig gol kaynakları + 3 Kasım'da incelenen UEFA/ikincil takım haberleri ile 17 maç / 34 takım eşleştirmesi. **Yeni Elo verisi indirilmedi, geçmiş deneyler tekrarlanmadı.**

## Sonuç özeti

- **17/17 maç, 34/34 takım:** aynı ortak international beyondELO ölçeğinde 3 Kasım 2026 günlü **Elo + RD** bulundu; 30 Ekim–1 Kasım son puanlanan maç tarihli ve tüm UEFA başlangıçlarından önce.
- Elo kaynak SHA-256: **073a461d810396af6ae74216e8d400d5c5d27a654a153014d36dc4a4c7ee8be5**. Orijinal kaynak denetim zamanı **2026-11-03 05:16:36 UTC** (TSİ 08:16:36). Daha önce alınmış 9 yerel lig gol kaynağı saatleri 06:30:45–06:30:56 UTC (TSİ 09:30). Her ikisi de bütün 17 maçın ilk başlama saatinden önce.
- **24/24 Şampiyonlar Ligi takımında UEFA'nın 2 Kasım 2026 tarihli olası 11/sakatlık/ceza editoryal yazısı** bulundu. Bu bir **resmî kesin ilk 11 veya kulüp doktor raporu değildir**.
- **10/10 Avrupa Ligi takımında üçüncü taraf Starting11 tahmini ve kısmi sakat/cezalı haberleri** gözlendi. **Bu takım haberlerini resmî veya bağımsız doğrulanmış saymıyoruz.** Hangi isimlerin bildirildiği açıklayıcı kanıtta ayrıntılı; haberler eksik liste olabilir.
- **0/34 kesin maç başlangıç kadrosu** (o günkü bu veri hazırlığında yayımlanmış/bağımsız teyit edilmiş değil). İlk 11 olmaması engel değildir; maç saatine yakın ayrı katmanda teyit edilecek.
- **8/8 yeni yazılım/tarih/kimlik kaynak testi başarılı.** GitHub tek koşu: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41591598226 .
- Tek yapılandırılmış sonuç artefaktı: GitHub artifact **13210143232**, dosya **17_match_elo_news_readiness.json**. Ayrıntılı 17 maç kaydı, 34 takım kanonik ID'si, Elo, RD, son puanlanma tarihi, UEFA haber kaynağı/sınıfı, öne çıkan eksikler ve belirsizlikler içerir.

## 17 maçın aynı kaynaktaki Elo puanları

**Önemli:** Aşağıdaki *Elo farkı* asla doğrudan galibiyet olasılığı, gol λ, 1X2 tahmini veya bahis önerisi değildir. RD değerleri de kaynakla birlikte arşivlenmiştir. İsimler sahadaki takımların aynı kaynaktaki doğrulanmış ad/slug eşleştirme adaylarıdır; bağımsız ortak UEFA numerik kulüp ID'si değildir.

| Türkiye tarihi | Eşleşme | Ev Elo | Dep Elo | Ev−Dep fark |
|---|---|---:|---:|---:|
| Salı 3 Kasım | Galatasaray – Stuttgart | 1797 | 1795 | +2 |
| Salı 3 Kasım | Atlético Madrid – Bayern Münih | 1929 | 2088 | −159 |
| Salı 3 Kasım | Barcelona – Aston Villa | 2042 | 1993 | +49 |
| Salı 3 Kasım | Feyenoord – Inter | 1714 | 1905 | −191 |
| Salı 3 Kasım | Manchester United – Roma | 1881 | 1866 | +15 |
| Salı 3 Kasım | Villarreal – PSG | 1762 | 2092 | −330 |
| Çarşamba 4 Kasım | Fenerbahçe – Liverpool | 1720 | 1968 | −248 |
| Çarşamba 4 Kasım | Dortmund – Real Betis | 1909 | 1857 | +52 |
| Çarşamba 4 Kasım | Porto – Napoli | 1832 | 1785 | +47 |
| Çarşamba 4 Kasım | PSV – Club Brugge | 1814 | 1889 | −75 |
| Çarşamba 4 Kasım | Leipzig – Manchester City | 1811 | 2022 | −211 |
| Çarşamba 4 Kasım | Lens – Como | 1770 | 1842 | −72 |
| Perşembe 5 Kasım | Crystal Palace – Hoffenheim | 1792 | 1712 | +80 |
| Perşembe 5 Kasım | Real Sociedad – Lyon | 1745 | 1785 | −40 |
| Perşembe 5 Kasım | AZ – Juventus | 1634 | 1814 | −180 |
| Perşembe 5 Kasım | Leverkusen – Marseille | 1857 | 1713 | +144 |
| Perşembe 5 Kasım | Celta – Union SG | 1719 | 1846 | −127 |

Bu 34 takımda Elo son puanlanan maç günleri **30 Ekim–1 Kasım**, RD yaklaşık **65,8–77,4** aralığında. Elo kaynağı: beyondELO, https://beyondelo.com, **CC BY 4.0**.

## Kulüp/kadro haberleri: kaynağa bağlı ihtiyatlı durum

### Şampiyonlar Ligi — UEFA haberinin 2 Kasım tarihli *Out/Doubtful* beyanları

Kaynak: https://www.uefa.com/uefachampionsleague/news/02ab-21f9907f0a27-6a6a67e9775d-1000--champions-league-predicted-line-ups-matchday-4-team-news-/

- Galatasaray – Stuttgart: UEFA Galatasaray için haberde *Out: None* bildirdi; Stuttgart için **Sauer, Stiller, Vagnoman** yok.
- Atlético Madrid – Bayern Münih: Atlético'da **Cardoso**, cezalı **Hjulmand**; **Koke belirsiz**. Bayern'de **Luis Díaz, Gnabry, Musiala, Saibari** yok; **Neuer, Olise belirsiz**.
- Barcelona – Aston Villa: Barcelona'da **Christensen, Eric García, Xavi Espart, Koundé, Olmo**; Villa'da **Ruggeri, Wan-Bissaka** yok.
- Feyenoord – Inter: Feyenoord'da **Bos, Moder, Nieuwkoop, Smal, St. Juste**; Inter'de cezalı **Bastoni**, ayrıca **Jones, Lautaro Martínez, Stones** yok; **Luis Henrique belirsiz**.
- Manchester United – Roma: United'da **Dorgu, Rashford, Šeško, Shaw** yok; **Diallo belirsiz**. Roma'da **Koné, Pellegrini, Svilar** yok; **Dybala belirsiz**.
- Villarreal – PSG: Villarreal'de **Akhomach, Alassane, Foyth, Moreno**; PSG'de **Dembélé, Kvaratskhelia, Marquinhos, Nuno Mendes** yok.
- Fenerbahçe – Liverpool: Fenerbahçe'de **Aké, Asensio** yok; **Oppong belirsiz**. Liverpool'da **Bradley, Ekitiké, Frimpong, Leoni** yok.
- Dortmund – Real Betis: Dortmund'da **Kauã Prates**; Betis'te **Cucho Hernández, Junior Firpo** yok.
- Porto – Napoli: Porto'nun UEFA haberindeki kesin eksik listesi boş; **William Gomes, Pietuszewski belirsiz**. Napoli'de **Badiashile, Di Lorenzo, Lobotka, Neres, Olivera, Alisson Santos, Spinazzola** yok; **De Bruyne, Højlund, Milinković-Savić belirsiz**.
- PSV – Club Brugge: PSV'de **Lammers, Ouaissa, Wanner**, Brugge'de **Ordoñez** yok.
- Leipzig – Manchester City: Leipzig'de **Ouédraogo** yok, **Estève belirsiz**. City'de **Semenyo** yok.
- Lens – Como: Lens'te **Édouard, Ganiou, Sima**; Como'da **Diao, Kean** yok, **Chalobah belirsiz**.

**Güvenlik:** UEFA'nın editoryal tahmini dahi son dakikada değişebilir. *Out: None*, bütün kulüp kadrosunun sağlıklı olduğuna dair bağımsız tıbbi kanıt değildir.

### Avrupa Ligi — şimdilik sadece üçüncü taraf tahminleri

Kaynak: https://starting11.com/europa-league (3 Kasım incelemesi). UEFA'nın resmî kadro duyurusu gibi kullanılmayacak, ikinci kaynakla veya doğrudan kulüple teyit gerek.

| Maç | Üçüncü tarafın öne çıkardığı eksiklik / belirsizlik örnekleri |
|---|---|
| Crystal Palace – Hoffenheim | Palace: Mateta (kaynak cezalı diyor), Riad, Sarr, Tomiyasu; Hoffenheim: Prass (kaynak cezalı diyor), Conté, Coufal, De Cat |
| Real Sociedad – Lyon | Sociedad: Beitia, Odriozola, Zakharyan, Aramburu; Lyon: Kango, Morton, Openda, Ouédraogo |
| AZ – Juventus | AZ: Hornkamp, Resink, Smit, Zoet, Verhulst; Juventus: Çelik, Conceição, González, Grabara ve ayrıca adı verilmeyen diğerleri |
| Leverkusen – Marseille | Leverkusen: Badé, Diaby, Doué, Eichhorn ve diğerleri; Marseille: Cornelius, Moumbagna |
| Celta – Union SG | Celta: Cuenca, El Abdellaoui, Iglesias, Núñez ve diğerleri; Union SG: El Hadj, Hurtevent, Kričfaluši, Mac Allister ve diğerleri |

**Eksik iddiaları kesinleştirilmedi:** Üçüncü taraf listelerindeki "ve diğerleri" için toplam hasta/cezalı sayısı hesaplanmadı, otomatik hiçbiri gerçek kadrodan eksiltilmedi. Maç özelinde resmî UEFA cezaları ve güncel kulüp haberleri ayrıca teyit edilmeden bu bilgiler matematik katsayısı olamaz. Takımın 2026/27 yerel lig fikstüründeki kimliği 167 Elo havuzunda teyitlidir, fakat UEFA listesinde oyuncu uygunluğunun bağımsız doğrulaması yapılamadı.

## Bir defalık mühendislik testleri ve korunan sınırlar

Tek GitHub Actions koşusu aşağıdakileri birlikte denetledi:

1. **17/17** fikstür ID'si, ev/deplasman **34 kanonik takım ID'si**, tarih ve saat, önceki stage3/stage4 dosyaları arasında aynen örtüşüyor.
2. 34 kulüpte önceden indirilmiş sağlayıcı CSV'sinin SHA'sı, beklenen slug, kulüp adı, Elo, RD ve son rating tarihi eşleşiyor. Tüm kaynak elde edilme zamanları ilk kickoff öncesinde.
3. **24 UEFA editoryal**, **10 ikinci kaynak** haberi doğru kaynağa ayrılıyor; hiçbiri bağımsız doğrulanmış resmî başlangıç kadrosu diye etiketlenmiyor.
4. Bozuk Elo CSV, kickoff sonrası rapor tarihi, yanlış kulüp haber kimliği, sahte UEFA güvenilirlik etiketi, kickoff sonrası yerel gol kaynağı ve izinsiz Elo model katsayısı ayrı ayrı testte reddedildi.

**Kesin sonuç:** Bu çalışma **"Aşama 5 ön hazırlık veri katmanı tamamlandı; Elo 17/17 mevcut; CL editoryal kadro haberleri 12/12 kaynaklı; EL 5/5 ön haberleri resmî doğrulama bekliyor"** durumundadır. Final maç günü oyuncu uygunluğu/ilk 11 hâlâ açık ve ilk 11 yokluğu analizi durdurmaz. Ayrıca sezon öncesinden dondurulmuş gözlemlere bakıp geleceği gördük sanma hatası yok; bu snapshot'lar 3 Kasım'da gerçekten kaydedildi, ancak haberlerin benzersiz first_seen UTC kanıtı yok.

**Sonraki adım Aşama 6:** Elo'suz M0 ve *sadece gölge deneme* Elo'lu varyant için pre-match matematik/çıktı güvencesini hazırlamak. Önce Aşama 7 toplu kalite denetimi; en son Aşama 8 tahmin/kayıt kilitlemesi, kullanıcı talimatına göre. Gölge matematikte bile sonuçlar görülmeden kilit zamanı, veri kimliği, katsayı seçimi önceden belirlenir.

**Değişmeyenler:** main, 10 yerel lig, B/C2/C3/M4, 17 bölüm, 0/100 pilot, oran/EV/A-B-C, gol lambda üzerindeki Elo ve sakatlık çarpanları (henüz onaysız).
