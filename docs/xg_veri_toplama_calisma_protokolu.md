# xG veri toplama calisma protokolu

Kullanici onayi: 2026-10-31

## Kesin is sirasi
1. Eksik 2025-26 ve 2026-27 mac bazli gercek xG kaynaklarini bul.
2. Kaynaklarin erisim, lisans, mac/sezon/lig kapsamini denetle.
3. Mac kimligi, tarih, skor, ev/deplasman yonu, xG degerlerini bagimsiz dogrula.
4. Dogrulanan verileri GitHub kalici veri dosyalarina yaz; ham kaynak, kaynak URL'si, cekilme tarihi ve dogrulama durumunu sakla.
5. Kalan eksikleri ayri envanterde tut ve alternatif kaynakla tek seferlik arastir.
6. Tamamlanan veri havuzunu tek kabul testinden gecir; sonra matematik modelini kronolojik backtest ile denetle.
7. **SADECE TUM BU ISLER BITTIKTEN SONRA** haftalik guncelleme/otomasyon konusuna gec.

## Sinirlar
- Simdilik cron, haftalik workflow, otomatik yenileme, zamanlama veya kullanicidan haftalik manuel veri girisi kurulmayacak.
- Otomasyon mumkun olmazsa kullanici haftada bir, belgelenmis basit manuel veri yukleme/girme yapmayi kabul ediyor; bu son asama.
- Sohbet hafizasi veri deposu degildir; kalici dogrulanmis veri GitHub'da tutulur.
- Tahmini xG gercek xG gibi yazilmaz.
- Tekrarlanan test dongusu yok: once hata/hipotez/degisiklik, sonra tek toplu test.
- Once mevcut veri havuzunu tamamla, sonra tahmin sistemini ve en son otomasyonu ele al.
