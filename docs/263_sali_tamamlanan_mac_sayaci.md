# 2.6.3 / 3 Kasım Salı veri yenileme son kontrolü

**Tespit ve düzeltme (2 Kasım):** Kaynak CSV dosyalarında henüz oynanmamış
maç satırları bulunabilir. `audit_fixture_candidates.py` ve
`import_real_fixtures.py` bunları önceden `UNPLAYED_SOURCE_ROW` diye
ayırıyordu. Ancak `build_historical_results.py` tamamlanmış sonuç sayısını
hatalı olarak tüm kaynak satırlarının sayısına eşitliyordu:
`len(out)==len(candidates)`. Bu, kaynakta tek bir gelecek maç varsa bile
veri güncellemesini bloke edebilirdi.

Artık `expected_rows` yalnız `CANDIDATE_ONLY` (kesin sonuçlu) maçtır;
`candidate_source_rows_total`, `skipped_unplayed_source_rows` ve
`skipped_empty_source_rows` ayrı audit alanlarıdır. Yalnız tamamlanmış
maçlar kalıcı geçmiş sonuç dosyasına yazılır. Bozuk veya kısmi sonuç,
kaynak eşleşmesi, takım kimliği ve SHA denetimi yine fail-closed.

**Sınır:** Bugünkü kontrol ağdan 10 ligin güncel veri indirmesi değildir.
20 lig/sezon kombinasyonunu taklit eden bağımsız sentetik kaynak testi
yapılmıştır. Gerçek otomatik Salı koşusu ayrıca doğrulanmalıdır. Eski
4.413 maç dondurulmuştur. Pilot/tahmin kaydı yok.
