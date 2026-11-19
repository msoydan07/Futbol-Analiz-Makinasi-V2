# 20 Kasım 2026 — D-MARKET-006 oran yalnız beşinci referans: uygulama ve kabul

## Önceki kilitli kullanıcı kararları (DEĞİŞMEDİ)
- `D-ODDS-001`: **iki iddaa.com PDF, tek sabah SHA tahmini ve tercihi**. İkinci PDF yalnız fiyat hareketi + kanıtlı XI/taktik yorumu; yeni tahmin veya seçim YOK.
- `D-MARKET-006`: iddaa/Pinnacle veya diğer piyasa oranları B/C2/C3/M4 model yüzdelerini, **ana tercih/alternatif/PAS** kararını DEĞİŞTİRMEZ; fiyatlar beşinci karşılaştırma referansıdır.
- 20 Kasım pazar uzmanları: **MS tek M4 1/X/2**, **KG ve 2.5 Alt/Üst C3**. M4'nin Ağustos önceden dondurulmuş joint Poisson kalibrasyonu yalnız **MS** için; C3 KG/2.5 henüz **ham/kalibre edilmemiş** olasılıktır ve raporda bu ayrım açık gösterilir. C3 uygun değilse işaretli M4 fallback; mühürlü modellerin denklemlerini değiştirme YOK.

## Kod — birleştirilen değişiklik
- **Mevcut tek komut ilk PDF girişine yönlendirme**: `experiments/263/iddaa_pdf_one_step_263.py` artık `model_first_iddaa_bridge_263.calibrate_session` çağırır, eski `iddaa_pdf_value_bridge_263` ile EV/odds bazlı karar yolunu **çağırmaz**.
- `model_first_decision_263.py`: SHA'lı forecast + aynı as-of baseline ile seçimi **fiyat argümanı olmadan** oluşturur; M4 MS üçlü vektörü tek normalleştirilmiş ortak dağılımdan gelir, C3 KG/O25 çiftleri kendi içinde toplam 1. İki pazar ailesi aynı anda seçilmez; ana + en fazla bir alternatif veya model-only PAS; teknik eksik ayrı engel.
- `model_first_selection_lock_20261120.json`: kilitli önceki M4 tarihsel politikayı yeniden yazmadan, yeni aile uzmanları / model-only eşikler için ayrı tam SHA'lı araştırma kilidi. **Yeni fit ve Ekim/Nov sonuçlarına göre gizli eşik ayarı yok**. Eski research lock dosyası değiştirilmedi.
- `model_first_iddaa_bridge_263.py`: model-only SHA kararını **önce** oluşturur; orijinal 1. PDF, takım kimliği, resmî fixture, SHA ve zaman eşleşmesinden **sonra** ayrı MARKET SHA referans raporu yazılır. Eksik fiyat grubu yalnız `NO_COMPLETE_GROUP`, model-only PAS sebebi değildir. Fakat PDF satırı/lig/kickoff/yön/SHA veya fiyatın sonradan oynandığına dair kanıt çelişkisi = **TEKNİK ENGEL**, sahte eksik fiyat gibi gizlenmez.
- `iddaa_pdf_report_263.py`: MS=M4, KG/O25=C3 uzmanını ve ham/kalibre ayrımını gösterir; eski fiyat-temelli kayıtları yalnız tarihsel denetimde okuyabilir, yeni ilk PDF o kayıtlardan üretmez.
- `iddaa_pdf_last_review_263.py`: eski son-PDF kodu araştırmadan aynı operasyon dalına taşındı; ilk sabah SHA'yı asla değiştirmez, ikinci PDF'de yeni piyasa-değer kararı ve model eğitimi yok.
- Eski `four_model_value_policy_263.py` ve `iddaa_pdf_value_bridge_263.py` **silinmedi**: önceki araştırma/odds değeri karşılaştırmalarının eski kanıt ve testleri için tutuldu. Bunların EV-gated sonucu **geçerli D-ODDS-001 karar motoru DEĞİLDİR**. Farklı tarihsel Pinnacle/new100 araştırma rotalarının hepsinin otomatik olarak yeni PDF model-first uygulaması olduğu İDDİA EDİLMEZ.

## Gerçek test kanıtları
- GitHub Actions: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44629695510 — başarılı.
- Birim: 18 fiyat bağımsız model güvenliği + 5 iddaa PDF model-first köprü + eski fiyat-köprüsü ve sabit-uzman geriye uyumluluk + PDF raporu/tek komut ve 2. PDF **sentetik** güvenlik testleri geçti.
- **40 eski SHA-mühürlü 8 Kasım tahmin kaydını salt-okunur replay**: 40/40 v2 model-only seçici başarı; **19 araştırma adayı / 21 model-only PAS**. M4 MS vektör toplamı 1, C3 KG/2.5 ailesi kullanıldı. Tek bir fiyat bile gerekmiyor. **0 eski mühür değişikliği, 0 yeni gerçek pilot, 0 model matematiği değişikliği**.
- Yeni `market_reference` piyasa fiyatı değişince kendi SHA'sını değiştirir; model karar SHA'sı, main/alternatif/PAS değişmez.
- Kullanıcının güncel gerçek iddaa PDF'si, aynı gün resmî fixture ve ikinci PDF ile **henüz uçtan uca saha kabulünden geçmedi**. C3 KG/O25 olasılık üstünlüğü kanıtlı kesin değil; model-first adayları bahis/kârlılık onayı değildir.

## Durum protokolü
A — **KARAR KİLİTLİ**. B — **Deney dalında kodlanıp CI ile doğrulandı**. C — **Gerçek iki PDF saha kabulü bekliyor**.
**Bir sonraki tek oran işi:** İlk gerçek kapsam ligi iddaa.com sabah PDF'si geldiğinde yeni sabah SHA ve 5. referansı gözlemle; aynı gün ilk 11 sonrası ikinci PDF'de yalnız yorumu doğrula. Eski odds-gated model seçimini yeniden açma; yeni Pinnacle ücretli API/scraper araştırması BAŞLATMA.
