# 22 lig × 2 sezon — veri havuzu güncel toplu kapanış raporu

**14 Kasım 2026; maçların kesim tarihi 13 Kasım 2026.** Bu belge veri envanteri ve henüz kapatılamayan kaynak engelleridir; eğitim izni veya gelecek maç tahmini değildir. Kullanıcının ana M4'ü, tahmin mühürleri ve xG belgesi değişmemiştir.

## Bir bakışta

| Durum | Adet |
|---|---:|
| Lig hedefi | **22 (13 analiz, 9 eğitim)** |
| Lig–sezon hücresi | **44** |
| 2025/26 için kalıcı kaynak olan lig | **22/22** |
| 2026/27 kalıcı arşiv bulunan lig | **17/22** |
| 2026/27 sadece canlı kaynağa erişilen lig | **5/22** |
| **Toplam kalıcı kaynak-maç kimliği** | **9.460** |
| Ana 10 ligin donmuş 10 Kasım kaynak arşivi | **4.617** |
| Genişleme araştırma arşivi / ayrıca BEL1 eksik maç | **4.842 + 1 = 4.843** |
| 2025/26 kalıcı kayıt | **7.779** |
| 2026/27 kalıcı kayıt | **1.681** |
| Beş 2026/27 liginde sadece canlı API'de okunan kayıt | **633 — toplamda YOK** |
| Manuel xG eksikliği | **1.855 (90 güncel, 1.765 geçmiş)** |
| Bu turda model eğitimine kabul | **0** |

**9.460 sayısı onaylı eğitim örneği değildir.** Ana 4.617 ve genişleme 4.842 farklı liglerde olduğundan sayı çakışmaz; son eklenen Belçika bir maçının ana 4.617'de eksik olduğu ayrı grup kontrolünde tespit edilmiştir. Eski kaynak HOLD kayıtları halen duruyor.

## 22 lig, iki sezon ve ek kaynak durumu

| Lig | Hedef | 2025/26 kalıcı | 2026/27 kalıcı | 2026/27 yalnız API |
|---|---|---:|---:|---:|
| ENG1 — Premier League | Analiz | 380 | 100 | — |
| ENG2 — Championship | Analiz | 552 | 180 | — |
| GER1 — Bundesliga | Analiz | 306 | 81 | — |
| ESP1 — La Liga | Analiz | 380 | 119 | — |
| ITA1 — Serie A | Analiz | 380 | 110 | — |
| FRA1 — Ligue 1 | Analiz | 306 | 90 | — |
| NED1 — Eredivisie | Analiz | 306 | 108 | — |
| TUR1 — Süper Lig | Analiz | 306 | 99 | — |
| POR1 — Primeira Liga | Analiz | 306 | 98 | — |
| BEL1 — Pro League | Analiz | 312 | 99 | — |
| SCO1 — Premiership | Analiz | 234 | 42 | — |
| DNK1 — Superliga | Analiz | 192 | — | 84 |
| CHE1 — Super League | Analiz | 228 | 57 | — |
| ENG3 — League One | Eğitim | 569 | 158 | — |
| ENG4 — League Two | Eğitim | 557 | 164 | — |
| ENG5 — National League | Eğitim | 560 | — | 190 |
| GER2 — 2. Bundesliga | Eğitim | 306 | 99 | — |
| ESP2 — Segunda | Eğitim | 468 | — | 141 |
| ITA2 — Serie B | Eğitim | 391 | — | 110 |
| FRA2 — Ligue 2 | Eğitim | 309 | — | 108 |
| GRE1 — Super League | Eğitim | 236 | 35 | — |
| AUT1 — Bundesliga | Eğitim | 195 | 42 | — |

**Tablo toplamları:** 2025/26 **7779**, 2026/27 **1681**, birlikte **9460**. API sütununu kalıcı toplamına ekleme.

## Bu turda gerçekten bitirdiklerimiz

**1. Belçika Pro League 2025/26 standart maçları.** Önceki 311 sonuçta **240 normal + 71 play-off** vardı. Mevcut ana arşivin takım kimlikleriyle kurulan üç grup grafiği, 6 takım gruplarında **30+30**, 4 takımlı düşme grubunda **11/12** karşılaşmayı gösterdi. Eksik olan **3 Mayıs 2026 FCV Dender EH – RAAL La Louvière 2–1**, [Dender kulübü](https://fcvdendereh.be/nl/nieuws/nieuws/2026/fc-dender-la-louviere-2-1-tanken-vertrouwen/) ve [RAAL kulübü](https://www.raal.be/event/playoffs-md05-dender-raal/) tarafından yayımlandı. Eski ana skor dosyasına dokunmadan ayrı kaynak kaydı ekledik: **240 normal + 72 play-off = 312** maç. [Kanıt](./bel1_2025_26_one_official_missing/bel1_2025_26_312_source_stage_identity_completion_20261114.json).

**2. İspanya Segunda 2025/26 kaynak açığı.** Önceki 131 ile mükerrer olmayan **331 normal + 6 play-off = 337 yeni maç** zaten arşivlenmişti. Yeni 331 normal maçın skorları bağımsız kaynakta birebir teyit edildi; 41 aynı Deportivo takım adı kaynak tekrarı çıkarıldı, iki maçın oynanma tarihi düzeltildi. Sezon **462 normal + 6 play-off** olarak kapandı. [Kaynak kalite raporu](./ccby_footballcharts_esp2_2025_26_original_source/esp2_2025_26_462_regular_41_duplicate_alias_6_playoff_131_old_identity_20261114.json).

**3. Güncel sezonun 17 liginde yeni kaynak kapsamı.** Football Charts canlı araştırma API'sinde 15 lig doğrudan, ayrıca Portekiz `Liga Portugal` ve Belçika `Jupiler Pro League` kesin lig kodlarıyla karşılaştırıldı: **17/17 kaynaktan sayım**. Önceki beş canlı ligdeki 633 maç yeniden çekilmedi. 12 ligin kaynak sayısı kalıcı arşivle eşleşti; sayısal eşitlik yine de maç kimliği eşitliği kanıtı değildir. [17 lig raporu](./2026_27_17_persisted_leagues_one_freshness_aggregates_only_20261114.json) · [Portekiz/Belçika çözümü](./2026_27_only_2_portugal_belgium_catalog_name_freshness_20261114.json).

**4. İspanya La Liga 2026/27'deki +1 kaynak hatası kapandı.** API 120 `0–0` dahil skorlu görünen olay, ana kaynakta ise 119 bitmiş maç vardı. Kaynakta fazla görünen **10 Ekim 2026 Rayo Vallecano – Athletic Club 0–0**, gerçekte **13 dakika dolaylarında durdurulmuş**, [resmî LaLiga maç merkezi](https://www.laliga.com/partido/temporada-2026-2027-laliga-ea-sports-rayo-vallecano-athletic-club-8) maçı **9 Aralık'a ertelemiş**. Bu **tamamlanmış bir 0–0 değildir**; arşive FT olarak eklenmedi ve araştırma HOLD'a yazıldı. Böylece LaLiga'nın kaydedilmiş **119 bitmiş maç sayısı** kaynak kalite filtresinden sonra doğru. [Olay denetimi](./esp1_2026_27_official_2026_nov8_gap_only/esp1_oct10_rayo_athletic_suspended_fake_0_0_HOLD_20261114.json).

**5. Eski işler döngüye sokulmadı.** Önceki 4.505 araştırma skor denetimi, 331 Segunda yeni FT kontrolü, 106+8 özel aşama, 296 kaynak HOLD sabit tutuldu. Herhangi bir M4 motor, yeni pilot, oran veya tahmin mühürü üzerinde çalışılmadı.

## Hâlâ gerçek olan dört veri engeli

**A — 2026/27 beş ligde kalıcı arşiv hakkı:** **ENG5 National League 190, ESP2 Segunda 141, ITA2 Serie B 110, FRA2 Ligue 2 108, DNK1 Danimarka 84** = **633**. Kişisel araştırma API'sinde sonuçlara erişebiliyoruz fakat canlı verinin kapsamlı ham kopyasını herkese açık GitHub'da yeniden yayımlama izni yok. Eski, 2025/26'ya ait CC BY 4.0 tarihsel snapshot, 2026/27 canlı API'ye otomatik lisans vermez. Kalıcı arşiv için açık yeniden yayın izni veya özgün hakları açık başka kaynak gerekir. [API kullanım koşulları](https://www.football-charts.com/terms).

**B — Dört 2026/27 ligde ek olabilecek 118 kaynak kimliği:** **SCO1 İskoçya +33, CHE1 İsviçre +21, GRE1 Yunanistan +34, AUT1 Avusturya +30.** Bunlar **kaynak sayısı farklarıdır**, tek tek yeniden yayınlanma hakkı ve tam maç kimliği teyidi henüz yoktur. Eski OpenFootball yayınları Ekim 2026 başında kaldığı için bunlardan aynı maçları tekrar almak eksikleri doldurmaz. **118'i 9.460'a eklemedik**.

**C — Geçmiş kaynak kalite HOLD:** **296** eski doğruluk HOLD ayrı; ayrıca Bastia–Red Star hükmen 0–0 ve şimdi Rayo–Athletic ertelenmiş 0–0 tamamlanmış sonuç olarak kullanılamaz. League One/Two ve National League eski kaynak fazlalıkları için dikkatli lig bazlı filtre sürüyor. Geriye dönük sahte maç skoruyla boşluk kapatılmadı.

**D — Elle girilecek xG:** Önceki kullanıcı dosyasında güncel **90** ve geçmiş **1.765** olmak üzere **1.855** maçın satırları hazır. Maç sonrası iki takım xG'si, kaynağın doğrudan maç URL'si ve gözlem tarihi girilmeli. xG yoksa boş bırakılmalı; tahmini maç önü xG veya uydurma 0.00 ile doldurulmamalı. Eski 459 kayıt ayrı kontrol sekmesindedir. Dosyanın yeni bir kopyası bu sohbetten teslim edilir; GitHub'a hassas kişisel çalışmanın sonucu yüklenmez.

## Son karar

**Yapabildiğimiz araştırma/olgu/veri toplama işlerini gerçekleştirdik; kalan haklar ve 118 güncel aday, kanıtsız olarak "bitmiş" yazılamaz.** 2025/26 Belçika ve İspanya eksikleri çözüldü; 22 lig için 44 hücrenin 39'u kalıcı, 5'i hak engeline takılmış canlı kaynak. Kullanıcının xG girişine geçmeden önce M4, mühürler, önceki deneyler ve skor arşivleri korunmuştur. Başka bir sağlayıcının ham verisini izinsiz yeniden yayınlamayacağız.
