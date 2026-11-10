# Futbol Analiz Makinası 2.6.3 — 99 yeni maçın kanıt kapsamı (10 Kasım 2026)

**Birincil hedef:** Önceden keşfedilmiş 99 adaydan yayınlanmış maç skoru bilgisi eksik 43'ünü tamamlamak ve **kanıt sınıfını şişirmeden** ana 2.6.3'e koruyarak kayıt altına almak. Bu araştırma, sonuçları üretim modeline katmaz.

## Sonuç özeti

| Kanıt sınıfı | Maç | Ne gerçekten kanıtlandı? |
|---|---:|---|
| Önceki 28; kamuda yayımlanmış lig/federasyon skoruyla ayrı veri sağlayıcı kaydı ve kanonik takım/tarih/skor uyuşması | 28 | **Araştırma düzeyinde iki farklı kaynakta skor uyuşması**, ama federasyonun benzersiz maç ID'si henüz yok |
| Önceki ek 28; doğrudan lig/federasyon sonuç sayfası veya kulüp haftalık özeti, sağlayıcı satırı tekrar karşılaştırması yok | 28 | La Liga 10, Eredivisie 9, Ligue1 kulüp özeti 9 için **kamusal skor gözlemi**, resmî maç-ID attestation değil |
| Bu turda 43; yayıncı ve bağımsız sonuç sayfaları, yanında kısmi resmî lig fikstürü/maç sonrası haberleri | 43 | 10 Premier League, 15 Championship, 10 Belçika, 8 Portekiz maçı için skor ve kanonik takım kimliği araştırma kaydı; **ikinci sağlayıcı satırı ve tüm yerel resmî maç ID'si yok** |
| **Toplam yayınlanmış skor gözlemi** | **99** | **99 gözlem**; hiçbirine otomatik bağımsız federasyon tekil maç ID onayı veya üretim kabulü verilmedi |

### Son 43 kaydın kaynakları

| Lig | n | Yayımlanmış skor kaynağı | Tamamlayıcı ama tek başına skor attestasyonu olmayan kaynak |
|---|---:|---|---|
| ENG1 | 10 | [RadarFooty 10. hafta sonuçları](https://radarfooty.com/en/competition/premier-league/round/10) | [Premier League 2026/27 resmî fikstürü](https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-2026-27), [Premier League 8 Kasım maç sonrası yazısı](https://www.premierleague.com/en/news/4757019/what-we-learned-from-sundays-matches/) |
| ENG2 | 15 | [Sky Sports Championship 2026 Kasım skorları](https://www.skysports.com/championship-scores-fixtures) | [EFL 7 Kasım maç sonu istatistik yazısı](https://www.efl.com/news/2026/november/07/sky-bet-championship--post-match-stat-pack/), [EFL 6–8 Kasım resmî maç görevlileri](https://www.efl.com/news/2026/november/05/referee-appointments--6---8-november/) |
| BEL1 | 10 | [Football Web Pages, Belçika Kasım sonuçları](https://www.footballwebpages.co.uk/belgian-pro-league/fixtures-results/november) | [DFB Datencenter Jupiler Pro League 11. hafta](https://datencenter.dfb.de/datencenter/jupiler-pro-league/2026-27/11) — **Almanya federasyonu, Belçika ligi yöneticisi değil** |
| POR1 | 8 | [É Golo, Liga Portugal 11. hafta sonuçları](https://egolo.pt/jogos/2026-27/liga-portugal/) | [Liga Portugal resmî 11. hafta fikstürü](https://www.ligaportugal.pt/noticias/28531/horarios-definidos-ate-a-12.a-jornada) |

**İki kritik tarih detayı**:
- İngiltere Championship'teki 15 yeni maç = **4 Kasım 3 maç** + **6–7 Kasım 12 maç**; başka bir lig haftasının üç maçını yanlışlıkla 15. hafta olarak etiketleme.
- Portekiz 11. haftada 9 fikstür var; Estoril–Marítimo **ertelenmiş** ve oynanmamış maç olarak sekiz skorun dışında. Eksik sonucu **0-0 olarak kaydetme**. Portekiz resmî fikstür sayfası tek başına skor doğrulamaz.

### Ne test ettik?

- 43 yeni maçın tamamında aynı 2026/27 sezonuna üye takımın kanonik ID'si, tarih, ev/deplasman sırası ve skor / H-D-A tutarlılığı sınandı.
- Yeni 43 kayıt, eski 28 + 28 kanıt kaydından ve 4.518 eski kabul edilmiş geçmiş maçtan **ayrı ve benzersiz maç kimlikleri** taşıyor; toplam **99** aynı maç yeniden sayılmıyor.
- Yalancı `official_fixture_id`, `provider_row_linked`, yanlış takım ID, kaynak alan adı, çelişkili skor / sonuç veya yinelenen maç QA testlerini **başarısız** kılacak şekilde kuruldu.
- **Yeşil GitHub testi, web sayfasından maç maç resmî ID çekilmiş demek değildir.** Bu yalnız elle/web ile oluşturulan kaynak kaydının yapısal bütünlüğünü denetler.
- Football-Data'ya yeni bir istek yapılmadı. Önceki iki hafif sorgu bütçesi korunuyor.
- 43 maç için KG Var gözlemi: BEL1 **5/10**, ENG1 **6/10**, ENG2 **10/15**, POR1 **4/8**. 2,5 Üst: BEL1 **5/10**, ENG1 **5/10**, ENG2 **11/15**, POR1 **3/8**. Bunlar yalnız **bu dönemin kaynak gözlemleri**, M4 kalibrasyonu veya tahmin üstünlüğü değil.
- `data/quad_accepted_263/extended_history.csv`, `m4_integrated.py`, `m4_lock.json`, `four_model_value_policy_263.py` blob SHA'ları `experiment/263-toplu-karsilastirma` ile aynı; **40 orijinal mühür ve 40 orijinal karar** da içerik SHA bakımından aynı.
- `experiment/263-toplu-karsilastirma` içinde 10 Kasım Salı veri yenilemesinin **ayrı staged/pending review** kaydı bulundu. Bu araştırma dalıyla **birleştirilmedi**; üretime alınmadı.

### Gerçek sonraki veri kabul kapısı

1. 99 araştırma skorunun tamamını ayrı, haklara uygun, **append-only** kabul dosyasına yazmadan önce her yeni maç için **benzersiz yerel federasyon/lig fikstür ID'si, maç tarihi, ev/deplasman kimliği ve son skor** eşleşmesi gerekir. Bunu otomatik bulamadığımızda “resmî teyit edildi” yazmayız.
2. İlk 28 skor iki kaynak uyuşmalı fakat federasyon-ID'si eksik; ikinci 28 ve son 43 için aynı sağlayıcı satırıyla tekrar karşılaştırma yapılmamış. **71 kaynak satırı rekonsilyasyonu eksik**. Kaynağa indirme sınırı uygun olduğunda **tek kontrollü işlemde** yapılmalı, eski test döngüsüne girilmemeli.
3. Kullanım ve yeniden yayımlama hakları doğrulanmadan sağlayıcı ham CSV'si GitHub'a kopyalanmaz; maç sonuçlarını resmî federasyon bilgi/ID kaynaklarından ve uygun haklarla almak öncelikli.
4. Oyun kimliği (baskı, blok yüksekliği, oyuncu rotasyonu) bu 99 skor kaydından çıkmaz. Pres ve taktik için 2026/27 kapsamlı olay / tracking veri kaynağı mevcut değil. Pozisyon yaratma kalitesi ayrı kanıt ister.
5. M4 ve gol pazarı modelleri yalnız **bağımsız ileri tarihli, maç önü mühürlenmiş, sonradan resmî sonuçla eşlenmiş** örneklerde değerlendirilip değiştirilebilir. 99 skoru yeni bir kör tahmin pilota dönüştürme.

**Mühendislik kararı:** 99/99 için kamuya açık skor bulma işi bu aşamada tamamlandı. **Resmî maç kimliği attestasyonu ve üretime uygun veri kabulü tamamlanmadı**; M4/çarpan/şut/gol olasılığı değiştirilmedi. Gol pazarlarını geliştirmek için önce mevcut modelin farklı liglerdeki kalibrasyonunu bağımsız mühürlerle ölçme kararı devam ediyor.

## GitHub kanıtları

- [Son 43 kaynak notlu, kanonik ID'li skor kaydı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-last43-public-evidence-20261110/research/opponent_goals/remaining_43_public_score_observations_20261110.json)
- [99 kayıt benzersiz kaynak sınıfı denetimi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-last43-public-evidence-20261110/research/opponent_goals/reports/last43_public_score_evidence_audit_20261110.json)
- [GitHub 99'lu denetim testinin başarı kaydı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42787794578)
- [Önceki 56/99 kaynak kapanışı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-public-scoreboard-expansion-20261110/docs/263_2026_11_10_56OF99_RAKIP_GUCU_KANIT_KAPANISI.md)
