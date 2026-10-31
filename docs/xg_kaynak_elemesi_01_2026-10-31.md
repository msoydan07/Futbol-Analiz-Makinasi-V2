# Eksik xG arastirmasi — kaynak eleme raporu 01

Tarih: 2026-10-31. Durum: MASA BASI KAYNAK DOGRULAMA. Henuz yeni xG kaydi eklenmedi.

## Kilitlenmis kullanici kararlari
- Once 2025-26 ve 2026-27 tarihsel verileri bul, kaynagi dogrula ve GitHub'da kalici sakla.
- Haftalik guncelleme, cron, otomasyon, zamanlama, manuel haftalik giris su an YASAK KAPSAM; tum veri ve matematik calismasi bittikten sonra degerlendir.
- Otomasyon sonradan mumkun olmazsa kullanici haftada bir elle yuklemeye hazir.
- Her testte hipotez, beklenen sonuc, kanit; ayni degisiklik olmadan ayni testi tekrarlama. Bes ligi toplu yonet.
- Tahmini xG veya takim sezon toplami, gercek tekil mac xG'si olarak kabul edilmez.
- Tek mac analizinde ilk 11 aciklanmamis olmasi tum analizi engellemez. Ilk yari korner kapsam disi. Oranlar son asama.

## Kaynak arastirmasi 01 — bulgular
| Kaynak | Dogrulanan | Sinir / sonraki karar |
|---|---|---|
| https://openfootapi.com/docs | Starter ucretsiz 5000 istek/ay: fixtures, standings, search. Developer xG shot maps: ucretli ve desteklenen musabakalarla sinirli. | Bes eksik ligin match-level tarihsel xG'si oldugu kanitlanmadi. XG icin simdilik ELENDI. |
| https://openfootapi.com/ | Developer paketinde xG top-5 Avrupa ligleri icin belirtiliyor. | Eksik 5 lig icin xG varsayilmaz. |
| https://github.com/v-eatpizzanot/soccer-dataset | 128746 xG bulunan fixture beyan ediliyor; provider xG degeri sut bolgesi formuluyle tahmin, shot-quality degil. Dataset tum liglerde es kapsamli degil. | GERCEK SHOT-BASED xG havuzuna ekleme. Farkli ozellik veya kalite testi adayi. Lisans ve upstream izinleri kontrol edilecek. |
| https://github.com/oladeeayo/open-matchday | 2026-27, 75 lig, mac sonuc/sut/korner/kart. Dokuman acikca xG yok diyor. | Yedek sonuc kaynagi; xG icin ELENDI. |
| https://sportsdatastack.com/leagues/ | Championship, Eredivisie, Primeira Liga icin xG kaynak listeleri var. | Kaynak kesfi adayi; link verilen saglayicilar tek tek kanitlanmali. |
| https://github.com/withqwerty/football-docs/blob/main/docs/free-sources/understat.md | Understat bes buyuk lig icin mac bazli xG ve sut verisi. | Mevcut bes lig hattini surdur; eksik diger bes lig icin genisletilemez. |

## Sonraki TEK is
Kaynak rehberindeki somut saglayicilari, ozellikle Championship, Eredivisie, Turkiye, Portekiz, Belcika icin **2025-26 ve 2026-27 match-level home/away xG** ornegi ve erisim kosullariyla denetle. Kabul edilen kaynaktan once 10 maclik bagimsiz pilot, sonra iki sezon toplu kayit. Tek GitHub kabul testi. Simdi otomasyon yok.

## Durum defteri
- Son basarili dogrulanmis xG: 2148.
- Yedi tarih override degisikligi var; yeni kabul testinde dogrulanmadi.
- Bes ligde 2025-26/2026-27 gercek xG kaynak acigi devam ediyor.
- Yeni xG veri satiri eklenmedi.
