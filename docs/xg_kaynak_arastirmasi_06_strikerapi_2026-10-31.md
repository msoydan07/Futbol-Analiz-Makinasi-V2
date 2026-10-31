# xG kaynak arastirmasi 06 — StrikerAPI resmi dokuman denetimi

Tarih: 2026-10-31. **Veri kaydi eklenmedi; haftalik guncelleme/otomasyon yok.**

## Resmi kanitlar
- https://strikerapi.com/docs : 17 desteklenen organizasyon; EFL Championship, Eredivisie, Primeira Liga mevcut; Turkiye Super Lig ve Belcika Pro League listede yok.
- https://strikerapi.com/docs/atlas : shot location + saglayicinin kendi xG'si; Championship 2008-09, Eredivisie 2020-21, Primeira Liga 2016-17 baslangic kapsami beyan ediliyor. 2025-26 ve 2026-27 bu tarih araliklarina giriyor, fakat her macin xG dolulugu ayri dogrulanmali.
- https://strikerapi.com/docs/get-events : get_events 10 kredi; sut olaylarinda xG alani var.
- https://strikerapi.com/docs : get_shot_map 10 kredi, get_game 5 kredi, get_team_stats 5 kredi; ucretsiz 500 kredi/ay, kart gerekmiyor, API anahtari gerekli.
- https://strikerapi.com/compare/soccer-api : saglayicinin xG modeli shot-location temelli, Understat ile ayni model degil.
- https://sportsdatastack.com/tools/strikerapi/ : ucuncu taraf rehber veri icin ticari urun/model kullanimini belirli kosullarla mumkun, ham veri akisi yeniden satisini yasak diye ozetliyor; resmi Terms ayrica kontrol edilmeden GitHub'a toplu kopyalama izni varsayilmaz.

## Lig karari
| Lig | 2025-26/2026-27 xG adayi | Engel |
| ENG2 | VAR | Kayit basina xG ve lisans pilotu |
| NED1 | VAR | Kayit basina xG ve lisans pilotu |
| POR1 | VAR | Kayit basina xG ve lisans pilotu |
| TUR1 | YOK | Baska saglayici |
| BEL1 | YOK | Baska saglayici |

## Kredi tahmini (kesin fiyat degil)
2025-26 + 2026-27 tarihsel havuzda ENG2=696, NED1=396, POR1=387 mac, toplam 1479. Her mac icin tek get_shot_map (10 kredi) varsayimiyla 14790 kredi; aylik 500 bedava kredi tek ayda yeterli degil. Bu bir ust sinir planlama senaryosu: daha verimli izinli export/batch veya get_game alanlari varsa maliyet degisir. **Ucretli plan ya da satin alma kullanici onayi olmadan yok.**

## Sonraki TEK is
StrikerAPI resmi Terms ile get_game/get_team_stats cevaplarinda home/away match-level xG'nin bulunup bulunmadigini ve izinli export/batch imkanini dogrula. Ardindan Turkiye/Belcika icin farkli saglayicinin ayni sartlarini arastir. API key kullanici tarafindan gerekecekse ancak bu kanitlardan sonra iste. Pilot ve GitHub Actions henuz baslatilmayacak.

## Sabit durum
Son basarili 2148 dogrulanmis xG; 7 tarih override test bekliyor. Yeni satir eklenmedi. Otomasyon sonraki asama.
