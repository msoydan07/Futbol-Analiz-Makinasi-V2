# 2.6.3 — Kaynak kabulünde dairesel kanıt sorununun düzeltilmesi (4 Kasım 2026)

Önceki `88/88` CI, **manifestteki skorun daha önceden hazırlanan CSV ile aynı** olduğunu ölçmüştü. Bu, veri aktarımının bozulmadığına dair mühendislik kanıtıydı; **dış sayfaların 88 maçta bağımsız yeniden doğrulandığına dair test DEĞİL**. Önceki `WEB_ROUND_SCORE_CORROBORATION_ONLY_HUMAN_REVIEW_PENDING` etiketi bu nedenle nihai kaynak kabulü sayılamaz.

## Tek kaynak spesifik örneklem (10 lig)

Aşağıdaki 10 maçın skoru, tarih ve tarafları **genel ligin /results sayfasından farklı olarak, maç-sonucunu açıkça içeren doğrudan ilgili kamu sayfası** ile bu denetimde karşılaştırıldı. Bunlar **gerçek insan onayı değildir** ve raw HTML'leri GitHub'a indirilip SHA ile mühürlenmiş değildir.

| Lig | Maç, sonuç | Görülen somut sayfa | Kanıt düzeyi |
|---|---|---|---|
| ENG1 | Chelsea–Manchester United 2-0 | [kaynak](https://www.premierleague.com/en/news/4751393) | OFFICIAL_LEAGUE_RESULT_NEWS |
| ENG2 | Sheffield United–Wrexham 1-0 | [kaynak](https://www.efl.com/news/2026/october/30/brereton-diaz-goal-gives-sheffield-united-win-over-wrexham/) | OFFICIAL_LEAGUE_RESULT_NEWS |
| GER1 | FC Bayern München–Borussia Dortmund 2-2 | [kaynak](https://www.bundesliga.com/en/bundesliga/news/bayern-munich-borussia-dortmund-match-report-highlights-matchday-8-kane-guirassy-silva-39815/) | OFFICIAL_LEAGUE_RESULT_NEWS |
| ESP1 | FC Barcelona–Deportivo Alavés 6-1 | [kaynak](https://www.laliga.com/en-EG/match/temporada-2026-2027-laliga-ea-sports-fc-barcelona-deportivo-alaves-11) | OFFICIAL_LEAGUE_MATCH_PAGE |
| ITA1 | Milan–Inter 3-1 | [kaynak](https://www.legaseriea.it/serie-a/news/milan-inter-2026-2027-3-1-cronaca-risultato-gol) | OFFICIAL_LEAGUE_RESULT_NEWS |
| FRA1 | OGC Nice–Stade Rennais FC 5-2 | [kaynak](https://www.staderennais.com/matchs/2026-10-30-nice-vs-rennes) | OFFICIAL_CLUB_MATCH_PAGE |
| NED1 | Excelsior Rotterdam–FC Twente 0-9 | [kaynak](https://eredivisie.nl/nieuws/terugblik-speelronde-11/) | OFFICIAL_LEAGUE_MATCH_RESULT_RECAP |
| POR1 | Casa Pia AC–Sporting CP 0-2 | [kaynak](https://www.ligaportugal.pt/match/20262027/ligaportugalbetclic/10/4) | OFFICIAL_LEAGUE_MATCH_PAGE |
| BEL1 | SV Zulte Waregem–Club Brugge 2-4 | [kaynak](https://www.proleague.be/wedstrijden/seizoen-2026-2027-jupiler-pro-league-10-sv-zulte-waregem-vs-club-brugge-685) | OFFICIAL_LEAGUE_MATCH_PAGE |
| TUR1 | KASIMPAŞA A.Ş.–BEŞİKTAŞ A.Ş. 2-2 | [kaynak](https://beinsports.com.tr/haber/kasimpasa-besiktas-17) | LICENSED_BROADCASTER_MATCH_REPORT |

**Özel tarih riski:** [The Guardian sonuç sayfası](https://www.theguardian.com/football/premierleague/results) geçmiş Premier League maçlarını zaman zaman bir gün sonraki başlık altında gösteriyor; [Premier League'in kendi 2026/27 MW9 kaydı](https://www.premierleague.com/en/news/4726845) Chelsea, diğer altı Cumartesi maçı ve Tottenham, Aston Villa'yı **31 Ekim**, Liverpool–Arsenal'i **1 Kasım**, Newcastle–Everton'ı **2 Kasım** olarak doğruluyor. Bu nedenle sonuç sayfasının zaman dilimi gösterimini resmi yerel maç tarihi yerine kullanmayın; makine girdi tarihi için lig-resmî maç sayfası öncelikli.

## Kod ve kabul ayrımı

- `experiments/263/source_evidence_strict_263.py` yalnız aynı fixture ID, lig, sezon, tarih, skor ve **maça özgü dış sonuç adresi** şartlarını inceler; paylaşılan genel /results/ URL'sini yeni kanıt saymaz.
- GitHub testi artık **10 maçta maça özgü kaynak adresinin bulunduğunu ve CSV ile eşleştiğini** ölçer. Eski 88'in kalan **78 maçı** ve ayrı kontrol edilen **8 yeni maç** bu katmanın resmî onay kapsamı dışındadır.
- Kaynak sayfaları CI sırasında çağrılmadığı için burada onay sadece `SPECIFIC_EXTERNAL_RESULT_PAGES_OBSERVED_NOT_LIVE_MACHINE_AUTHENTICATED` olarak raporlanır.
- Güvenlik kapısı **değişmedi**: tüm 96 yeni ek satır için geçerli kaynak kabulü ve gerçek insan incelemesi olmadan `data/quad_accepted_263/source_acceptance.json` oluşturulmaz. API, scraper, canlı bookmaker ya da bahis emri üretilmedi. 4.413 sabit eski veri, 96 pilot kapsamı, B/C2/C3/M4 kodu, S1/S2 ve `main` aynı kaldı.

## Kalan tek pratik kaynak işi

Maçların kaynak **tam liste** ve tam futbol takımı/tarih/gol bilgisi bir kere gözden geçirilmeli; öncelik üçüncü tarafın kullanıldığı BEL1/POR1, site bakımında olan NED1 ve tarihi yanlış gösterebilen dinamik results sayfaları. Gerçek insan denetimi isteyen kabul durumunu kodla taklit etmeyeceğiz. Daha sonra tam 4.509 görüntüsünün SHA ve gerçek kaynak URL'lerini içeren kabul kaydı oluşturulabilir.
