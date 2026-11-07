# Futbol Analiz Makinası 2.6.3 — NEW100 mühür + mobil devir sözleşmesi

7 Kasım 2026, Türkiye saati. Deney dalı: experiment/263-toplu-karsilastirma. main değişmez.

## Temel kanıt
Üç gerçek maçın ayrı acceptance3 mühendislik kohortunda resmî kimlik, orijinal matematik, SHA mühür, PAS karar, GitHub push, birebir telefon ekranı zinciri başarılı: run 42358492713. Bu üç maç 100 maçlık ileri pilota katılmaz. Eski 96 aday dosyası ve 6 Kasım'daki dört pilot kayıt korunur.

## Yeni 100 ileri pilotu
- Yalnız kullanıcının açıkça adlandırdığı maçlar için yeni experiments/263/sabah_requests/*.json dosyasının deney dalına ADD olarak gönderilmesiyle başlayan GitHub push iş akışı: .github/workflows/263-sabah-new100-on-request.yml. Otomatik maç seçici yok.
- Şema örneği: {"schema":"SABAH_TOPLU_V1","day_turkey":"2026-11-07","matches":[{"league":"TUR1","home":"Ev","away":"Deplasman"}]}. İsimler örnektir; gerçek maç oldukları iddia edilmez. Saat ve takım ID kullanıcıdan tahmin edilmez. Gün Türkiye saatiyle eşleşmeli, sabah pencere 05:00–12:59.
- Yeni git push ulaşılabilirliği ayrı no-op experiments/263/sabah_readiness_probes/*.json dosyasıyla test edilir. Sıfır maç/sıfır pilot/sıfır oran, bu test gerçek pilot değildir.
- Resmî federasyon veya lig kaynağında açık güncel maç saati, 2026–27 sezon eşsiz takım kimliği, güncellik ve veri kabul kilitleri zorunludur. Başlamış maça tahmin kaydı yok.
- B/C2/C3/M4'ün dördü denenir. C3 ve M4 AVAILABLE ve en az üç model AVAILABLE olmalı. B veya C2 tarihsel bağlam eksikliğinde açık UNAVAILABLE; başka modelin yüzdesi ödünç verilmez. Orijinal matematik ve M4/DEV kilitleri değiştirilmez.
- Güncel oran yok: tarihsel baseline ve araştırma kararı yalnız RESEARCH_PAS. Ana/alternatif bahis yok, EV yok. Başarısız decision varsa yeni pilot dosyası geri alınır.
- Sadece forward_morning_263 altında maks. 100 yeni, mühürlü, kullanıcı adıyla seçilmiş maç kabul edilir. Başka kohorttan (forward_quad_263 veya forward_acceptance_263) aynı karşılaşma önceki kayıt olarak 100 sayılmaz; bloke edilir. Tekil yeni 100 ileri pilotu sıfırdan başlar.
- sabah_new100_commit_guard_263.py: kaydedilen rapor, gerçekten oluşan tahmin, model durumu, baseline, RESEARCH_PAS decision, telefon özeti ve tekli sayfaların SHA ve birebir çıktısını karşılaştırır. Git commit'ten hemen önce ve uzak push'tan önce kickoff'a en az iki dakika kalması gerekir.
- Git staged alanında sadece yeni forward_morning_263 kayıtları, new100 karar/baseline, batch raporu, acceptance receipt ve SHA-uyumlu mobil dosyalar ADD olabilir. Önceki mühürlü dosyalar ve main üzerinde değişiklik yasak.
- Pinnacle, iddaa, ODDSPAPI ve tüm bookmaker API anahtarları yeni iş akışında yoktur; kredi kullanımı sıfırdır. Deneysel araştırma bahis onayı değildir.
- Güvensiz eski workflow_dispatch akışı fail-closed kapatıldı; yeni push yolu güvenilir tetikleme olarak seçildi. Deney dalında workflow_dispatch butonunun gerçekten kullanılabildiği kanıtlanmadığından aktif yöntem olarak önerilmez.

## Pilot başlatma şartı
Kullanıcı yeni maçların isimlerini açıkça belirtmeden rastgele gerçek maç ya da geçmişte analizi yapılmış maçlar 100 pilota eklenmez. Sıradaki gerçek kayıt için kickoff'tan önce yeni manifest, resmî kaynak, kabul edilmiş veri ve kalıcı GitHub SHA/mobil receipt gerekir. Başarı sayısı yalnız uzak GitHub'da gerçekten mühürlü yeni forward dosyası olan maçlardır.
