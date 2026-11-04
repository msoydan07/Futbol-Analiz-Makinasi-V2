# 2.6.3 — Maç sonrası gol çizgileri kapsam düzeltmesi

4 Kasım 2026 — mevcut kodun denetiminde saptanan eksik: manuel oran alımı ve ana/alternatif/PAS kararında **1.5, 2.5 ve 3.5** tüm gol çizgileri destekleniyordu; fakat maç sonu piyasa-model ikili Brier/logloss değerlendirmesi yalnız **2.5** çizgisini izliyordu.

Bu değişiklik hiçbir ön maç tahminini, parametreyi, kalibrasyonu veya pilot kaydını değiştirmez. Mevcut `market_fifth_baseline_263.py` eşleşmiş örneklem değerlendirmesine GOALS_1.5 ve GOALS_3.5 eklendi. Bir gol sayısının aynı anda farklı çizgilerde nasıl sınıflandığı ayrı ayrı sınanır (ör. 2 toplam gol: 1.5 Üst, 2.5 Alt, 3.5 Alt). Eksik veya 10 dakikayı aşmış oranlar bireysel pazar bazında **NO_COMPLETE_FRESH_QUOTE** kalır ve model-piyasa karşılaştırmasına girmez.

Hedef: tek sentetik toplu kabul paketi **18 test** (önceki 15 + yeni 3); canlı oran, gerçek sonraki maçın başarısı veya kâr iddiası değildir. Eşleşmeyen lig/maç kayıtları ve kabul edilmiş 4.518 geçmiş satır değişmedi. İlk B/C2/C3/M4 canlı KO-öncesi örneği hâlâ gerekli. Kaynaklar manuel kontrol gerektirir; varsayılan sonuç PAS'tır.
