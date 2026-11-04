# 2.6.3 — 4.509 maçlık güncel hafta sonu veri paketi: ilk sonuç / kaynak teyidi (4 Kasım)

**Gerçek GitHub CI:** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41802358251 (7/7 hedefli test ve 10 canlı sağlayıcı dosya indirmesi başarılı).

- **4.413** değiştirilemez temel maç + önceki **88** değişmeden korunmuş tamamlanmış maç + **8** yeni 2 Kasım 2026 sonucu = **4.509**; 10 ligde sonuç tazeliği (ilk pilot tarihi 6 Kasım esas) 4–6 gün.
- SHA-256: `69d687965500a260cc965a1482c23c1e07f11ebcabb1adaa9441dc6a17334a14`.
- Bu SHA'lı `extended_history.csv` / `refresh_audit.json` / `preflight_report.json` dosyaları, üstteki **GitHub Actions artifact** paketinde; `main` veya ana M4 kodları değişmedi.
- Gerçek kaynak indirme makine tarafından yapıldı. Kaynak iddiası ve 4.501 kayıt bütünlüğü korundu; fakat **4.509 maçın tüm sonuçları bağımsız resmî kaynaklarda çapraz onaylanmadı**.

## 8 yeni tamamlanmış maç — sadece dış skor çapraz kontrolü

| Lig | Maç (2 Kasım 2026) | Staged sonuç | İkinci kaynak |
|---|---|---:|---|
| POR1 | Gil Vicente FC – Vitória SC | 0-0 | [OFFICIAL_LEAGUE](https://www.ligaportugal.pt/match/20262027/ligaportugalbetclic/10/5) |
| ITA1 | Sassuolo – Fiorentina | 2-4 | [OFFICIAL_LEAGUE](https://www.legaseriea.it/serie-a/match/932c3719da2a4fe4adba1c846cae9814/Sassuolo-vs-Fiorentina) |
| POR1 | SL Benfica – FC Alverca | 1-0 | [OFFICIAL_LEAGUE](https://www.ligaportugal.pt/match/20262027/ligaportugalbetclic/10/9) |
| TUR1 | Gençlerbirliği – Corendon Alanyaspor | 5-0 | [OFFICIAL_CLUB](https://www.alanyaspor.org.tr/Haber/genclerbirligi-corendon-alanyasporumuz-5-0) |
| FRA1 | Lorient – Brest | 0-2 | [BROADCASTER_SCORE](https://www.beinsports.com/en-us/soccer/ligue-1/lorient-vs-brest-2026-10-31?origin=app) |
| ITA1 | Atalanta – Parma | 0-3 | [OFFICIAL_LEAGUE](https://www.legaseriea.it/serie-a/news/atalanta-parma-2026-2027-0-3-cronaca-risultato-gol) |
| ESP1 | RC Deportivo – CA Osasuna | 2-1 | [OFFICIAL_LEAGUE](https://www.laliga.com/es-PE/partido/temporada-2026-2027-laliga-ea-sports-rc-deportivo-ca-osasuna-11) |
| ENG1 | Newcastle United – Everton | 0-1 | [BROADCASTER_SCORE](https://www.skysports.com/football/newcastle-united-vs-everton/report/559532) |

**8/8 skor uyuştu.** `BROADCASTER_SCORE` resmî federasyon skoru yerine geçmez; ilgili lig fikstürü ayrıca doğrulandığında bunun seviyesi ayrı kaydedilir. Bu çalışma geçmiş 88 yeni satırın bağımsız çapraz doğrulanmış olduğunu **iddia etmez**.

## Doğruluk / kabul sınırı

1. Bu rapor yalnız mevcut haftalık dosyanın SHA, önceki veri bütünlüğü, tazelik ve 2 Kasım'daki son **8** maçın dış sonuç kontrolüdür. Ligler arası bütün 4.509 kaydı otomatik federasyon onayına yükseltmez.
2. `forward_quad.py` gerektirdiği `HUMAN_VERIFIED_SOURCE_ACCEPTANCE` statüsüne burada geçilmedi. İnsan tarafından doğrulanmayan skorlar için otomatik yalan onay veya yapay reviewer kullanılmaz.
3. **Sıradaki çözülmesi gereken tek önemli engel:** önceki 88 ek maç için gerekli kaynak kabul prosedürü; ardından 4.509 snapshot için gerçek insan kaynak incelemesi ve maç başlamadan dört-model pilot tahmini kaydı. Bu öncesinde `data/quad_accepted_263` oluşturulmayacak.
4. 96 adaylık fikstür, S1/S2, M4/B/C2/C3 matematiği, eski arşiv ve `main` unchanged. Yalnız bu deney dalında kanıt toplandı.
