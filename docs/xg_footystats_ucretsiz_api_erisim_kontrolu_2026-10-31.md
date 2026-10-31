# FootyStats ucretsiz API erisim kontrolu — 2026-10-31

## Resmi belgeler
- https://footystats.org/api/documentations/setup-the-api : example key ile Ingiltere Premier Lig 2018-19 (season_id 1625) ornek test.
- https://footystats.org/api/documentations/try-all-endpoints : 2024-25 Premier Lig (season_id 12325) ornekleri.
- https://footystats.org/api/documentations/league-list : sezonlara ozel ID; league-list endpoint.
- https://footystats.org/api/documentations/match-schedule-and-stats : league-matches endpoint; match-level istatistikler.
- https://footystats.org/api/documentations/faq : xG kapsami ligden lige degisir, tarihi veri her ligde ayni degil.

## Dogrulama
- API ornek adreslerini bu ortamda acma denemesi basarisiz (erişim hatasi). Gercek JSON okunamadi.
- TUR1/BEL1 2025-26 ve 2026-27 match-level xG, ucretsiz example key ile **DOGRULANAMADI**.
- Hedef sezon ID'leri, doluluk orani, maliyet ve izinli test erisimi **DOGRULANAMADI**.
- Bu sebeple API'den yeni xG kaydi yok; 2148 verified degismedi.

## Sonraki tek is
admin@footystats.org adresine hedef dort lig-sezon icin xG coverage, deneme endpoint erisimi, lisansli private storage, fiyat ve bos deger yuzdesi sorularini iletmek. Kullanici onayi olmadan disariya e-posta gonderilmedi; ucretli abonelik baslatilmadi.
