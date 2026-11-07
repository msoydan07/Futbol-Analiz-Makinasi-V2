# Futbol Analiz Makinası 2.6.3 — NEW100 pilot hattı, 7 Kasım 2026 kabul raporu

## 1. Kesin kanıtlanmış sonuçlar
- Toplu offline kod kabulü: **105/105 test geçti**, run https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42359385799 .
- Bu test; yeni100 kohortu için 100'lük limit, M4/C3 zorunluluğu, B/C2 eksikliklerini başka modelden doldurmama, karar/baseline/mobil SHA uyumu, kickoff sonrası kayıt engeli, başka kohortun aynı maçını saymama, hiç oran API'si çağırmama ve isim verilmeyen maçların otomatik seçilmemesi koşullarını kontrol etti.
- Gerçek GitHub push tetikleme: **SUCCESS**, run https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42359442872 .
- İş akışı gerçekten yeni experiments/263/sabah_readiness_probes/20261107_no_matches_no_credit.json ADD commit'i 509afbc0e67e3705a595dee433d6fcd86dbfecdd üzerine tetiklendi. Ayrıştırma türü = readiness_only. Matematik, kalıcı pilot mühürleme, Pinnacle ve diğer bookmaker adımları **skipped**. Başka maç seçilmedi. Aynı iş akışının otomatik gerçek kullanıcı manifestli kayıt kısmı ayrıca gerçek pilot maçıyla doğrulanmalıdır.
- Repo dalı araştırma: experiment/263-toplu-karsilastirma. B/C2/C3/M4 matematikleri, M4/DEV kalibrasyon kilitleri, 96 tarih adayı, ana main dalı ve önceki 3 acceptance mühendislik kayıtları korunur.
- 7 Kasım denetiminde forward_morning_263 altında **0 yeni pilot kayıt**; eski forward_quad_263 altında 4 kayıt; ayrık forward_acceptance_263 altında 3 kayıt. Readiness çalışması bunlara hiç kayıt eklemedi.

## 2. Uygulanan mühendislik
- Yeni push tetikleyicili iş akışı: .github/workflows/263-sabah-new100-on-request.yml .
- Aynı gün TSİ 05:00–12:59; sadece tek yeni ADD experiments/263/sabah_requests/ adlı kullanıcı adlandırılmış JSON manifesti kabul edilir. Yalnız kullanıcı açıkça adı verilen maçlar, mevcut canonical 2026–27 takım/lig kimliği ve canlı resmî KO kapısından geçer.
- Yeni100 dosyaları yalnız forward_morning_263 içinde. Başka kohortta daha önce mühürlü aynı karşılaşma yeni100'e kopyalanmaz veya o pilot sayacına yazılmaz.
- Üç aşama: (1) resmî kaynak/takım kimliği + orijinal B/C2/C3/M4 + aynı-as-of araştırma baseline/kalibrasyon; (2) kodda ve Git'te çift kontrol: sahte/eksik model, ayrı SHA karar, pre-KO T−2 güvenliği, tekli/toplu mobil byte-for-byte kontrolü; (3) yalnız ADD kaydı + Git commit/push + uzak ref dosyası kanıtı.
- En az üç model AVAILABLE, C3/M4 zorunlu; B veya C2 "unavailable" gerekçesiyle bırakılabilir ve o maçta başka modelin yüzdesi doldurulmaz.
- Oran kullanılmaz, karar RESEARCH_PAS; Pinnacle ve diğer bookmaker secret'ları yeni workflow'da yok. Eski manual workflow_dispatch dalı fail-closed olarak kapatıldı, yeni push yolu doğrulandı.
- Kabul edilen insan kaynak statüsü yalnız sınırlı deneysel araştırmadır; 4518 maçın tamamının tek tek bağımsız doğrulandığı anlamına gelmez.

## 3. Açık kalan gerçek kabul
**İlk kullanıcı adlandırmalı yeni100 maçı henüz girilmedi.** Hazırlık testi gerçek model/mobil Git SHA zincirinin yeni100 kohortunda üretimden sonra Git'e push edildiğini kanıtlamaz. O son sınav için kullanıcı tarafından adı verilen, canlı resmî kickoff'u henüz gelmemiş bir maçla yeni experiments/263/sabah_requests/YYYYMMDD_istekNN.json ADD edilmelidir. Kayıt başarı ilanı sadece GitHub run SUCCESS ve uzak dalda SHA-uyumlu forward_morning_263 dosyasıyla yapılır.

Kullanıcı maç/başlama saatini bilsin veya maç adını versin; sistem saati resmî kaynaktan kendi doğrular. Adayları otomatik pilot yapma, geçmiş maçlardan ileri tahmin uydurma ve önceki mühendislik kayıtlarını 100 pilotuna transfer etme YOK.

## 4. Tek eylemlik iş defteri
- **Son doğrulanmış başarı:** 105/105 offline + 0-maç no-api yeni100 push route SUCCESS.
- **Açık eksik:** 1. gerçek yeni100 named-match kayıt/push/mobile kabulü yapılmadı.
- **Sonraki tek eylem:** İlk açık isimli maç geldiğinde yeni manifesti ekle; gerçek run'ı incele; güncel maç durumuyla ilgili engel varsa tek raporla açıklayıp model/çıktı uydurma.
