# xG kaynak arastirmasi 03 — iki sezon ve bes lig durum kontrolu

Tarih: 2026-10-31. Yeni xG kaydi kabul edilmedi. Otomasyon/haftalik yenileme kapsam disi.

## Kaynak bulgulari
- **Championship 2025-26** Football Fallout 557/557 finished fixture icin home/away xG oldugunu belirtiyor: https://footballfallout.com/england/championship?season=25648 . Bizim havuz 552 mac; 5 fark icin fikstur/sezon/playoff kapsam analizi sart. Kaynakta xG oldugunu ilan etmek tum satirlara indirme izni demek degil.
- **Championship 2026-27** Football Fallout 144/144 mac icin xG oldugunu belirtiyor: https://footballfallout.com/england/championship .
- **Football Fallout lisans/erisim** https://footballfallout.com/terms (9 Oct 2026) normal kisisel kullanim serbest; ucretli alanlar var, otomatik sistemle makul olmayan yuk yasak; verinin kalici kopyalanip sistemde tekrar kullanilmasina dair acik lisans bulunmadi. Izin/kosullar netlesmeden toplu cekim YOK.
- **Eredivisie 2025-26** Tifolab Feyenoord sayfasi 33/34 mac icin xG gosteriyor, 10 May 2026 Feyenoord–AZ Alkmaar macinda xG acikca bos: https://www.tifolab.com/teams/apifb-team-209-2025-26?competition=eredivisie&season=2025%2F26 . Kaynakta mac bazli xG VAR ama tam kapsam YOK. Eksik maci sifir sayma.
- **Belcika 2025-26** Tifolab Pro League takim sayfasi tekil mac xG ciftlerini listeliyor: https://www.tifolab.com/teams/apifb-team-569-2025-26?competition=pro-league&season=2025%2F26 . Ornek 22 Nov Charleroi 1-0, xG 1.26-0.78. Ancak site takimin perspektifinden xG gosteriyor olabilir: home/away sirasi mac kimligiyle kontrol edilmeli.
- **Portekiz 2025-26 / 2026-27** match-level xG ve yasal arsiv indirme henuz kanitlanmadi.
- **Belcika 2026-27** Tifolab 2025-26 kaniti, 2026-27 kapsamini kanitlamaz; ayrica kontrol edilecek.

## Kabul kapisi
1. Iki sezon icin lig bazinda gercek match-level home/away xG gorulmeli.
2. Kaynak lisansi ve kalici depolama/otomatik erisim izni acik olmasi gerek.
3. 10 rastgele mac: tarih, skor, ev/deplasman, takim, xG, kaynak URL, fixture_id.
4. Eksik xG=bos; asla 0 degil.
5. Kaynak xG modeli/uretici farki kaydedilmeli.
6. Veri kabulu olmadan verified xG toplam 2148; 7 tarih override test bekliyor.
7. Haftalik yenileme ve cron konusuna girme.

## Tek sonraki is
Tifolab kullanim/lisans kosullari ve Portekiz mac-bazli xG kanitini ara; ardindan adaylarin kalici depolama izni durumuna gore kaynak secimi. Uygun yasal kaynak bulunmazsa kullanicidan sadece acik bir veri dosyasi yuklemesini isteme secenegi sun, veriyi uydurma.
