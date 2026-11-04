# 2.6.3 — Tek kabul raporu: eksik süreli maçın deneysel eğitimden çıkarılması

**Tarih:** 2026-11-04 | **Dal:** `experiment/263-toplu-karsilastirma`

**Kabul kanıtı:** [GitHub Actions #41851081895](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41851081895) — **16/16 test başarılı**, commit `8fefc21059e2a82493fb64fe136021866e4f3954`.

## Değişiklik

- `data/staged_263/2026_10_31_ned1_abandoned_awarded_exception.json`: 31 Ekim 2026, **SC Cambuur 4–0 Go Ahead Eagles**, tamamlanmadan tatil edilmiş fakat 4–0 hükmen/kesin sayılmış skor; ayrıca normal 90 dakikalık gözlem değildir. Maç sonucu **asla değiştirilmez**.
- `experiments/263/full_match_eligibility_263.py`: tutarlı lig/tarih/skor kimliği ile yalnız bu karşılaşmayı **tam süreli örnek havuzundan** çıkarır; politikanın SHA-256 değerini döndürür ve değişen sonuçta hata verir.
- `experiments/263/forward_quad.py`: B/C2/C3/M4 model eğitimi ve güncellik/sayı kontrolü aynı temizlenmiş lig örneklerini kullanır; SHA ve çıkarılan maç kimliği tahmin kaydına mühürlenir. Önce veri kaynak kabulü yine zorunludur.
- `experiments/263/forward_empirical_baseline_263.py`: liglerin 11 pazar oranlarında **aynı** dışlama uygulanır; tahminin politikasına ve kayıt sayısına ters veri kullanılırsa engeller.
- `experiments/263/test_full_match_eligibility_263.py`: gerçek staged CSV (4.501 satır, resmî 4–0 değişmemiş), bozuk skorun engellenmesi, baz oranların dışlaması, model eğitimine giren örneklerin kontrolü. Önceki baz ve birleşik akış testleriyle aynı CI'da 16 geçiş.

## Değiştirilmeyenler

4.413 orijinal arşiv, 4.501 staged CSV, 4.509 hafta sonu kaynak-artifact'ı, resmî 100-maç pilotu, M4 ayar kilidi, üretim dalı. Geçmiş 880 tahmin tekrar hesaplanmadı.

## Açık kapılar — otomatik kabul YOK

1. **Kaynak kabulü:** 4.509 satırlık güncel paket GitHub Actions #41802358251 içindeki `weekend-263-ten-league-source-evidence` artifact'ında mevcut; `HUMAN_VERIFIED_SOURCE_ACCEPTANCE` henüz verilmedi; `data/quad_accepted_263/` yok. Bu kod bu statüyü otomatik üretmez.
2. **Gerçek maç kaydı:** Kullanıcının isimlendirdiği maç için canlı resmî fikstür kapısı, maç öncesi onaylı veri ve mühürlenmiş tahmin gereklidir; bu testler gerçek maç tahmini üretmedi.
3. **Zamansal dürüstlük:** `forward_empirical_baseline_263.produce` şu anda baz kaydının `created_at_utc` alanına geçmiş tahminin saatini yazar; bu işlem sonradan yapıldığında yanlış bir oluşum zamanı izlenimi yaratabilir. Gerçek ileri pilotun son değerlendirmesinden önce kayıtların gerçek yaratılma zamanı ve pre-KO sınırı ayrıştırılmalıdır. Bu rapor zamansal kabul anlamına gelmez.

**Sonraki tek iş:** Baz kaydının gerçek oluşum zamanının güvenli şekilde muhafazası / kaynak anı doğruluğunun onarımı; ardından insan kaynak onayına dön. Aynı 16 testi gerekçe olmadan tekrar etme.
