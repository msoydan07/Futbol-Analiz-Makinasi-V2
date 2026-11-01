# 2.6.3 C3 — deneysel ileri dönem kayıt sistemi

**Durum:** Sadece deney; üretim motoruna entegre edilmemiştir. Modül 0 yok; kullanıcı adıyla belirttiği maçı resmî kaynaktan denetler, asla kendi maç seçmez. İlk yarı korner yoktur. Bu kod tahmin doğruluğunu veya bahis avantajını garanti etmez.

## Kaynakların kilidi

- Toplu geçmiş çalışma: 01.11.2026, 4.413 tarihsel maç, 10 lig; 2026/27 **bağımsız final değil**.
- Dondurulan C3 kaynak kodu: `exp_263_batch.py` SHA-256 `1a0c519b6c8f2947de43545fcd0c5d4e8abcc9a4f8b47f8372bee43f53beb96f`. **Değiştirilmemeli.**
- Geçmiş veri arşivi: 31.10.2026 run `41251343847`, artifact `13061725424`, `historical_results.csv` SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`. Arşiv sonraki maçlar için güncellenebilir, ancak **her kayıt kendi girdi dosyasının tam hash'ini saklar**.
- Sabit ayar: C3 Ridge=6, iki lig iç/dış intercept, ayrı takım hücum/savunma katsayıları. Bu **2.6.3 §6.2'nin `k=5,w=0,5` ana modeli değil**, deneysel alternatiftir.
- Çalışma: Python 3.11+; `numpy`, `scipy` kurulu olmalı.

## Yeni maç için kullanım

1. Gerçek zamanlı veri güncellemesiyle `data/historical_results.csv` hazır olmalı (önceki mevcut veri boru hattı); model geçmiş sonuçları **tahmin gününden önceki** maçlar için okur.
2. Gerçek takım adlarıyla komut: `python experiments/263/forward_c3.py --league TUR1 --home 'Galatasaray' --away 'Konyaspor' --history data/historical_results.csv --out-dir forward_263`. **Bu bir örnek komuttur, mevcut bir fikstürün doğrulanması değildir.**
3. Program mevcut `analyze_named_match_gate.run()` üzerinden resmî fikstürü doğrular. Olumlu değilse, maç başlamışsa, 7 gün dışındaysa, kaynak 24 saatten eskiyse, veri 10 günden eskiyse veya Poisson sınırları geçilirse **hiç tahmin dosyası oluşturmaz**.
4. Geçerliyse `forward_263/YYYY-MM-DD/<fixture_hash>.json` oluşturur; `x` moduyla üzerine yazmayı **reddeder**. Her dosyada maç, kaynak, kontrol saati, kod ve veri hash'leri, C0/C1/C3 olasılıkları, `λ` ve eksik veri nedenleri vardır.
5. Git geçmişindeki yeni dosya **normal commit** ile saklanmalı; `force-push`, dosya düzenleme veya eski tarihli geriye dönük kayıt **yasaktır**. Sadece yerelde oluşturulan dosya otomatik olarak GitHub'a yazılmaz. Git geçmişi tek başına bir yöneticinin yeniden yazmasını teknik olarak engellemez; bu sistem **kurala dayalı append-only ve tamper-evident**, mutlak değiştirilemez değildir.
6. Kayıt yayınlanıp gerçek sonuç oluşana kadar kesinlikle gerçek sonuç dosyasına bakılmaz. **Üretim veya sanal bahis otomatik olarak başlatılmaz.**

## Sonuç değerlendirme (ayrı, eski kaydı hiç değiştirme)

`python experiments/263/evaluate_forward.py --records forward_263 --final-scores data/historical_results.csv --out forward_263_evaluation.json`

Değerlendirme yalnız **maç başlamadan oluşturulmuş, SHA-256 doğrulanmış** ve sonucu gerçekleşmiş kayıtları ölçer. Aynı maçta C1/C3/C0 karşılaştırılır. Önceden tanımlanan mühendislik inceleme eşiği: en az 300 ortak maç, 50 farklı gün, yeterli gözlemi olan en az 8 lig; C3 log-loss iyileşmesi ≥0,005, Brier kötüleşmiyor, tarih-blok bootstrap alt sınırı pozitif ve ≥7 ligde iyileşme. **Bu eşiklerden geçmek otomatik entegrasyon değildir; ayrıca mühendislik incelemesi gerekir.** Eşikler bilimsel olarak optimize edilmiş değildir.

## Test ve sınırlar

`C3_TEST_HISTORY=/path/to/historical_results.csv python -m unittest -v experiments/263/test_forward_c3.py` — sentetik, sahte maç/kaynak kullanarak sadece yazılım güvencesini sınar. Gerçek resmî fikstür testi değildir. Geçmiş model performansı tekrar çalıştırılmaz. Yeni bir Action oluşturulmadı. Deney dalı GitHub'ın ana dalından bağımsızdır.
