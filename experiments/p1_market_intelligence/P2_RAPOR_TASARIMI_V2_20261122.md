# Üç Makine — Sade Rapor Tasarımı v2

Tarih: 22 Kasım 2026. **Araştırma dalı tasarım sözleşmesi**; üretim raporlayıcısına terfi/onay anlamına gelmez.

## Kullanıcı kararı

1. Ana M4/C3, kendi yedi olayından en yüksek gerçekleşme olasılığını kendi seçer.
2. P0, ilk iddaa PDF'sindeki komisyonu çıkarılmış yedi olay arasından en yüksek olasılığını **ana seçimi görmeden** kendi seçer. P1 yalnız ayrı teknik araştırma satırıdır.
3. P2 yalnız iki **bağımsız lideri** değerlendirir. Kodun şartlarını rapor ekranında yazma: **"Şart 1", "Şart 2", "Evet/Hayır" kapıları, iki ayrı kontrol listesi yasak.**
4. P2 sonuca yalnız **UYUMLU**, **FARKLI**, **ORAN EKSİK** gibi kısa bir ifade yazar. Aynı iki olay seçilmiş ve iki zirve yüzdesi yakınsa **Fark: N,NN puan** satırı gösterilebilir. Farklı olay seçilince iki farklı olayın yüzdeleri çıkarıl **maz**; fark satırı yoktur.
5. Her makinenin tercih kodu ve **kendi yüzdesi** korunur. **İddaa ham oranı**, P0'ın kendi liderinin altında ayrı küçük metin olarak gösterilir. Kullanıcıya yeni bir üçüncü matematiksel olasılık gösterme.
6. Ana alternatif, ana kartın alt kısmında **kırmızı**; varsa aynı olaydaki yüzde farkı **kırmızı**. Arka plan beyaz, ana metin siyah, simetrik kutular, Arial/benzeri font.
7. Tekli detayda piyasanın yedi olay yüzdesi ve gözlenen ham ilk-PDF oranları listelenebilir. İkinci PDF varsa fiyat hareketi/yorum değişir; mühürlü ana tahmin değişmez.
8. Bir iddaa hücresinde literal `-` varsa bu **fiyat yayımlanmamış seçim** olabilir (MS1, MSX, MS2, OU25, KG). Eksik grup no-vig yüzdesi hesaplanmaz. **P0'ın yedi seçeneğin gerçek lideri belirsiz** kalır, diğer fiyatlı pazarlar ayrı gösterilir; P2 = `ORAN EKSİK`. Fiyat uydurulmaz.

## Toplu satır örnekleri (22 Kasım araştırma; kaynak GitHub canlı test)

| Maç | Ana tercih (kendi %) | P0 tercih (kendi %) | İddaa ham oranı (P0 lideri) | P2 sonuç |
|---|---|---|---|---|
| Erzurumspor–Göztepe | MS2 %52,72 | 2.5 Alt %55,30 | 1,56 | FARKLI |
| Konyaspor–Beşiktaş | KG Var %54,91 | MS2 %60,30 | 1,43 | FARKLI |
| Kasımpaşa–Alanyaspor | KG Var %52,40 | KG Var %52,74 | 1,64 | UYUMLU (0,34 puan) |
| Trabzonspor–Eyüpspor | MS1 %85,54 | **Belirlenemiyor** | MS1 — | ORAN EKSİK |

Bu örnekler geçmiş araştırma koşusudur, yeni kesin/onaylı bahis tahmini değildir. P0 ve ana yüzdeleri birbirinden bağımsız hesaplanır.

## Görünüm ve kaynak

Prototip: kullanıcıya bu sohbette sunulan `uc_makine_rapor_tasarimi_v2.pdf` (3 sayfa; toplu + Konyaspor tekli + Trabzonspor eksik fiyat). PDF dosyası **GitHub'a yüklenmedi**. Tasarım burada kayıtlıdır; mevcut ana otomatik PDF şablonu henüz değiştirilmemiştir.

P2 karşılaştırma yöntemi testleri: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/45006284268
