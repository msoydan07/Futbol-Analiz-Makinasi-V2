# xG kaynak arastirmasi 04 — Portekiz bulundu, Tifolab kullanim siniri

Tarih: 2026-10-31. Bu rapor kaynak taramasidir; henuz yeni xG satiri kabul edilmedi.

## Dogrulanan yeni bulgular
- Portekiz Primeira Liga **2025-26** Tifolab takim mac listesinde skor, rakip, tarih, H/A ve xG ciftleri bulunuyor. Ornek sayfa: https://www.tifolab.com/teams/apifb-team-242-2025-26?season=2025%2F26 . 5 Ekim Arouca macinda xG bos; 26 Ekim Guimaraes macinda xG 1.71-0.48. Her macin kapsandigi iddia edilemez.
- Portekiz **2026-27** Tifolab ornek sayfa: https://www.tifolab.com/teams/apifb-team-212-2025-26?competition=liga-portugal&season=2026%2F27 . 9 tamamlanmis macin 9'unda xG gorundugu belirtiliyor; sayfa kimlik parametresi sezonla uyumsuz gorunebilecegi icin takim/season kontrolu zorunlu.
- Portekiz 2025-26 xG.Football sezon tablosu: https://xg.football/competitions/portugal-primeira-liga/seasons/2025/xg . 308 oynanmis macin 306'sinda iki takim xG verisi oldugunu belirtiyor; fakat gorulen tablo takim toplamlari, mac bazli export kaniti degil.
- Tifolab acik kullanim sartlari: https://www.tifolab.com/terms . Scrape/reverse-engineer yasak; servis otomatik kullanimlari kisitlayabilir. **Kalici GitHub'a toplu kopyalama lisansi acik degil**. Izin alinmadan toplu kazima ve xG havuzuna transfer YOK.
- Football Fallout sartlari: https://footballfallout.com/terms . Normal kisisel kullanim ve makul otomasyon siniri var; toplu yeniden dagitim/depolama icin acik lisans yok.

## Guncel aday kapsami
| Lig | Mac-bazli aday | Iki sezon | Toplu yeniden kullanim izni |
| ENG2 | Football Fallout | Her iki sezon gorunuyor | BELIRSIZ |
| NED1 | Tifolab | 2025-26 gorunuyor, 2026-27 teyit bekliyor | BELIRSIZ / scrape yasagi |
| TUR1 | Tifolab/Mackolik | 2025-26 gorunuyor, 2026-27 teyit bekliyor | BELIRSIZ / scrape yasagi |
| POR1 | Tifolab | Iki sezondan ornek var, tam kapsama teyit bekliyor | BELIRSIZ / scrape yasagi |
| BEL1 | Tifolab | 2025-26 gorunuyor, 2026-27 teyit bekliyor | BELIRSIZ / scrape yasagi |

## Karar
Bes lig icin artik mac-bazli adaylar var; **veri kaynagi bulmak ile kalici olarak kullanma izni ayni sey degil**. Lisans yoksa otomatik kazima veya kullaniciya binlerce satir elle yazdirma yok. Alternatif olarak acik lisansli mac-bazli xG veri seti veya saglayicidan acik yazili izin aranacak.

## Sonraki TEK is
Acik lisansli, 2025-26 ve 2026-27 sezonlarini kapsayan gercek match-level xG arastirmasi; gerekirse saglayicilara toplu kisisel arastirma kullanimi ve depolama icin izin sorusu hazirla. Kullanici onayi olmadan satin alma yok; otomasyon yok. Verified xG = 2148, 7 tarih override test bekliyor.
