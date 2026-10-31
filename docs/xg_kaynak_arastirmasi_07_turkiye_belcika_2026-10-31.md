# xG kaynak arastirmasi 07 — Turkiye ve Belcika, somut karar

Tarih 2026-10-31. Kapsam TUR1/BEL1 2025-26 ve 2026-27. Veri havuzuna yeni xG EKLENMEDI. Haftalik otomasyon YOK.

## Kanitli kaynaklar
- **Belcika 2025-26** https://statz.ai/index.php/competitions/belgian-pro-league/xg?season=2025-2026 — sezonluk xG/xGA, kaynak olarak Sportmonks'u acikliyor. 311 mac, ligde play-off yapisi var. Gorulen tablo takim toplami, mac-bazli ham xG arsivi degil.
- **Belcika 2026-27** https://footystats.org/belgium/pro-league/datasets — 81/306 maclik 2026-27 sayfasi, 2025-26 secenegi, CSV ve API oldugunu belirtiyor. Veri sutunlarinin match-level home/away xG icerdigi, CSV lisansi ve hangi planla indirildigi ayrica dogrulanmali. Acik ornek indirmeler EPL 2018-19; BEL 2025-26 indirme linkinin gorunmemesi ucretsiz oldugunu kanitlamaz.
- **Turkiye/Belcika** https://openfootapi.com/docs — ligleri fikstur/sonuc kapsamina aliyor, xG icin ayri ucretli ve desteklenen musabaka siniri var. Lig adi gecmesi mac xG'si kaniti degil.
- **Open Matchday** https://github.com/oladeeayo/open-matchday/blob/master/README.md — TUR1 ve BEL1 dahil 75 ligde mac sonuclari ve istatistikler; xG yok. Repo, ileri seviye xG icin acik issue ile veri talebi/arastirma is birligi oneriyor.

## Karar
1. BEL1 icin **Sportmonks** upstream veri saglayici olarak ve **FootyStats** izinli CSV/API adaylari olarak denetlenecek. Mac-bazli xG alanlari ve lisans kanitlanmadan veri alinmayacak.
2. TUR1 icin **Mackolik/Tifolab** mac sayfalari xG varligini gosteriyor; toplu kalici kullanim izni belirsiz. **FootyStats Super Lig** CSV/API alan ve lisans kontrolu yapilacak.
3. Ayni xG saglayicisinin birden fazla sitede kullanilmasi bagimsiz capraz dogrulama degildir.
4. Kaynaklarin birinde veri yoksa kullaniciya sadece fixture_id/tarih/takim/skor bazli kalan mac listesi verilecek; gercek home_xg, away_xg, kaynak_url alanlari bos kalacak. Kaynaksiz deger girilmeyecek.
5. Public GitHub'da ham lisansli veriyi yayinlamadan once haklar kontrol edilecek.
6. 2148 verified xG sabit, yedi tarih override toplu kabul testi bekliyor.

## Siradaki tek is
FootyStats TUR1/BEL1 2025-26 + 2026-27 match CSV xG alanlarini ve indirme/lisans sartlarini; Sportmonks match xG API kapsam ve maliyetini resmi dokumanla denetle. Sonra uygun degilse eksik maclarin somut Excel listesini kullaniciya sun.
