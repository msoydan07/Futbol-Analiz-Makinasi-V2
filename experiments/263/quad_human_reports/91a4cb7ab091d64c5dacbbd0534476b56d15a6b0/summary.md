# Futbol Maç Analiz Makinası 2.6.3 — TOPLU MAÇ KARAR EKRANI

**Önce karar, sonra teknik ayrıntı. S1 yüksek olasılık ile S2 değerli seçim ayrı alanlardır.**

**DENEYSEL.** Bütün yüzdeler ve oranlar SHA-kayıtlı kaynaklardan okunur; örnek veri üretilmez.
İstenen: 2 · Tahminli: 2 · PAS: 2 · Koşullu seçimli: 0 · Analizi engellenen: 0
Kaynak kayıt: experiments/263/quad_batch_reports/91a4cb7ab091d64c5dacbbd0534476b56d15a6b0.json

| Maç | S1 · yüksek olasılık | S2 · ana karar | Alternatif | En olası MS (açıklayıcı) | Durum / gerekçe |
|---|---|---|---|---|---|
| Venezia – Udinese | ONAYSIZ | **PAS** | YOK | MS 2 | Güncel fiyat doğrulanamadı; NO_PRICE; oranlı pazar 0; RESEARCH_PAS |
| Toulouse – Strasbourg | ONAYSIZ (araştırma uyarısı mevcut) | **PAS** | YOK | MS 1 | Güncel fiyat doğrulanamadı; NO_PRICE; oranlı pazar 0; RESEARCH_PAS |

Her maçın dört modeli, kalibre edilmiş pazar yüzdeleri, fiyat kanıtı, veri eksikleri ve karar gerekçesi matches/ altında ayrıca gösterilir.
**PAS:** Analiz var ama fiyat veya yeterli değer yok. **ÜRETİLEMEDİ:** Gerçek tahmin kaydı oluşmadı.
Sabah fiyatı kullanılırsa KOŞULLU ibaresi zorunludur; güncel oran farklıysa güncel olan önceliklidir.
