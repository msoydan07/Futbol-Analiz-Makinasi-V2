# M4 AŞAMA 3 — kronolojik veri yeterliliği teşhisi (ilk bölüm)
Tarih: 2026-11-03
Durum: `NEW_READ_ONLY_SAMPLE_DIAGNOSTIC_DONE / MATCH_PREDICTION_ERROR_PROFILE_PENDING`

## Sabit veri ve yeni işlemin kapsamı
- Kaynak GitHub Actions `41251343847`, artifact `13061725424`, orijinal `historical_results.csv`.
- SHA256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1` **yeniden doğrulandı**.
- 10 lig, 2025/26 3.533 + 2026/27 880 = 4.413 gerçek sonuç satırı.
- Yeni diagnostik **hiçbir modelin katsayılarını fit etmedi**, geçmiş log-loss testlerini tekrarlamadı. Yalnız her 2026/27 maçında `match_date < target_date` kapsamında daha önce tamamlanan maçları saydı; aynı gün sonuçlarını hariç tuttu.
- Kaynak yalnız 2025/26 ve 2026/27 sezonlarını içeriyor. 2024/25 ayrı araştırma kümesinde; bu teşhisin geçmiş maç sayısına bilinçli olarak katılmadı.

## Ölçülmüş somut sonuç
| Ölçüt (2026/27, 880 hedef maç) | n | Oran |
|---|---:|---:|
| Ev veya deplasman takımının 2025/26 **aynı lig** geçmişi yok | 272 | %30,9 |
| Ev takımının kendi ev, ya da deplasmanın kendi dış saha **cari sezon** geçmişi <4 maç | 775 | %88,1 |
| Yukarıdaki saha örneklerinden biri cari sezonda <6 maç | 880 | %100 |
| İlgili ev/deplasman saha örneklerinden birinin **toplam** geçmişi <10 maç | 272 | %30,9 |
| Eşleşmedeki iki takımın en az birinin **tüm geçmiş** maç sayısı <20 | 272 | %30,9 |
| İki rol arasından daha az geçmişi olan takımın **ilgili saha** maç sayısının medyanı (iki sezon) | 19 | — |
| Aynı metrikte yalnız **cari sezon saha** medyanı | 2 | — |

Bu sayılar `880` farklı hedefin maça-özel öncesindeki tarihsel sayılarıdır; "775 takım" gibi yorumlanmaz. Eski sezon dahil edilmiş olduğunda saha geçmişi çoğu takıma 19+ maç verir; eksiklik özellikle yeni girişlerin ve **güncel saha formunun** azlığıdır.

### Lig kırılımı
| Lig | 2026/27 hedef maçı | 2025/26 aynı ligde geçmişi olmayan tarafla oynanan | Cari saha örneği <4 |
|---|---:|---:|---:|
| BEL1 | 80 | 24 | 72 |
| ENG1 | 80 | 23 | 80 |
| ENG2 | 144 | 63 | 97 |
| ESP1 | 99 | 29 | 83 |
| FRA1 | 72 | 16 | 71 |
| GER1 | 63 | 20 | 63 |
| ITA1 | 90 | 26 | 85 |
| NED1 | 90 | 28 | 74 |
| POR1 | 81 | 17 | 72 |
| TUR1 | 81 | 26 | 78 |
| **Toplam** | **880** | **272** | **775** |

## 2024/25 eklenmesinin özel etkisi
2026/27 başlangıcında 2025/26'da aynı ligde bulunmayan **31 takım-lig kaydı** var. Yeni 2024/25 araştırma takvimi bunların **7'si** için aynı ligde geçmiş buluyor. Geri kalan **24** yeni takım-lig eşleşmesi yine 2024/25 aynı lig geçmişine sahip değil. Bu **31 takım** ile **272 maç** ayrı örneklem tanımlarıdır; birbirine karıştırılmaz.

2024/25 ile aynı lig geçmişi yeniden görülebilen örnekler: Ipswich Town, Burnley, Cardiff City, Monza, Venezia, Willem II, KV Kortrijk. Bu bilgi iki yıllık mevcut takım güçlerini daha uzun geçmişle beslemenin etkisiyle aynı değildir. **İki ayrı deney açıklaması** gerekir: (A) mevcut takımlar için geçmiş uzatımı, (B) lige yeni giren takımın yeni bulunmuş aynı lig geçmişi.

## M4–C3 eski performans kanıtını tekrar kullan, yeniden ölçme
Kaynak `experiments/263/M4_RETROSPEKTIF_DORTLU_KARSILASTIRMA_2026-11-02.md`:
- C3–M4 aynı **873** maçta 1X2 log-loss C3 **0,9971**, M4 **0,9993**. Referans–M4 = **−0,0022**; gün bazlı bootstrap %95 aralığı **[−0,0065; +0,0026]** sıfırı içeriyor.
- M4 %80 üzerinde güven verdiği 24 maçta ortalama tahmin **%84,1**, gerçekleşen isabet **%62,5**. Örneklem 24, aşırı güven sinyali; kesin genellenemez.
- 873 ortak maçta KG Var/Yok log-loss C3 **0,6826**, M4 **0,6852**; 2.5 Alt/Üst C3 **0,6852**, M4 **0,6907**. İstatistiksel belirsizliği ayrıca ölçülmedi.
- C3 ile M4 farklı maçlarda aynı sezondan yeni sonuçlar kullanılarak seçilmedi; fakat 2026/27 bu projede daha önce incelenmiş olduğundan bağımsız, dokunulmamış final **değil**.

## Ne kanıtlandı, ne kanıtlanmadı?
1. **Veri durumu:** Özellikle yeni giren takımlarda aynı lig tarihçesi büyük oranda yok. 2024/25 arşivi yedi takım-lig girişine geçmiş sağlayabilir.
2. **Hipotez:** M4'ün takıma-özel saha katsayısı 4 ek takım parametresi getirdiği için küçük örneklemde istikrarsız olabilir; bu nedenle testte Ridge-venue=48'in (denenen en güçlü değer) seçilmesi tutarlı olabilir. **Yalnız açıklama, nedensel kanıt değil.**
3. **Hipotez:** M4'ün 360 günlük yarı ömür seçmesi daha uzun geçmişten yararlanmaya işaret edebilir, fakat bu aday 180 gün ile çok yakın çıktığı için sabit tercih değişmeyecek.
4. **Eksik:** Eski **maç başına 880 C3/M4 olasılık defteri** arşiv artifact'ında yok, deney dalındaki mevcut depoda da yok. Mevcut eski sonuç raporunda 873 ortak maçın bireysel hata dosyası bulunmuyor. Bu nedenle "M4 yeni takımlarda daha çok yanılıyor", "rakip gücünü az önemsiyor" ya da "favorileri abartıyor" diye **henüz** kesin sonuç verilemez.

## Sıradaki tek teknik iş: önyargılı tekrar yerine bir kayıtlı teşhis
Önce tek bir toplu, salt-araştırma çalışmasını kod düzeyinde hazırla: dondurulmuş kaynak ve değişmeyen M4/C3 formüllerinden `2026/27` maç-başına tahmin vektörlerini **yalnız hata teşhisi için bir kez yeniden üretmek gerekiyorsa**, eski ortak toplam log-loss değerleriyle regresyon eşitliği doğrula, sonra şunları bir kerede çıkar: yeni-giren takım var/yok, geçmiş saha örnek sayısı, ev/deplasman, lig, erken/geç sezon, büyük favori, yüksek güven, MS/2.5/KG gol pazarları, tekrarlayan kalibrasyon hataları. Hiçbir parametreyi 2026/27'ye göre seçme veya üretime geçirime. Eşleşme regresyonu tutmazsa tüm yeni bireysel sonuçları **karantinaya al**; yeniden tekrar çalıştırma yerine farkın teknik kaynağını raporla.
Sonraki bileşen/ablasyon testi bundan **ayrı**, tek önkayıtlı batch olacak; teşhis kohortunda daha iyi görünmesi bağımsız son test sayılmaz.

## Proje güvenliği
`main`, dondurulmuş 4.413, `2024_25_identity_resolved_research_history.csv`, M4/C3 kodu/ayarları, 100 ileri maç pilotu, UEFA maç önü mühürlü tahminler **değişmedi**. Bu rapor başka bir modele terfi kararı içermez.
