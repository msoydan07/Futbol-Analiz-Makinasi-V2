# xG kaynak arastirmasi 02 — tekil mac ornekleri ve erisim sinirlari

Tarih: 2026-10-31. Yeni veri kabul edilmedi; haftalik guncelleme/otomasyon YOK.

## Yeni dogrulanan adaylar
1. **Football Fallout Championship 2025-26:** https://footballfallout.com/england/championship?season=25648 — sayfa 557 tamamlanmis macin 557'sinde ev ve deplasman xG degerlerinin bulundugunu bildiriyor. Bu kaynak, ENG2 icin sezon kapsaminda en guclu yeni aday. Ancak mac-bazli indirilebilir veri, izin/lisans, tarihsel kimlik ve model kaynagi kontrol edilmeli. Bizim tarihsel CSV'de 552 mac bulunmasi veri kapsami/takvim uyusmazligi; ayni maclar olduklari varsayilmaz.
2. **Tifolab Eredivisie tekil mac xG:** https://www.tifolab.com/teams/apifb-team-410-2026-27?competition=eredivisie&season=2025%2F26 — takim mac listesinde tarih, rakip, H/A, skor ve xG ciftleri var. Ornek: 26 Oct 2025 Excelsior maci 2-0, xG 1.81-0.54. Tekil mac verisi varligi dogrulandi; lig/sezon kimlik uyumu, lisans, erisim ve ev/deplasman yonu kontrol edilmeli.
3. **Tifolab Super Lig tekil mac xG:** https://www.tifolab.com/teams/apifb-team-1001-2025-26?competition=super-lig&season=2025%2F26 — takim mac listesinde tarih, rakip, H/A, skor, xG ciftleri var. Ornek: 24 Aug 2025 Galatasaray maci 0-4, xG 0.90-3.71. Takim sayfasinin baglami ve H/A yonu kontrol edilmeden eslestirme yapilmaz.
4. **StAtz.ai Super Lig 2025-26:** https://statz.ai/competitions/super-lig/stats?season=2025-2026 — 306 maclik sezon icin takim xG/xGA toplamlari; mac-bazli veri oldugu kanitlanmadi, capraz kontrol icin aday.
5. **FootyStats Super Lig:** https://footystats.org/tr/turkey/super-lig/xg — iki sezonu secilebilir gosteriyor; sayfada takim xG ortalamalari, mac bazli export ve lisans bilinmiyor.
6. **FotMob:** https://sportsdatastack.com/tools/fotmob/ — Championship, Eredivisie, Primeira Liga icin xG istatistik sayfalari oldugu bildirilmis; ancak https://github.com/pseudo-r/Public-FotMob-API/blob/main/README.md FotMob kosullarinin izinsiz otomatik/sistematik veri cekimini yasakladigini not ediyor. MIT lisansli ucuncu taraf dokumani FotMob verisine izin anlamina gelmez. Izinsiz toplu kazima YOK.

## Siradaki tek adim
Football Fallout (ENG2) ve Tifolab (NED1/TUR1) icin once kullanim izni, tum maclara erisim, 2025-26/2026-27 sezon kapsami ve en az 10 rastgele mac kimlik dogrulamasi. Ardindan POR1/BEL1 icin tekil mac xG kanitlarini ara. Kaynaklarin ham sayfalari veri deposu degildir; kabul olmadan verified xG CSV'sine yazma.

## Durum
2148 xG son kabul edilen sayi; 7 tarih istisnasi test bekliyor. Yeni xG satiri eklenmedi.
