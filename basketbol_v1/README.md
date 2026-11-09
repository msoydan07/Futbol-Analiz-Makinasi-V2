# Basketbol Analiz Makinası 1.0 — bağımsız matematik ve veri pilotu

**Araştırma prototipi, bahis tavsiyesi veya doğrulanmış kârlı sistem değil.** Futbol 2.6.3 ve LITE ile veri veya kod paylaşmaz.

## Gerçek matematik
BASE: lig ortalaması ve ev avantajı; ELO: geçmiş sayı farkına göre takım gücü; FORM: takımların yalnız **önceki maçlardaki** hücum ve savunma sayı eğilimleri; HYBRID: önceden sabit Elo+form ağırlıkları. Dört yöntemin her biri maçın beklenen sayı farkı M ve toplam sayısı T değerlerini üretir; ev/deplasman sayıları (T±M)/2, maç galibi, 0,5'li toplam sayı ve 0,5'li handikap olasılıkları aynı normal dağılım yaklaşımından gelir. Sonuçlar matematiksel belirsizlik içerir. Oyuncu, gerçek possession/tempo, kadro ve sakatlık etkisi **henüz modele dahil değildir**.

## Geçmiş veriler ve doğru sınama
NBA: ESPN sonuçlarının [roni-altshuler/nba_predictor](https://github.com/roni-altshuler/nba_predictor) kaynaklı sezonluk görüntüleri, sabit commit 2c98a8cc6beae31f425fb1380c794d598d2d74b6. 2022–23 ve 2023–24 geçmişi, 2024–25 model seçimi, 2025–26 kesin farklı sezon testi, 2026–27 erken sezon salt geriye dönük yeniden oynatma.

EuroLeague: [6.75 Analytics](https://675hoops.com/downloads/) üzerinden EuroLeague API'den derlenmiş skorlar, 2022–23 ve 2023–24 geçmişi, 2024–25 geliştirme, 2025–26 sonraki yıl testi, 2026–27 salt yeniden oynatma. Kaynak URL ve SHA-256 rapora girer. EuroLeague istatistikleri Euroleague Basketball mülkiyetindedir; üçüncü taraf paylaşımı sadece ticari olmayan araştırma kapsamında, başka kullanım için ayrıca izin koşulları gerekir. Veri dosyaları repoya kopyalanmaz.

**Zaman güvenliği:** Her günün tüm maçlarının tahmini bir önceki takvim gününe kadar gözlenmiş sonuçlarla hazırlanır. Aynı günün hiçbir skorundan diğer maça bilgi sızmaz. Sezon geçişinde takım gücü kısmen azaltılır. Dört model aynı maçların sonuçları üzerinden Brier, log-loss, galip isabeti, toplam sayı ve sayı farkı MAE/RMSE ile karşılaştırılır. Model seçimi ayrı geliştirme yılında yapılır ve ancak sonra ayrı test yılının sonucu açılır. Gelecek maçtan önce mühürlü gerçek ileri pilot **henüz yapılmadı**.

## Çalıştırma
Python 3.11+, ek üçüncü parti bağımlılığı yok.
- python -m unittest -v basketbol_v1/test_engine.py
- python basketbol_v1/benchmark.py --fail-if-empty --out /tmp/report.json --mobile /tmp/report.md

GitHub Actions: .github/workflows/basketbol-v1-backtest.yml. Ücretli veri ve oran API'si yok; bahis/EV/ROI üretilmez. Diğer Avrupa ligleri (EuroCup, Türkiye BSL, İspanya ACB, Almanya BBL, İtalya LBA, Fransa LNB, Yunanistan, FIBA BCL) veri araştırma adaylarıdır, bu sürümde desteklenmiş veya test edilmiş **değildir**.

Yeni GitHub deposu oluşturma aksiyonu bağlayıcıda bulunmadığından, geçici bağımsız araştırma dalı basketbol-v1-bagimsiz-arastirma kullanılıyor. Ana dal ve futbol deney dalı değişmedi. Daha sonra ayrı repoya taşınabilir.

## EuroCup ikinci veri kaynağı
V1.1'de EuroCup (EC) için api-live.euroleague.net kamuya açık v2 sezon oyunları uç noktası eklendi; yalnız RS, played=true, sayısal final skor, mevsim kodu, eksiksiz sayfalama ve kimlik teyidi alanları kabul edilir. Bu harici API'nin ağ üzerinden çalışma kanıtı Actions sonucuna bağlıdır. Veri lisansı EuroLeague ile aynıdır. Bu kaynak, ülke ligi olan BSL/ACB/BBL'yi desteklendi diye saymaz.
