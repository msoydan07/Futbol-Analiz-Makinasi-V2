# xG arastirmasi 05 — acik lisansli kaynak denetimi (2026-10-31)

## Net bulgu
**Aranan bes lig (ENG2/NED1/TUR1/POR1/BEL1), 2025-26 ve 2026-27, tekil mac home/away gercek xG icin hem tam kapsami hem kalici yeniden kullanim izni kanitlanan acik veri seti henuz bulunamadi.** Bu, verinin internette olmadigi anlamina gelmez.

## Kaynak kanitlari ve sinirlar
- StatsBomb Open Data: https://github.com/hudl/open-data — gercek shot-event xG ve arastirma kullanimina yonelik paylasim; fakat aciklanan musabaka/sezonlar secili, 2025-26 ve 2026-27 aranan bes lig icin tam arsiv yok. Referans kapsam: https://sportsdatastack.com/tools/statsbomb-open-data/
- OpenFootball Europe: https://github.com/openfootball/europe — CC0 kamu mali fikstur/skor; xG yok. xG kaynagi yerine kullanma.
- Open Matchday: https://github.com/oladeeayo/open-matchday — 2026-27 75 lig, mac sonucu/sut/korner/kart; acikca xG yok. Upstream haklar ayrica gecerli.
- SportsDataStack xG rehberi: https://sportsdatastack.com/data/xg/ — Championship/Eredivisie/Primeira Liga dahil xG gosteren servisler listeleniyor; bir sitenin ucretsiz goruntulenmesi toplu indirip GitHub'da kalici saklama izni demek degil. Ozellikle StrikerAPI ayrica incelenmeli.
- OpenFoot API: https://openfootapi.com/docs — top-5 xG ozellikleri ve expanded Europe ligleri ayni hizmette yer aliyor, ama iki ifadenin bir arada olmasi aranan bes ligde xG kaniti degil.
- Wyscout Pappalardo 2017-18 CC BY 4.0 mac-event dataseti, hedef sezonlar degil: https://github.com/withqwerty/open-football

## Kesin karar
1. StatsBomb'u bu iki sezonun eksiklerini kapatacakmis gibi sunma.
2. OpenFootball/Open Matchday sonuc verisini gercek xG yerine koyma.
3. Kaynaklarin lisansini ihlal eden scraping yapma.
4. Siradaki tek is: StrikerAPI'nin bes lig, iki sezon, mac-bazli xG, ucretsiz kota, export ve kalici saklama izinlerini kendi resmi dokumanindan denetle.
5. Ardindan kalan adaylardan yazili veri kullanma izni/izinli export olanlari kisa listeye al; 10 maclik pilotu sadece izinli kaynaktan yap.
6. Sonraki asamaya kadar 2148 dogrulanmis xG sabit; 7 tarih duzeltmesi test bekliyor.
7. Haftalik guncelleme ve otomasyon kapsam disi.
