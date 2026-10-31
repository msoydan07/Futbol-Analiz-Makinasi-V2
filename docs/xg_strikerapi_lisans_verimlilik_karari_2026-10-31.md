# StrikerAPI lisans ve verimlilik karari — 2026-10-31

## Resmi dogrulama
- https://strikerapi.com/docs/timing-and-rights : Hesap acikken cekilen veri, hesap acik kaldigi surece arastirma/backtest/model egitimi icin saklanabilir. Ham veri dosyasi/akisi/API olarak yeniden dagitilamaz. Hesap kapanirsa dahili arastirmada kullanilabilir. GitHub public repository'ye ham xG kaydi koymak, ham veri yeniden dagitimi olabileceginden **uygun degil**; izinli veriyi private erisimli depoda saklama veya saglayicidan acik izin gerektirir.
- https://strikerapi.com/docs/timing-and-rights : StrikerAPI xG as-of degil; her sezon dahil yeniden egitilmis model geriye donuk tum sut xG'sini degistirebilir. Katı kronolojik backtest icin mevcut xG'yi sanki mac gunu biliniyormus gibi kullanma; kendi as-of modeli veya farkli kronolojik test gerekir.
- https://strikerapi.com/docs/get-shot-map : get_shot_map 10 kredi; team+season ile toplu sezon sutleri (include_shots opsiyonlu), veya game_id ile tek mac. Bu, 1479 maca tek tek 10 kredi harcama varsayimini gereksiz pahali kilabilir. Takim/sezon bazli cagirip sutleri match_id'ye gruplama olasiligi pilot yanitla test edilmeli.
- https://strikerapi.com/docs : get_team_stats 5 kredi, xG per-match ortalama; bu tekil mac xG tablosu degildir. get_game 5 kredi, mac boxscore; home/away xG alanlari belgelenmeden kesin kabul edilmez.
- https://strikerapi.com/docs/atlas : ENG2, NED1, POR1 shot+xG kapsami; TUR1 ve BEL1 yok.
- https://strikerapi.com/docs : 500 kredi/ay ucretsiz, API key gerekir; kullanici henuz key vermedi ve istenmedi.

## Karar
1. StrikerAPI 3 lig icin **izinli dahili arastirma** adayi; public GitHub ham xG deposu uygun degil. Kalici private depolama icin onay/altyapi degerlendirilmeli.
2. Pilot icin en ekonomik sorgu once tek takim+sezon get_shot_map, yanittaki sutlerde game_id var mi ve tam sayfalama var mi kontrol edilmeli. Pilot kullanici anahtari olmadan yapilamaz.
3. xG revizyonlari ve veri sizintisi uyarisi mutlaka saklanmali.
4. TUR1/BEL1 icin farkli kaynak veya kullanicinin yasal olarak edindigi CSV gerekecek.
5. Kullanici elle yardima hazir; **sadece gercekten eksik kalan fixture ID + lig/sezon + tarih + takimlar + skor + xG_home + xG_away + kaynak URL + model + kontrol** sutunlu somut liste hazirlanacak. Binlerce satirlik manuel giris isteme; once kaynaklardan toplu veriyi bul.
6. Haftalik guncelleme/otomasyon YOK.

## Sabit durum
2148 verified xG, 7 tarih override kabul testi bekliyor; yeni satir eklenmedi.
