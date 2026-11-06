# Futbol Maç Analiz Makinası 2.6.3 — KALICI KARAR EKRANI STANDARDI

**Durum:** 6 Kasım 2026'da kullanıcı tarafından açıkça tercih edilen nihai kullanıcıya sunum düzeni. **Yeni sohbette de aynen uygulanacak.**

## Değiştirilemez sunum sırası

### A. TEKLİ MAÇ KARAR EKRANI — en üstte, önce karar sonra teknik açıklama

1. Maç, lig, başlama TSİ, tahmin kilit tarihi, deneysel/resmî kayıt statüsü.
2. **MAKİNENİN ANA KARARI (S2 / değer odaklı)**: Seçim ve pazar, kalibre olasılığı, doğrulanmış fiyat ve EV, karar statüsü; koşullar sağlanmazsa açık **PAS ve nedeni**.
3. **Alternatif tercih**: Farklı pazar ailesinden en fazla bir onaylanabilir alternatif veya **YOK**; güven ve koşullu sabah fiyatı ayrı yazılır.
4. **S1 yüksek olasılık kontrolü**: En olası / yüksek yüzde araştırma uyarılarını göster; *resmî filtre GEÇTİ* kararı gerçekten üretilmediyse **ONAYSIZ** yaz. S1'i S2/value yerine geçirme.
5. **S2 matematiksel değer**: Güncel oran, no-vig, EV, kalibrasyon kararını göster; doğrulanmamış oranla seçim üretme.
6. **A/B/C tercih adayı sınıfı**: Sadece şablonun §12.1–12.2 koşulları gerçekten çalıştırılmış ve ispatlanmışsa sınıf göster; aksi hâlde **ONAYLANMADI** yaz. A/B/C, B/C2/C3/M4 matematik modelleri değildir.
7. **Açıklayıcı futbol tahmini**: En olası MS (hangi model/hangi yöntem!), M4 MS yüzdesi ve en olası skor ayrı. Farklı modelin medyan yüzdesini M4'ün kalibre edilmiş karar yüzdesi gibi göstermeyin.
8. Veri güveni, model güveni, kadro/ilk 11, rakip kalite, ilk yarı, korner, Elo, xG ve oran kontrollerinin gerçekte uygulanma/eksik durumları; kanıtlanmamış alanlar **DOĞRULANAMADI / BU KAYITTA HESAPLANMADI**.
9. Altta dört-model karşılaştırması, gol/KG/çifte şans, saha/taktik ayrıntı, kaynakları ve GitHub SHA kaydı. **Önce matematik tablosu değil, önce karar ekranı.**

### B. TOPLU MAÇ KARAR EKRANI — en üstte tek karşılaştırma tablosu

Tablo sütunları öncelikle:
**Maç | S1 | S2 ana karar (pazar / yüzde / fiyat veya PAS) | Alternatif | En olası MS | Durum ve kısa gerekçe**.

Tablodan sonra toplam istenen/tahmin üretilen/engel/PAS/koşullu seçim adedi, risk-kayıt zamanı ve her maçın tekli ayrıntı rapor bağlantısı verilir. Bir maç için oran yoksa tablo dağılmaz: **S2 PAS**; açıklayıcı model MS ve varsa S1 araştırma uyarısı korunur.

### C. Yanlış anlaşılmayı önleyen kesin kurallar

- **S1**, yüksek gerçekleşme olasılığı filtresi; **S2**, oran ve matematiksel değer seçimi. S1 resmi onayı ile S1 araştırma uyarısı farklıdır.
- **S2 PAS ≠ model tahmini yok**; "en olası maç sonucu" ile "değerli ana tercih" birbirinin yerine geçmez.
- A/B/C sınıfı, onaylanmış §12 filtre ve değer koşulları olmadan verilmez.
- 1,5 Üst sırf yüksek yüzdesi nedeniyle ana seçim olmaz; fiyat, değer ve geçmiş kalibrasyon gerekir.
- En fazla bir **ana** ve farklı aileden en fazla bir **alternatif**. Gerekirse hiçbiri seçilmez.
- Doğrulanmayan pazar/ilk yarı/korner/xG/ilk 11 verisi uydurulmaz; eksik veri diğer hesapları otomatik iptal etmez.
- Model tahminleri, seçim kararları ve SHA kilitleri maçtan sonra değiştirilmez.
- Modül 0 ve ilk yarı korneri geri eklenmez.
- Bu dosya mevcut tahmin motorunun bütün 17 bölümünü uyguladığını **iddia etmez**; sunum düzenini sabitler.

## GitHub uygulama bağlantısı

Yeni maçlar için standart rapor üreticisi: `experiments/263/quad_user_report_263.py`.
GitHub Actions: `.github/workflows/263-quad-forward-on-request.yml`.
Raporlar: `experiments/263/quad_human_reports/<istek-commit-SHA>/summary.md` (TOPLU) ve `matches/<gün>/<maç-kimliği>.md` (TEKLİ).
6 Kasım 2026 Gaziantep–Kasımpaşa'nın önceden oluşturulmuş eski raporları değiştirilmez.

## Yeni sohbet için tek cümle

**"Ortak, Futbol Analiz Makinası 2.6.3 için GitHub'daki `docs/263_KARAR_EKRANI_KALICI_STANDART.md` dosyasını esas al. Son sözümüz TEKLİ ve TOPLU KARAR EKRANIDIR: önce S2 ana karar, sonra alternatif, S1, A/B/C, açıklayıcı MS, eksikler ve en altta teknik modeller. Eski kısa model tablosuna dönme; kilitli tahminleri değiştirme."**
