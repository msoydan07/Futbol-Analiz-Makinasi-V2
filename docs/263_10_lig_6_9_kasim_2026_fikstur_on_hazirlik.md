# Futbol Maç Analiz Makinası 2.6.3 — 10 LİG / 6–9 KASIM 2026 FİKSTÜR ÖN HAZIRLIĞI

**Durum: YALNIZ GÜN VE EŞLEŞME ADAYLARI · 96 MAÇ · 0 YENİ TAHMİN KAYDI**

Kaynaklar 3 Kasım 2026 itibarıyla resmî lig/federasyon fikstürleri esas alınarak tarandı. Championship ve Belçika tam hafta listelerinde resmî kısmi duyurulara ek üçüncü taraf kaynağı kullanıldı; bu iki ligde her maçın resmî tekil teyidi T−60 ön koşulu. Hollanda için KNVB'nin arama indeksi ile Eredivisie'nin güncelleme ilanı birlikte incelendi. Bu dosya skor, model yüzdesi veya bahis önerisi içermez.

**Günlük sayım:** 6 Kasım Cuma 10; 7 Kasım Cumartesi 44; 8 Kasım Pazar 42; 9 Kasım Pazartesi 0. **Toplam 96**.

## Çalışma protokolü

1. Şimdilik yalnız maç tarihi ve tarafları saklanır. Saatler bilinçli olarak **onaylanmış T−60 saatleri sayılmaz**, kod/kanonik takım kimliği eşleştirilmiş kabul edilmez.
2. Gün gelince resmî fikstür ve maç saati yeniden teyit edilir; maç başlama T−60 penceresinde ilk 11 resmî kulüp/lig veya güvenilir kaynaklardan araştırılır. Açıklanmamış ilk 11 analizi durdurmaz, iki tarafın 11'i uydurulmaz.
3. Uygun maç için B, C2, C3, M4 aynı anda, aynı pre-match girdilerle hesaplanır. Kilitleme yalnız maç başlamadan SHA+commit kanıtıyla başarılıdır. T60 yapılandırması **bu dosyayla otomatik yaratılmadı**.
4. Aday 96 maç, 100 maç pilotuna **otomatik sayılmaz**. Sadece başarıyla kilitlenen gerçek maç sayılır; önceki modeller ve Avrupa M0/M0+Elo kayıtları değiştirilmez.
5. Saat, rakip, statü veya takım kimliği belirsiz çıkarsa kaydı kilitlemeden önce o maç ayrı doğrulanır. Maç sonrası hiçbir girdi tahmine girmez.

## Gün gün maçların tamamı

### Cuma — 2026-11-06 · 10 maç

**Türkiye Süper Lig (TUR1) — 1:** Gaziantep FK – Kasımpaşa.

**İngiltere Premier League (ENG1) — 1:** Everton – Coventry City.

**İngiltere Championship (ENG2) — 1:** Derby County – Bolton Wanderers.

**Almanya Bundesliga (GER1) — 1:** Hamburger SV – Borussia Mönchengladbach.

**İspanya La Liga (ESP1) — 1:** Sevilla – Deportivo Alavés.

**İtalya Serie A (ITA1) — 1:** Venezia – Udinese.

**Fransa Ligue 1 (FRA1) — 1:** Toulouse – Strasbourg.

**Hollanda Eredivisie (NED1) — 1:** Willem II – PEC Zwolle.

**Portekiz Primeira Liga (POR1) — 1:** Famalicão – Arouca.

**Belçika Pro League (BEL1) — 1:** Standard Liège – SK Beveren.

### Cumartesi — 2026-11-07 · 44 maç

**Türkiye Süper Lig (TUR1) — 4:** Eyüpspor – Kocaelispor; Samsunspor – Konyaspor; Göztepe – Başakşehir; Galatasaray – Amed SK.

**İngiltere Premier League (ENG1) — 4:** Leeds United – Tottenham Hotspur; Arsenal – Hull City; Fulham – Newcastle United; Nottingham Forest – Manchester City.

**İngiltere Championship (ENG2) — 11:** Wrexham – Wolverhampton Wanderers; Portsmouth – Stoke City; Bristol City – Norwich City; Preston North End – Southampton; Watford – Middlesbrough; Blackburn Rovers – West Ham United; Birmingham City – Swansea City; Charlton Athletic – Sheffield United; West Bromwich Albion – Millwall; Cardiff City – Burnley; Queens Park Rangers – Lincoln City.

**Almanya Bundesliga (GER1) — 5:** Borussia Dortmund – SV Elversberg; RB Leipzig – FC Augsburg; Mainz 05 – Bayern München; SC Paderborn 07 – Eintracht Frankfurt; VfB Stuttgart – Werder Bremen.

**İspanya La Liga (ESP1) — 4:** Málaga – Racing Santander; Espanyol – Deportivo La Coruña; Osasuna – Athletic Club; Valencia – Real Madrid.

**İtalya Serie A (ITA1) — 4:** Cagliari – Frosinone; Torino – Lecce; Parma – Bologna; Roma – Sassuolo.

**Fransa Ligue 1 (FRA1) — 2:** Auxerre – Paris FC; Paris Saint-Germain – Troyes.

**Hollanda Eredivisie (NED1) — 3:** Fortuna Sittard – Telstar; ADO Den Haag – Sparta Rotterdam; Excelsior – Go Ahead Eagles.

**Portekiz Primeira Liga (POR1) — 3:** Nacional – Académico; Alverca – Casa Pia; Sporting CP – Moreirense.

**Belçika Pro League (BEL1) — 4:** Westerlo – Charleroi; OH Leuven – KV Mechelen; Royal Antwerp – Lommel SK; RAAL La Louvière – Cercle Brugge.

### Pazar — 2026-11-08 · 42 maç

**Türkiye Süper Lig (TUR1) — 4:** Çaykur Rizespor – Erzurumspor FK; Çorum FK – Fenerbahçe; Alanyaspor – Trabzonspor; Beşiktaş – Gençlerbirliği.

**İngiltere Premier League (ENG1) — 5:** Brighton – Brentford; Crystal Palace – Liverpool; Ipswich Town – Bournemouth; Sunderland – Chelsea; Manchester United – Aston Villa.

**Almanya Bundesliga (GER1) — 3:** 1. FC Köln – Bayer Leverkusen; Freiburg – Union Berlin; Hoffenheim – Schalke 04.

**İspanya La Liga (ESP1) — 5:** Elche – Real Betis; Real Sociedad – Rayo Vallecano; Celta Vigo – Levante; Villarreal – Getafe; Atlético Madrid – Barcelona.

**İtalya Serie A (ITA1) — 5:** Napoli – Lazio; Genoa – Milan; Monza – Atalanta; Inter – Como; Fiorentina – Juventus.

**Fransa Ligue 1 (FRA1) — 6:** Rennes – Lille; Brest – Lyon; Le Mans – Monaco; Angers – Nice; Le Havre – Lorient; Lens – Marseille.

**Hollanda Eredivisie (NED1) — 5:** Heerenveen – Feyenoord; FC Twente – Ajax; AZ Alkmaar – FC Groningen; SC Cambuur – PSV; FC Utrecht – NEC Nijmegen.

**Portekiz Primeira Liga (POR1) — 5:** Estoril – Marítimo; Santa Clara – Gil Vicente; Vitória Guimarães – FC Porto; Estrela Amadora – Benfica; Rio Ave – Braga.

**Belçika Pro League (BEL1) — 4:** Club Brugge – Anderlecht; Gent – Kortrijk; Union Saint-Gilloise – Genk; Sint-Truiden – Zulte Waregem.

### Pazartesi — 2026-11-09 · 0 maç
Bu kapsamda planlanmış maç yok.

## Kaynak ve resmî teyit durumu

| Lig | Birincil kaynak | Kapsam notu |
|---|---|---|
| TUR1 | [Resmî fikstür](https://www.tff.org/Default.aspx?pageId=198) | OFFICIAL_FEDERATION; [yardımcı bağlantı](https://www.tff.org/Default.aspx?hafta=11&macId=222921%26rcbID%3Dctl00_RPane_m_198_2084_ctnr_m_198_2084_mo%26rcbServerID%3Dmo&pageId=198) |
| ENG1 | [Resmî fikstür](https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-season-2026-27) | OFFICIAL_LEAGUE |
| ENG2 | [Resmî fikstür](https://www.efl.com/news/2026/july/30/see-the-latest-sky-sports-tv-selections/) | OFFICIAL_TV_SELECTIONS_PLUS_SECONDARY_COMPLETE_ROUND; [yardımcı bağlantı](https://eflchampionship.co.uk/fixtures) |
| GER1 | [Resmî fikstür](https://products.bundesliga.com/fixtures) | OFFICIAL_LEAGUE |
| ESP1 | [Resmî fikstür](https://www.laliga.com/en-GB/laliga-easports/results/2026-27/gameweek-12) | OFFICIAL_LEAGUE |
| ITA1 | [Resmî fikstür](https://en.legaseriea.it/serie-a/fixtures-results) | OFFICIAL_LEAGUE_SEARCH_RESULT |
| FRA1 | [Resmî fikstür](https://ligue1.com/fr/articles/l1_article_5839-) | OFFICIAL_LEAGUE |
| NED1 | [Resmî fikstür](https://www.knvb.nl/competities/eredivisie/programma) | OFFICIAL_FEDERATION_SEARCH_RESULT_PLUS_LEAGUE_UPDATE; [yardımcı bağlantı](https://eredivisie.nl/nieuws/data-en-tijden-najaar-vriendenloterij-eredivisie-bekendgemaakt/) |
| POR1 | [Resmî fikstür](https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada) | OFFICIAL_LEAGUE |
| BEL1 | [Resmî fikstür](https://www.proleague.be/teams/cercle-brugge-3/fixtures-results) | PARTIAL_OFFICIAL_CLUB_PAGES_PLUS_SECONDARY_COMPLETE_ROUND; [yardımcı bağlantı](https://www.playmakerstats.com/competition/jupiler-pro-league?fase=242662&jornada_in=11) |

**Üretim sınırı:** Bu hazırlık kaydı model performansı, ilk 11 doğrulaması veya gerçek T−60 kilidi değildir. Yerel lig 100 maç pilotu henüz sadece yeni gelecekteki gerçek kilitli kayıtlarla ilerleyecek.
