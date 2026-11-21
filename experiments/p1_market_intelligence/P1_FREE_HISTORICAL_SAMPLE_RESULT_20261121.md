# P1 — İzinli ücretsiz tarihsel örnek / tek toplu araştırma raporu

**Tarih:** 21 Kasım 2026. **Dal:** `experiment/p1-market-intelligence-20261121`.
**Durum:** İzinli dış kaynak örneğinde betimsel P0/P1 karşılaştırması yapıldı. Bu çalışmada ana 10 lig, 2.6.3, M4/C3, SHA mühürleri, canlı iş akışları ve eski model kararları **değiştirilmedi**.

## Veri ve izin

- Yayımcı: Football Charts, https://www.football-charts.com/data
- Herkese sunulan ücretsiz örnek: `https://www.football-charts.com/samples/fc-odds-archive-sample-germany2-2024-25.zip`.
- Sezon: **2024/25 Almanya 2. Bundesliga** — ANA 10 ANALİZ LİGİ DIŞINDA. Yalnız yöntem doğrulaması.
- Kullanım: Yayımcının ücretsiz deneme/değerlendirme örneği. İzinli test için ZIP, GitHub Actions işçisine **geçici indirildi**, ham oranlar depoya konmadı.
- Sunucu arşivine ait fiyatlar kaynak tarafından maçtan **sonra derlenmiş**; açılış/kapanış etiketi ve arşiv zaman alanları gerçek, bağımsız as-of SHA mühürü veya kör ileri test demek değildir. Bu nedenle **üretim terfisi yok**.
- Dış fiyatlar iddaa değildir. P0/P1 sonucu ana iddaa modelinin oranlarını değiştirmez.
- Erişilen 4 tablonun sayıları: **306** maç; **2.439** MS fiyat satırı; **17.060** Alt/Üst fiyat satırı (çoklu gol sınırları ve periyotlar); **644** KG satırı.

## İlk veri keşfi — kritik

Yedi tam fiyatın **tek bir bahis şirketi için** MS 1/X/2 + 2.5 Alt/Üst + KG Var/Yok olarak aynı maç ve fiyat aşamasında bulunduğu fikstür sayısı: **0 / 306**. Piyasaların her birinde fiyat var, fakat şirket kapsamları eşleşmiyor. Sırf üç pazar farklı şirketlerde var diye yedi oranın aynı şirketten geldiği iddia edilmedi.

## Ayrı yöntem deneyi: çoklu-şirket piyasa uzlaşısı

Eksik şirket oranları **uydurulmadı**. Her pazar için kendi karşıt seçimleri tamam olan **gerçek** şirket oranları alındı; her şirketin ilgili pazarı içinde ters-oran toplamı ile marj arındırıldı. Pazar içindeki seçim yüzdelerinin medyanı alınıp o pazarın toplamı tekrar %100'e normalize edildi. Bu **türetilmiş olasılıklar**, bahis şirketi fiyatlarıymış gibi yeniden etiketlenmedi. P1'in iki parametreli ters-Poisson modeli bunlara oturtuldu.

- Açılış ve kapanış aynı hesapta karıştırılmadı.
- Aynı maç, aynı faz içinde yalnız bir kez sayıldı; tek şirkete ait olmayan veri açıkça **CROSS_BOOK_FAIR_PROBABILITY_CONSENSUS** sayıldı.
- Her faz için **293** farklı, skor ve üç pazarın tamamı mevcut maç değerlendirildi; **13** maç eksik/uygunsuz pazar nedeniyle çıkarıldı.
- Aynı 293 maçın opening/closing sonuçları **iki bağımsız 293 maç seti değildir**; aynı fikstürün iki fiyat versiyonudur.

## Sayısal sonuç — gerçek dış örnek (betimsel)

Üç pazar: MS çok sınıflı Brier + 2.5 ikili Brier + KG ikili Brier; üç pazar eşit ağırlıklı makro ortalama. **Düşük Brier / log-loss daha iyi.**

| Ölçüm | Açılış P0 | Açılış P1 | Kapanış P0 | Kapanış P1 |
| --- | ---: | ---: | ---: | ---: |
| Eşleşmiş maç | 293 | 293 | 293 | 293 |
| Makro Brier | 0.52676 | 0.52769 | **0.52602** | 0.52706 |
| Makro log-loss | **0.79453** | 0.79598 | **0.79360** | 0.79540 |
| En yüksek olasılıklı seçim doğru | 180 | **187** | 186 | **190** |
| En yüksek seçim isabeti | %61.43 | %63.82 | %63.48 | %64.85 |

**Yorum:** P1 yüksek olasılıklı seçimi birkaç maç daha sık tutturmuş; ancak hem opening hem closing **düzgün olasılık hata puanlarında P0 az farkla daha iyi**. Tek bir lig ve tek sezonluk, yayımcı tarafından maç sonrası derlenmiş özel deneme seti; kalibrasyon, güven aralığı ve gerçek kör P1 üstünlüğünü kanıtlamaz. Bir oran-verisi dönüşümünden kendiliğinden bağımsız avantaj oluşmaz.

## GitHub yürütmeleri

1. Ham örnek indirme, tablo/şirket eşleştirme keşfi: `https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44942979758`.
2. Pazar bazında gerçek oranlardan türetilmiş olasılık konsensüsü ve P0/P1 ölçümü: `https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44943060766`.

İki çalışma da geçerli ve başarılı çıktı; ikinci çalışmada **293/306** kullanılabilir maç ölçüldü. Depoda ücretli arşiv, kaynak ZIP dosyası, çalıntı veri, iddaa dışı verinin iddaa etiketiyle sunulması veya kullanıcı belgeleri bulunmaz.

## Son teknik karar

- Bu veri, **10-lig P1 tarihsel backtesti değil**, bağımsız kaynak/hesap metodolojisinin **GER2 yöntembilim testi**dir.
- Yedi gerçek şirket fiyatı için tek sağlayıcı kuralı korunur. Çoklu-şirket yüzdelerinden yapılan **piyasa uzlaşısı ayrı model sınıfıdır**; doğrudan gerçek oran olarak kaydedilemez.
- P0 uygun geçerli bir piyasa referansı olarak devam eder; P1'in P0'dan üstün olduğu iddia edilmez. Ana **M4/C3 değişmez**.
- Ana 10 ligde iki veya daha fazla sezonun tek-sağlayıcı/yedi-fiyat, açık lisanslı ve maç öncesi doğrulanabilir kaynakları henüz tamamlanmadı.
