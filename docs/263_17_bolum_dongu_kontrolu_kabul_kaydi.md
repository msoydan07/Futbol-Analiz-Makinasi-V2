# 2.6.3 — 17 bölüm kabul ve döngü kontrolü

**Kapsam:** Model B/C2/C3 formülleri, kabul geçmişi, xG geçmişi, isim kimliği ve resmî fikstür adaptörleri değiştirilmedi. Modül 0 ve ilk yarı korner iş kapsamı dışı. Haftalık veri güncelleme kararı **Salı (Europe/Istanbul)**; bir cron/otomasyonun kurulu olduğu iddia edilmiyor.

**Tek değişen mühendislik işi:** `operational_report_263.py` artık aynı çalıştırmada `section_acceptance_263.py` ile 17 bölümün ayrı JSON/Markdown kontrol raporunu üretir. Yalnız raporun kendisindeki hesap çıktıları, kalibrasyon etiketleri, veri kesimi, model terfisi ve bahis önerisi güvenlik kuralları denetlenir. Bir harf veya liste başlığı tamamlanmış canlı analizi kanıt sayılmaz.

## Somut kontrol sonuçları

- 4.413 maç SHA-256 ve kilitli kabul veri bağı doğrulandı.
- 3 geçmiş tarihli, varsayımsal isimli offline vaka için matematik/rapor bağlantısı çalıştı. C2 bunların **1/3**'ünde yeterli örneklem buldu; kalan ikisinde onaysız model terfisi olmadı.
- 17 bölümde **tam canlı hazır** etiketi verilmedi; hesaplanmış, kısmi, canlı maç sırasında kontrol edilecek ve sonraki aşama durumları ayrıldı.
- C2 sabitleri `k=5, w=0.5`; matris 1X2/çifte şans/gol/KG olasılık tutarlılığı; aynı gün ve sonrası veri kesimi; C3 ve xG'nin onaysız terfi yasağı denetlendi.
- İlk 11 açıklanmadı diye temel hesaplama durmaz; doğrulanmış ilk 11 diye de gösterilmez.
- Bu çalışma yeni geçmiş model performans testi, xG yeniden deneyi veya 25 maç pilotu değildir.
- **102/102 birleştirilmiş yazılım testi geçti**; `section_acceptance_263.json` durum: `PASS_OFFLINE_INTEGRATION_ONLY`.

## Gerçekten bekleyen teknik işler

1. Kullanıcının adını verdiği ve resmî kaynaktan kontrol edilen tek maçın gerçek verileriyle 2.6.3 raporunun aynı çağrıda tamamlanması (fikstür tarama sistemi geliştirmeden).
2. Güncel lig verisinin Salı yenilemesinde kaynağı/kimliği/tarihiyle alınması ve özellikle kritik kadro/haber gibi maç saati unsurlarının doğrulanması.
3. C2 kapsam ve kalibrasyon sınırı; henüz onaylı yüksek güvenli A/B/C seçim üretilmediği gerçeği.
4. Bağımsız ileri dönem kanıt, ardından kullanıcı kararına göre maç önü sabit tahmin defteri, oran/EV ve pilot.

**Kabul ayrımı:** Offline zincir/testler = geçti. Tam canlı 2.6.3 ve doğruluğu yüksek tahmin kanıtı = henüz kabul edilmedi. Eski deneyleri yeniden açma veya yeni fikstür alt projesi kurma yok.
