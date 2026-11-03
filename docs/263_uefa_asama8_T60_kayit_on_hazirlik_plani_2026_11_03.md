# 2.6.3 — AŞAMA 8 / MAÇTAN 60 DAKİKA ÖNCE GÖLGE TAHMİN KİLİDİ HAZIRLIK PLANI

**Tarih:** 2026-11-03. **Durum:** SADECE HAZIRLIK; GERÇEK MAÇ TAHMİNİ KAYDEDİLMEDİ.

## Tek akış
1. Maçtan yaklaşık **T−60** dakikada UEFA resmî fikstürü, saat ve takım kimliği tekrar doğrulanır. 3 Kasım 20:45 TSİ maçları için hedef **19:45 TSİ**, 23:00 TSİ için **22:00 TSİ**. 4 Kasım 20:45/23:00 için aynı saatler. 5 Kasım 20:45/23:00 için aynı saatler.
2. Aynı anda resmî UEFA/klüp/federasyon ilk 11 ve maç kadrosu kontrol edilir; teyit edilenler kaynak URL ve kontrol zamanı ile kayda alınır. Açıklanmamışsa `NOT_ANNOUNCED`; analiz DURMAZ. Resmî kadro verisi mevcut ama doğrulanmamış sakatlık/ilk 11 bilgisi **yüzde veya λ katsayısına çevrilmez**.
3. Maç önü gol ve Elo kaynakları güncellik / SHA / tarih / sonuç sızıntısı açısından kontrol edilir. 3 Kasım sabah arşivi 4–5 Kasım maçları için otomatik güncel sayılmaz. Maç saatine yakın gelen yeni veri varsa iki gölge model aynı yeni kaynakla hesaplanır; dondurulmuş geçmiş β **değiştirilmez**.
4. 17 maçtan her biri için aynı veri kesiminde **M0_REFERENCE_ONLY** ve **M0_PLUS_ELO_EXPERIMENTAL** hesaplanır. Her kolun `lambda_home`, `lambda_away`, 1X2, 2,5 Üst ve KG Evet olasılığı ile `source_sha256`, `data_captured_utc`, `kickoff_utc`, `lineup_status`, `lineup_source_urls`, `lineup_used_as_numeric_adjustment=false`, `elo_beta_production_approved=false`, `pilot_100_matches_affected=false` yazılır. Oran/EV ve bahis seçimi eklenmez.
5. **Gerçek tahmin kilidi**, **her maç başlamadan önce** ve ancak güncel doğrulanmış kaynaklar + iki model çıktısı mevcutsa açılır. Hazırlanan kayıt `uefa_stage8_prematch_lock_guard_263.py` ile doğrulanır. Çıktı yolu `experiments/263/locked_prematch/` içinde maç ID'sine özgü olur. Dosya `open('x')` ile yalnız bir kez oluşturulur; üzerine yazılmaz. Ardından GitHub'da **commit SHA ve UTC zamanı** doğrulanır; tek başına yerel dosya üretimi değişmez GitHub kaydı sayılmaz. Repo yöneticisinin tarihi yeniden yazmasını teknik olarak engelleyen ayrı uzak depolama/koruma olmadan **mutlak değişmezlik iddiasında bulunulmaz**.
6. Maç başlamışsa **geriye dönük maç önü tahmin kaydı kesinlikle oluşturulmaz**. Maç sonrası sonuçlar, tahminler değişmeden ayrı dosyada eşleştirilir. 100 maçlık yerel pilotla karıştırılmaz.

## Mevcut kod ve güvenlik
- Yalnız deney dalı `experiment/263-toplu-karsilastirma`. `main`, B/C2/C3/M4 ve pilot değişmez.
- Kayıt doğrulayıcı: `experiments/263/europe/uefa_stage8_prematch_lock_guard_263.py`.
- Hazırlık testleri: `experiments/263/europe/test_uefa_stage8_prematch_lock_guard_263.py`.
- Hazırlık CI: `.github/workflows/263-uefa-stage8-prep-guard-only.yml`. Bu workflow **sadece sentetik testleri** çalıştırır, gerçek tahmin kaydı veya gerçek maç analizi oluşturmaz.
- Güncel resmî ilk 11 açıklanmamış olması analiz engeli değildir. Açıklanmış ilk 11'in resmi kaynağı yoksa "BOTH_OFFICIAL" yazılamaz.

## Sınırlar
Aşama 6 ve 7 veri/formül doğruluğu kanıtıdır; gerçek tahmin kalibrasyonu değildir. Elo β keşif aşamasında kalır. 17 maçın hiçbirine şu an tahmin kaydı yapılmamıştır. Hazırlık bittiğinde akşam maçlardan T−60'da kullanıcı yeniden geldiğinde yalnız maç önü veri teyidi, iki gölge hesap, kilit doğrulaması ve uzak commit kanıtı kalacaktır. **Tamamen otomatik kayıt yapan workflow henüz oluşturulmadı.**
