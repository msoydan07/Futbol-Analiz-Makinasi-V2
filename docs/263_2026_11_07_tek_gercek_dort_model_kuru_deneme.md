# 2.6.3 — Tek gerçek dört-model kuru deneme (pilot dışı)

Amaç: 7 Kasım 2026 sabahı doğrulanmış gerçek Valencia–Real Madrid maçında, dört modelin dondurulmuş kodunun, 4518 sınırlı araştırma-kabul verisi ile SHA-kilitli baz 4413 arşivinden gerçekten ileri tahmin üretebildiğini görmek.

**Kritik sınırlamalar:** Bu, kullanıcı tarafından teklif edilen 96-match ya da ayrı 100-match pilotuna yeni kayıt eklemez. Bir canlı maçın analizini yalnız geçici klasörde yürütür, dosyayı çalışmanın sonunda siler; GitHub'a veya uzun ömürlü tahmin defterine sonuçları push etmez. Sadece kaynak SHA, durum, model 1/X/2-KG-2.5 özetleri ve araştırma kararının PAS olduğunu gösteren geçici GitHub Actions artefaktı tutulur. Pinnacle, API anahtarı ve bahis seçimi kullanılmaz.

Resmî sayfada bugünkü maç başlama saatinin hâlen doğrulanması, eşsiz canonical takım kimlikleri, güncel zamanın kickoff'tan en az 20 dk önce olması, kaynak SHA, model lock SHA ve DEV kalibrasyon lock geçerli olması zorunludur.

İş akışı: .github/workflows/263-sabah-one-real-four-model-smoke.yml

**Başarı şartı:** Baseline 4413 SHA, 4518 kabul checksum, B/C2/C3/M4 kod kilitleri, en az B/C3/M4 AVAILABLE, doğrulanmış pre-KO kayıt, tarihsel baz pazarları ve no-odds RESEARCH_PAS durumunu tek ve gerçek testte geçirmek.

Bu deneme, müşteri bahis önerisi veya modelin başarı oranını kanıtlamaz. Geçmiş maçları geriye dönük tahmin gibi mühürlemeyiz.
