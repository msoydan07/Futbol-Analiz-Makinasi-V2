# 2.6.3 — 2025/26 UEFA CL+EL maç öncesi yerel veri kapsamı: tek kabul raporu

**İnceleme tarihi:** 2 Kasım 2026.  
**Durum:** Yeni veri bulunabilirlik ve zaman-kesit denetimi BAŞARILI; güç modeli ONAYLANMADI.

## Çalışmanın kaydı ve kullanılan geçmiş çıktılar

- **Tek yeni GitHub kabul koşusu (başarılı):** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41485016193
- **Yeni yazılım güvenlik kontrolleri:** 5/5 başarılı.
- **Girdi A:** 4.413 maçlık sabit `historical_results.csv`, run 41251343847, arşiv SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- **Girdi B:** önceden tamamlanan tek CL+EL kapsam çalışması, run 41480542512; UEFA CL 95 + UEFA EL 37 = **132** yalnız inceleme adayı.
- **Yeni artefakt:** `263-uefa-2025-26-asof-domestic-input-coverage`, özet `coverage.json`, detay `matches_REVIEW_ONLY.json`.
- Yeni ağ erişimi, UEFA fikstür alma, önceki 432 maç puan testi veya 288 maç kapsam testi **tekrar çalıştırılmadı**. Eski kabul edilmiş artefaktlar okundu.

## Doğrudan ölçülen sayılar

| Tarihsel maç öncesi tamamlanmış yerel maç kapsaması | Şampiyonlar Ligi | Avrupa Ligi | Toplam |
|---|---:|---:|---:|
| 2025/26 kapsam adayı | 95 | 37 | **132** |
| İki takımda da en az 4 eski lig maçı | 89 | 37 | **126** |
| İki takımda da en az 8 eski lig maçı | 64 | 25 | **89** |
| En az bir takımda 4'ten az eski lig maçı | 6 | 0 | **6** |
| İki takımda da en az 4 eski xG çift verisi | 0 | 0 | **0** |

**Tanım:** `maç öncesi` burada **yalnızca maç takvim gününden daha eski yerel lig sonucu** anlamına gelir. Aynı gün oynanmış lig maçları, başlama saatleri bilinmediğinden, geçmişe alınmadı. Bu toplu CSV'nin UEFA tarihinden **önce gerçekten erişilebilir veya yayımlanmış olduğuna dair kanıt değildir**.

4 veya 8 tarihsel maç eşiği bir **girdi kapsam göstergesi**, asla gerçek tahmin gücü veya matematik modelinin kalibrasyonu değildir. xG sıfır sonucu, **bu özgün CSV içinde iki taraf için dörder geçmiş xG eşleşmesinin bulunmadığını** gösterir; dünyada xG yoktur anlamına gelmez.

## Kritik mühendislik değerlendirmesi

**Olumlu:**
1. 132 adayın 126'sında en az dört eski yerel maçlık tarihsel gol verisi her iki taraf için mevcut. Ligler arası güç farkı konusunda *veri tabanı koşulu* kısmen oluşmuş.
2. Eski maçlara tarih filtresi uygulanmış; hedef UEFA gününde/sonrasında gerçekleşen maç skorlarının sızdırılması önlenmiş.
3. Orijinal 4.413 maçlık veri arşivi hash ile doğrulanmış; hazır CL+EL 132 aday kaydı yeniden üretilmeden kullanılmış.
4. 2025/26 takım ve lig bağlamı esas alınmış; 2026/27 üyelik geriye taşınmamış.

**Henüz kapanmayan kanıt açıkları:**
1. UEFA karşılaşma takım adları kanonik lig kimlikleriyle eşleşen **adaylardır**, tüm takım numerik resmî UEFA club-ID eşlemeleri bağımsız biçimde onaylanmadı.
2. 132 UEFA karşılaşmasının her biri resmî karşılaşma sayfasına göre bağımsız teyit edilmiş değildir; kaynak güven sınırı korunur.
3. Tarihsel yerel lig verileri 2026'da derlenen arşivden alınmıştır. Bunların **maçtan önce yayınlandığı ve canlı sistem tarafından erişilebilir olduğu** ayrıca gösterilmedi.
4. Mevcut 4.413 maçlık kaynakta geçmiş maç bazlı xG/xGA girdileri iki takımda dörder eşleşme koşulunu **hiçbir** aday için sağlamıyor. Dışarıdan bulma ya da uydurma yok.
5. UEFA kulüpleri Avrupa'ya seçilerek katıldığı için ülke ligi ortalaması ile güçlü kulüp örneklemi arasında seçim yanlılığı sorunu var; ülke katsayısı ve takım etkileri henüz test edilmedi.
6. Bu denetim olasılık/logloss/Brier, 2.5 Alt/Üst, KG veya EV üretmedi; matematiksel karşılaştırma değildir.

## Karar ve tek sonraki toplu iş

**Modeli üretime almak veya yeni bir M5 kurmak YASAK.** Yalnız dondurulmuş 132 aday ve 4.413 yerel sonuç verisiyle keyfî küresel güç katsayısı kullanılmayacak.

Tek sıradaki paket: **132 maç özelinde resmî UEFA takım-kimlik kanıtlarının ve eski yerel verilerin tarihsel yayın/zaman bilgisi kaydının toplu kaynak denetimi.** Daha sonra xG'li/ xG'siz model kollarının gerçekte mümkün olup olmadığı için ayrı *veri kapsam kararı* yapılır. Bu aşamalardan önce M0/M1/M2 toplu dış testine geçilmez; kullanıcı tarafından kapsam dışı ülkeler/lige ayrı araştırma açılmaz.

**Değişmeden kalanlar:** main, 10 lig, B/C2/C3/M4, 100 maçlık pilot, kullanıcı bildirimli saat, T–60 ilk 11 akışı, H2H kaldırma kararı, haftalık yerel güncelleme.
