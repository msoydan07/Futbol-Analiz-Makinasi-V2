# 2.6.3 — 3 Kasım Salı veri hattı ön kontrolü

**Tespit:** Önceki `audit_fixture_candidates.py` sonuç hücreleri tamamen boş ama
ev/deplasman/tarih dolu gelecekteki fixture satırlarını `CANDIDATE_ONLY` işaretliyordu.
`import_real_fixtures.py` bunları tamamlanmış maç kimliği gibi kaydediyor;
`build_historical_results.py` ise skorsuz satırda hata veriyordu.

**Düzeltme:** Sonucu kesinleşmiş maç `CANDIDATE_ONLY`; skoru boş eşleşme
`UNPLAYED_SOURCE_ROW`; kısmi/yanlış sonuç `INVALID_RESULT_...`;
tamamen boş hücre `EMPTY_SOURCE_ROW`. Skorsuz ve tamamen boş satırların
orijinal kaynak satır numarası denetim için korunur ama maç sonu kaydı oluşturulmaz.

- Art arda üç aşama (fikstür kaynak adayı, kimlik, sonuç birleştirme) tutarlı.
- Güncel geçmişe kaydedilen her satırın tamamlanmış maç skoru olmak zorunda.
- Gelecekteki fikstür verisi doğrulanmış resmî maç kabul edilmez.
- 4.413 satırlık orijinal arşiv değişmez. Yeni satırlar `STAGED_UNVERIFIED_SOURCE_FILES`
  alanında kalır ve insan kaynak onayı olmadan ana sisteme geçmez.
- Hiçbir M4/B/C2/C3 koduna, pilot kayıtlarına, oranlara veya A/B/C'ye dokunulmadı.
- Testler yalnız yenilenen veri akışının güvenliğini kontrol eder.
- GitHub scheduled workflow hâlâ 3 Kasım TSİ 10.37, `main` üzerindedir; deney dalı
  üzerinden mevcut kaynak kodunu checkout eder.

**Açık sınır:** Daha önce tamamlanmış 2026/27 sonuçları kaynağın eski satırlarında
yeniden sıralanırsa veya kaynak sonuçları düzeltilirse kaynak kabulü otomatik durur.
Bu doğru güvenlik davranışıdır; sessiz eşleştirme yapılmaz.
