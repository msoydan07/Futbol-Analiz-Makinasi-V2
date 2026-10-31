# xG kaynak arastirmasi 08 — FootyStats mac CSV sutunlari ve Sportmonks

Tarih 2026-10-31. Veri eklenmedi. Haftalik otomasyon yok.

## Kesin dogrulanan
- https://footystats.org/download-stats-csv — Match CSV 64 sutun; `team_a_xg` ve `team_b_xg` **tekil mac home/away xG** alanlari. Ancak tum veri bulunabilirlik kosuluna tabi, tum lig/sezonlarda dolu olacagi garanti degil.
- Ayni sayfa: sezonluk CSV indirmek icin giris gerekiyor; ucretsiz indirilebilen ornekler Premier League 2018-19. 2025-26 / 2026-27 TUR1 ve BEL1 CSV'sinin ucretsiz oldugu kanitlanmadi. Otomatik indirme icin API oneriliyor.
- https://www.sportmonks.com/faq/ — Super Lig'de xG oldugu resmi olarak belirtiliyor; yeni sezonlarda daha ayrintili kapsam, xG 2024 ve sonrasinda.
- https://www.sportmonks.com/blogs/how-to-use-xg-data-with-sportmonks-football-api/ — `expected/fixtures` home/away takim xG, `fixtures/{id}?include=xGFixture`; xG add-on gerekebilir.
- https://www.sportmonks.com/Football%20API/ — Growth 99 EUR/aydan, xG addon 24 EUR/ay civari, tarihsel veri tek seferlik 29 EUR'dan; bunlar fiyat baslangiclaridir, lig/plan durumuna gore degisir. Satin alma YOK.
- FootyStats kaynak lisansi / ham veri GitHub public redistribusyonu acikca onaylanmis degil.

## Uygulama karari
1. **TUR1 ve BEL1** icin FootyStats match CSV izinli elde edilebilirse, `team_a_xg`/`team_b_xg` doluluk ve skor/tarih/takim eslesmesi testiyle aktarilacak.
2. Sportmonks TUR1 icin alternatif; BEL1 fixture xG 2025-26/2026-27 kapsaminda resmi sezon ornegi gerektirir.
3. Once kullaniciya ucretsiz ve izinli CSV/API secenekleri; ucret gerekiyorsa karar icin fiyat/yarar karsilastirmasi. Onaysiz satin alma, login bypass, scraping yok.
4. **Elle tamamlama listesi** sadece fixture kayitlariyla dogrulanmis eksik maclardan turetilecek; tarih/lig/ev/deplasman/skor/source_url/home_xg/away_xg sutunlari; xG bos birakilacak. Mac kimligi eslesmesi olmadan dosya olusturup uydurma mac ekleme.
5. 2148 verified xG; yedi tarih override kabul testi bekliyor; bu arastirma yeni veri eklemedi.

## Siradaki tek is
Mevcut repo fixture CSV'lerini GitHub'dan okuyup TUR1/BEL1 icin iki sezonluk gercek mac kimlikleriyle **manuel tamamlama Excel listesi** cikarmak. Kaynak arastirmasini sinirsiz surdurmek yerine kullanicinin elle yardim teklifini somutlastir. Veri hakki belirsiz ham xG public GitHub'a yazilmayacak.
