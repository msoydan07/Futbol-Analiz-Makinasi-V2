# 2.6.3 — Tek seferlik Avrupa Elo kaynak erişimi ve geçmiş sezon kanıtı

**3 Kasım 2026 — amaç:** Yeni Avrupa Elo, lig gücü, ortak rakip
modeli veya tahmin kodu kurmadan önce **gerçek, tarihsel, uluslararası
ölçekli Elo verisinin otomatik erişilebilirliğini** bir kez ölçmek.

## Eldeki kod ve geçmiş karar
- Mevcut `audit_elo_auxiliary.py` tarih sıralı yerel maç
  sonuçlarıyla her takım için `(league,team_id)` kimliğinde
  1500'den başlayan kendi Elo'muzu kuruyor. **Farklı ülkelerdeki iki
  takımın puanlarını ortak ölçek gibi kullanamayız.**
- ClubElo eski ücretsiz CSV API'si 23 Eylül 2026'da 502 hatasıyla
  raporlandı (soccerdata issue #977). Bu URL üretim kaynağı değil.
- Alternatif: https://beyondelo.com/developers, *beyondELO*; açık
  CSV dokümantasyonu, uluslararası takım Elo + rating uncertainty
  `rd`, CC BY 4.0 lisansı ve kaynak atıf şartı.
- `https://public-api.beyondelo.com/v1/datasets/club-ratings.csv`
- `https://public-api.beyondelo.com/v1/datasets/club-elo-history/2024-2025.csv`
- `https://public-api.beyondelo.com/v1/datasets/club-elo-history/2025-2026.csv`
- `https://public-api.beyondelo.com/v1/datasets/club-elo-history/2026-2027.csv`

## Bu tek işin kabul ölçüsü
Yalnız bu **4 GET** ve mevcut `identity_index_263.json`
üzerinden aday takım isim kapsaması sayılır:
HTTP 200; HTTPS adresi başka yere yönlendirilmemiş;
CSV şema `club/date/elo/rd`, güncel `as_of` ve
`country_code`; sayısal finiteness; geçmişten sezon tarih
aralığı; 2026/27 güncel CSV son 14 gün içinde olmalı.
Çıktı tek `beyondelo_elo_source_health.json` raporu.

**Kritik farklar:**
- Tarihsel dosyalardaki `date` muhtemelen puanın
  **maçtan sonra kaydedildiği** tarihtir: o gün oynanacak
  maçın ön tahminine kesinlikle kullanma. Yalnız
  `rating_date < target_match_date`; yayın anı bilinmiyorsa
  retrospektif kaynak, canlı maç öncesi kanıt değildir.
- Sırf isim benzerliğiyle canonical-ID eşlemesi
  onaylanmaz; bulunanlar `CANDIDATE_ONLY`.
- 10 ligden biri dahi dışındaysa UEFA tek maç kapısı
  değişmez: `ANALYSIS_SKIPPED_OUTSIDE_TEN_LEAGUES`.
- API erişimi başarılı olsa bile Elo'yu modelde kullanmaya
  başlama, yeni olasılık, EV, A/B/C, 100 maç pilotu ve
  `main` terfisi YOK. Ayrı doğruluk/kapsam kontrolü gerekir.
- Kaynak `beyondELO (https://beyondelo.com)` olarak
  atfedilecek; model tahmin başarısı kaynak dokümanıyla
  kanıtlanmış değildir.

**Tek seferlik GitHub Actions:** `.github/workflows/263-europe-elo-source-one-pass-audit.yml`.
Yalnız bu dosya değiştiğinde çalışır; eski analiz,
M0/M1/M2, lig güncellemesi ve 432 UEFA deneyi
yeniden koşturulmaz.
