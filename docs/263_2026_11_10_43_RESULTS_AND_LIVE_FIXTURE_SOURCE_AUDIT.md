# 2.6.3 — Son 43 skor araştırması + canlı fikstür kapısı | 10 Kasım 2026

## Arşiv/Veri
- Kullanıcı isteğiyle 99 geçmiş maçın sonuç arşivine girişi daha önce tamamlandı: 4.518 + 99 = 4.617. 99 sonuç aslında tarih, iki takım kimliği ve gol skorlarıyla çelişkisizdi.
- Geriye kalan 43 kayıt **yeniden maç olarak eklenmedi**. Her biri için lig, tarih, ev/deplasman, son skor ve resmi/klüp kaynak URL'si içeren **ayrı kanıt kaydı**: `data/results_only_263/43_primary_public_score_review_20261110.json`.
- 43/43 kayıt, özgün 99'luktaki aynı dört-tupla ve skorla birebir eşleşiyor; kaynak URL alanı yalnız beklenen lig/kulüp resmî ana makinelerinden. Portekiz 8/8 için tek maçın skorunu açıkça bildiren resmî Liga Portugal video URL'leri vardır (Vitória SC 1-2 Porto dahil).
- Kaynak kanıtları 10 ENG1, 15 ENG2, 10 BEL1, 8 POR1 olarak gruplandı. Toplu haber veya maç özeti sayfası ile doğrudan maç ID belgelemek aynı iş değildir.
- [Resmî kaynak bağlantısı, 99 skor arşivi ve SHA uyumunu kontrol eden 7/7 CI](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42822335142) başarılı. CI internet sayfa gövdelerini çekerek her maç skorunu denetlediğini iddia ETMEZ.
- [43 resmî kaynağın sayfa gövdesini gerçek tarayıcıyla okumayı deneyen yeni bağımsız ağ denetimi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42822967974) (sonuçları GitHub artifact içindedir; başarı durumunu ayrıca kontrol et).
- Eski 4.518 CSV'nin SHA'sı `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9` aynı.
- 4.617 eğitim sonuç CSV'nin SHA'sı `637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89` aynı. 9 eski ENG2'nin istatistik satırları sessizce değiştirilmedi, 99 yeninin eksik ayrıntı alanları modelde uydurulmadı.
- [4.617 veriyle 10 ligin hepsinde M4/B/C2/C3 ve tarih kesiti testleri 9/9](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42819330391), başarılı. Eski tahmin mühürleri ve matematik parametreleri aynı.

## Bugünkü canlı fikstür kanıtı (gerçek tarayıcı, kesin 10.11.2026 — 17.11.2026)
- [Gerçek sayfa erişimi ve üç hassas lig için sıfır/tarayıcı sınıflandırması CI](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42822293468) başarıyla yürütüldü (offline regresyonlar + live-source-diagnostic).
- ENG2 resmî `efl.com/competitions/efl-championship/`: HTTP 200, gerçek önümüzdeki 7 gün **0** doğrulanmış maç; yalnız **21–22 Kasım 2026 gibi ileriki tarihler** için alternatif zaman penceresinde 12 maç kartı ayrıştırılabildi. Bunlar bugünden yedi gün içinde değildir ve **tahmin olarak mühürlenmedi**.
- POR1 resmî `ligaportugal.pt/calendar`: HTTP 200, gerçek önümüzdeki 7 gün **0**; yalnız 28–30 Kasım gibi daha uzak günlerin test penceresinde 6 maç kartı ayrıştırılabildi. Bunlar **canlı geçerli tahmin veya önümüzdeki 7 günlük maç değildir**.
- BEL1 merkezî `proleague.be/fr/jpl-calendar` ve `nl/jpl-calendar`: HTTP **403**; kulüp kaynakları `kvmechelen.be`, `krcgenk.be` erişilebilir (200) fakat bu gerçek 7 günlük pencerede benzersiz tarih + takım + KO kartı sağlanamadı. Bu 0 maç iddiası değil, **kaynak engeli**.
- ENG1 resmî Premier League'in [21 Kasım'daki maçları duyuran fikstür bülteni](https://www.premierleague.com/en/news/4725574) uluslararası ara sonrası yeni turu gösterir. Bugün 10 Kasım iken 21 Kasım 7 günlük tahmin penceresi dışında.
- Belgede yer alan kaynak erişimiyle **gerçek tarih ve skor öncesi tahmin mührü** aynı iş değildir. Bugün uygun yedi günlük resmi fikstür tanığı olmayan lig için sahte bir 10 Kasım maçı/başlama saati/tahmin kaydı üretmek yasaktır.

## Kapanış sınırı
Maç sonuçlarının arşivde kayıtlı olması ve kaynak bağlantısı bulunması tamamlanmış iştir. Resmî sağlayıcıdan **tekil maç kimliği + gövde skoru** bağımsız otomatik kontrolü her maçta kanıtlanamadıysa bu kısmı "tam resmî sertifikalı" yazma. Resmî tarih+KO geçidi olmayan bir maç için canlı tahmin mühürlenemez. Kaynakların erişim engelleri aşılmadan onay iddiası yerine sağlam hata kodları tutulur.
