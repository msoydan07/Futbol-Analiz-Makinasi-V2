# Eksik gercek xG veri kaynagi arastirmasi — 2026-10-31

## Hedef
2025-26 ve 2026-27 sezonlari, ENG2, NED1, TUR1, POR1, BEL1; 2.265 eksik macin kaynak bazli tamamlama plani. Kaynagi, lisansi, mac seviyesi xG ve tarihsel kapsam kanitlanmadan veri birlestirilmeyecek.

## Adaylar ve karar
| Kaynak | Bulgular | Karar |
|---|---|---|
| https://xg.football/competitions/netherlands-eredivisie/seasons/2025/xg | Eredivisie 2025-26 icin 304 macin xG verisiyle hazirlandigi belirtilen tablo; gorunen tablo takim toplamlaridir | ADAY: tekil mac bazli ev/deplasman xG ve indirme hakki dogrulanmali |
| https://matchdaysync.com/stats/expected-goals | 2026-27 icin bes eksik ligin tumunu xG siralamasinda listeliyor | ADAY: tekil mac ve gecmis sezon disari aktarma/lisans kontrolu |
| https://openfootapi.com/docs | Eredivisie, Portekiz, Turkiye, Belcika; xG/shot map endpointleri tanitiliyor | ADAY: ucretsiz kota, 2025-26 kapsami, ticari/otomasyon izni ve fixture ID test edilmeli |
| https://footballxg.com/xg-league-tables/ | 50+ lig; Excel indirmeleri uyelik gerektiriyor, provisional xG olabilir | KOSULLU/UCRETLi: bedava tam veri olarak varsayilamaz |
| https://www.sportsdatavault.com/en/data/ | 2025-26 ve 2026-27 sezon arsivleri xG tablolarini listeliyor; sezon basina ucret var | UCRETLi: kullanici onayi olmadan satin alma yok |
| https://github.com/oladeeayo/open-matchday | 75 lig sonuc/korner/kart/sut verileri, xG kolonu tanitilmiyor | YEDEK SONUC KAYNAGI, xG degil |
| https://github.com/openfootball/europe | Acik lisansli mac sonuc ve fikstur verisi | YEDEK SONUC KAYNAGI, xG degil |
| https://github.com/TopMarx/eredivisie | xG alanlarinin Opta lisansi nedeniyle cikarildigini acikca belirtiyor | xG ICIN KULLANILMAZ |

## Kabul kapisi
1. Kaynak gercek match-level xG_home/xG_away dondurmeli; takim sezon toplami veya modelimizin tahmini degil.
2. Sezon, lig, tarih, takimlar, skor, ev/deplasman yonu ve kaynak URL'si dogrulanmali.
3. Lisans ve erisim izni acik olmali; engelli endpointlere dolanma yok.
4. Bir pilot ligden en az 10 rastgele mac kontrolu + ayni mac icin varsa ikinci kaynak karsilastirmasi.
5. Once 2025-26, sonra 2026-27; iki sezon tek veri semasina alinir, tarihsel tahminlerde gelecek mac sizintisi yasak.
6. Yalnizca gecmis macin bitisinden sonra yayimlanan xG sonraki maclarin tahmininde kullanilir.
7. Gecmeyen veri `UNVERIFIED_XG` olarak karantinada kalir; verified toplam degismez.

## Sonraki somut adim
OpenFoot API ve MatchDaySync icin mac seviyesinde gercek xG erisim/lisans testi; uygun olanla tek lig pilotu, sonra toplu bes lig entegrasyonu. Yedi mevcut tarih istisnasi tek denetim kosusunda kontrol edilecek. Kullaniciya simdilik manuel is yok.
