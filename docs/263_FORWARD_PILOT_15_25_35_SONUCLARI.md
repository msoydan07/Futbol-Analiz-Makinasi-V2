# 2.6.3 — İleri pilot sonucunda 1.5 / 2.5 / 3.5 gol bazında tam ölçüm

4 Kasım 2026. **Sadece test verisi ve ileri pilot sonrası skorlayıcı** güncellendi; eski tahminlerin SHA'sı, 4.413 arşiv, 4.518 kabul edilmiş kaynak ve B/C2/C3/M4 matematik motorları sabittir.

`experiments/263/evaluate_quad.py` artık her gerçek sonuç için BTTS ve `OVER_1.5`, `OVER_2.5`, `OVER_3.5` Brier/logloss ve kalibrasyon dağılımını ayrı ölçer. Aynı maç sonucu üç gol çizgisinde farklı işaretlenir; sonuç bulunmuyorsa hiçbir pazar için gerçekleşme yazılmaz. Alt çizgileri 1−Üst biçiminde okunur.

`experiments/263/test_evaluate_quad_goal_markets_263.py` sentetik maçlarla, arşivi yeniden hesaplamadan **7 test** yürütür. Testlerin başarısı gerçek tahmin isabeti veya ROI kanıtı değildir.

Önceki M4 model sabitliği 4413 tarihsel maç ile defalarca test edildiğinden, `.github/workflows/263-m4-quad-batch.yml` yeni iş başına mevcut model değişiklikleri için eski ağır testi korur; yalnız sonuç skorlayıcısının değiştiği commit'lerde ağır modeli yeniden çalıştırmaz. Manuel workflow_dispatch bir model kabul talebidir; eski model testi çalışır.

Ana tercih / alternatif / PAS gerçek sonuç değerlendirmesi henüz tekil odds kararıyla bütünleştirilmiş resmî pilot değildir. İlk gerçek B/C2/C3/M4 T−60 kayıtları ve kaynağı doğrulanmış fiyatlar geldiğinde o değerlendirme veriyle yapılacaktır; simüle edilmiş bahis geliri üretilmez.
