# 2.6.3 — 7 Kasım 2026: önceden seçilmiş 44 maçın TAMAMI hesaplandı

## Dondurulmuş liste değişmedi
Kaynak: experiments/263/local_leagues/2026-11-06_09_10_league_date_only_candidates.json.
7 Kasım için 44 aday (10 lig). Hiçbiri silinmedi, maç ismi değiştirilmedi, geçmişe dönük 100 maçlık pilot tahmini yazılmadı.

## İki farklı kaynaktan iki ayrı araştırma hesabı
1. **Canlı resmî HTML + 2026/27 canonical ID**: 26/44 otomatik doğrulanan kaynak/maç kimliği. Resmî sitelerde DFL Bundesliga tarih tablosu, LaLiga yayın fikstürü ve TFF Göztepe–Başakşehir tek maç sayfası okuyucusu düzeltildi. 130/130 test başarılı. Canlı named gate 26/26. Resmî kaynak kanıtı: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42362421048 . Bu 26 maçın salt okunur gerçek B/C2/C3/M4 sonuçları: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42362653810 .
2. **Web üzerinden insan incelemeli resmî kaynak, GitHub HTML'de bağımsız tekrar doğrulanmamış**: ENG2 11, POR1 3, BEL1 4 = **18/44**. Bugün EFL resmî maç merkezi, Liga Portugal 11. hafta resmî saat duyurusu ve Pro League resmî takviminde eşleşme, ev/deplasman sırası ve UTC saatleri insan tarafından kontrol edildi. Kaynak sınıfı HUMAN_WEB_OFFICIAL_ATTESTATION_NOT_MACHINE_REVERIFIED. Bu 18 maç için sadece silinen geçici dizinde orijinal B/C2/C3/M4 matematiği kullanıldı; GitHub resmî sayfayı kodla bu çalışmada yeniden okumadı. Gerçek run: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42363140860 (18/18 EXPERIMENTAL_PASS, no betting).

## Değerlendirme
- 44/44 müsabaka için matematiksel çıktı var.
- **43/44**, en az üç model AVAILABLE + C3/M4 AVAILABLE eşiğinde.
- **PSG–Troyes:** C3/M4 çalıştı ama B/C2 yetersiz olduğundan 2/4 ve seçim EŞİĞİ ALTINDA; yüksek ham/kalibre yüzdeyle ana seçim gibi sunulmaz.
- Her karşılaşma için 1-X-2, KG ve 1.5/2.5/3.5 Üst olasılıkları, varsa model bazında ayrıdır.
- Kalibre edilen **tekli MS pazar yönleri**, normalize 1-X-2 toplama zorunluluğu olan bir dağılım değildir. Diğer gol/KG gösterimleri ham model medyanıdır, kalibre ana tercih veya EV değildir.
- Oran/API çağrısı = 0, bahis onayı = YOK, karar = RESEARCH_PAS.
- İlk 11'in sayısal değerlendirmesi henüz yapılmadı, erken saatli maçlarda KO öncesi son kontrolden bağımsız bahis kararı yok.
- Yeni100 **0/100**, dört eski 96-pilot kaydı ve üç acceptance3 mühendislik kaydı değişmedi. Önceki mühürler korunuyor.
- DFL/BEL/POR/ENG2 yayımladığı fikstürleri değiştirebilir; web ile insan incelemeli 18 maç, **resmî otomatik doğrulama tamamlanmadan kalıcı ileri pilotun VERIFIED kapısına terfi ettirilmez**.

## Kalıcı sonraki adım
EFL, Liga Portugal ve Pro League'ın JS ağırlıklı HTML/API takvimlerini makinede gerçekten ayrıştırabilecek bağımsız otomatik kaynak okuyucularını geliştirmek. 44 maçı kapsayan listeyi asla 26'ya indirme. Fikstürü ve takım ID'si güvenilir olsa dahi bağlamı eksik modellerin yüzdesini uydurma. Geçmiş maçları ileri tahmin olarak yeniden kaydetme.
