# BASKETBOL ANALİZ MAKİNASI V1 — 09.11.2026 MÜHENDİSLİK KABUL RAPORU

**Durum:** ÇALIŞAN BAĞIMSIZ ARAŞTIRMA PROTOTİPİ. Maç öncesi canlı fikstür doğrulama, gerçek ileri SHA mühürleri, sakatlık/oyuncu, possession/tempo ve bahis piyasası karşılaştırması **henüz yok**. Gerçek parayla kullanım veya gelir iddiası uygun değildir.

## Değişmez çalışma ve veri sınırı
- Futbol 2.6.3, main, LITE, eski tahmin ve otomasyonlar değişmedi. GitHub bağlayıcısı yeni repository kurma aksiyonu sunmadığından ayrı `basketbol-v1-bagimsiz-arastirma` dalında tamamen bağımsız, taşınabilir Python paketi kuruldu.
- Kullanılan veri: NBA'nin ESPN kaynaklı arşivlerinden normal sezon final skorları (belirli SHA commitli), EuroLeague non-commercial 6.75 Analytics geçmiş normal sezon maç skorları, EuroCup EuroLeague API v2'den oynanmış normal sezon skorları.
- NBA Cup Championship maçları **normal sezon dışı** kabul edilip 2023–2026 sezonlarının veri kümesinden dışlandı (NBA type=2 olsa bile). Playoff ve play-in aynı şekilde ayrı tutulur.
- Aynı günün bütün tahminleri hesaplanmadan o güne ait hiçbir skor motor hafızasına alınmaz. Model seçimi bir önceki geliştirme yılından; sonraki, ayrılmış test yılına seçim için bakılmaz.
- İlk sürüm dört model: BASE, ELO, FORM, HYBRID. Galip ve iki farklı sayı pazarı **aynı** beklenen fark/toplam dağılımından hesaplanır.
- Test dosyaları değiştirme / sahte skor üretme / oran çekme / ücretli API / sahte bahis getirisi yok. Sonuçlar github Actions artefaktında JSON+MD.

## Gerçek test / ayrılmış sonraki sezon

| Organizasyon | İncelenen geçmiş maç | Tutulan sonraki sezon N | Önceden seçilen model | MS doğru | MS yön isabet | MS Brier | Fark MAE | Toplam sayı MAE |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| NBA | 5.059 | 1.230 (2025–26) | HYBRID | 839 | %68,21 | 0,203913 | 11,3793 | 14,9972 |
| EuroLeague | 1.398 | 380 (2025–26) | HYBRID | 234 | %61,58 | 0,224269 | 9,2373 | 13,8911 |
| EuroCup | 816 | 180 (2025–26) | HYBRID | 121 | %67,22 | 0,207794 | 11,6940 | 14,4765 |
| **TOPLAM** | **7.273** | **1.790** | — | **1.194** | **%66,70 (karma lig, ham isabet)** | — | — | — |

**Önemli:** Karma %66,70 ölçüsü sadece 1.194/1.790 = %66,70 aritmetik oranıdır; üç farklı ligin Brier/MAE'si birleştirilmez. Arşiv NBA ve Avrupa kaynakları farklı statüde, bağımsız resmi çapraz skor doğrulama yapılmış değil.

## Aynı test maçlarında BASE karşılaştırması

- NBA: HYBRID MS Brier 0,203913 vs BASE 0,247154; fark MAE 11,3793 vs 13,0979; toplam MAE 14,9972 vs 15,9070.
- EuroLeague: HYBRID Brier 0,224269 vs BASE 0,232483; fark MAE 9,2373 vs 9,6042; toplam MAE 13,8911 vs 14,6387.
- EuroCup: HYBRID Brier 0,207794 vs BASE 0,242454; fark MAE 11,694 vs 13,1000; toplam MAE 14,4765 vs 15,9191.

## Alt/Üst ve handikap — gerçek oran DEĞİL sabit araştırma çizgileri

| Organizasyon | Sabit toplam çizgisi | A/Ü yön doğru | A/Ü Brier | Sabit ev handikap | Handikap yön doğru | Handikap Brier |
|---|---:|---:|---:|---:|---:|---:|
| NBA | 224,5 | 793/1230 | 0,223401 | -4,5 | 814/1230 | 0,210931 |
| EuroLeague | 164,5 | 246/380 | 0,217810 | -4,5 | 237/380 | 0,229579 |
| EuroCup | 164,5 | 118/180 | 0,212021 | -4,5 | 118/180 | 0,217240 |

Bu çizgiler **gerçek bahis şirketlerinin maç maç açıkladığı fiyatlar veya oranlar değildir**; sabit eşiklerde dağılımın tutarlılığını görmemizi sağlayan güvenlik ölçümleridir. 2026–27 erken sezon yeniden oynatmalar: NBA 139, EL 100, EC 96; gerçek geleceği önceden mühürlü sınama değildir.

## GitHub kanıtı
- 09.11.2026 güvenli kabul ve gerçek kaynaklı toplu CI: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42630366321
- 9 offline kaynak/tarih/dağılım testi + 1 geçmişe dönük senaryo engelleme testi; tamamı **PASS**. Üç lig gerçek veriyle benchmark tamamlandı; geleceğe yönelik **resmî fikstür onayı olmayan örnek maç** hesaplaması da çalıştı.
- Kod: `basketbol_v1/sources.py`, `engine.py`, `benchmark.py`, `predict.py`; testler iki ayrı dosya, README ve yalnız bu dala ait Actions workflow.
- Kodu ayrı repo kurulduğunda taşıyabilmek için ayrıca basketbol-v1-source.zip GitHub Actions artefaktı üretilir. Bu bir günlük kullanım/ücretli bahis otomasyonu değildir.

## Teknik karar ve eksikler
- V1 **geçmiş maç istatistiksel analiz motoru** olarak kabul edildi. HYBRID mevcut 3 ligde BASE'ten daha iyi ayrılmış sezon testine sahip; diğer yöntemlere göre seçim geliştirme döneminde yapıldı. Daha güçlü veya kârlı sistemin kanıtı yok.
- **Sıradaki zorunlu işler:** 1) gerçek possession/tempo + doğrulanmış oyuncu eksikleri dahil edilebilir mi, 2) Türkiye BSL / İspanya ACB / Almanya BBL ve diğer liglerde ücretsiz izinli veri erişimi ve maç kimlikleri, 3) resmî gelecek fikstür + kickoff öncesi SHA, 4) bağımsız skor teyidi ve güncel piyasa benchmarkı, 5) güvenli bant/kalibrasyon.
- Gereksiz tekrar, sentetik başarı iddiası, oynanmamış maç için galibiyet sonucu varmış gibi kayıt, futbol sistemine müdahale yok.
