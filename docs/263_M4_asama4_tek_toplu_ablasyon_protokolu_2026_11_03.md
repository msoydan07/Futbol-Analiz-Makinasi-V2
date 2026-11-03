# M4 AŞAMA 4 — önceden sabitlenen tek toplu ablasyon protokolü
Tarih: 2026-11-03
Durum: `PLAN_LOCK_ONLY / NO_ABLATION_RUN_YET / NO_MODEL_PROMOTION`.
Motivasyon kaynağı: [Aşama 3 eşleşmiş hata teşhisi](263_M4_asama3_880_eslesmis_hata_raporu_2026_11_03.md).
**Önemli:** Hipotezler 2026/27 verileri görüldükten sonra üretildiği için 2026/27 *bağımsız final test* değildir; bu deney yalnız mühendislik geliştirmesidir. Üstünlük yeni mühürlü maçlarda ölçülmelidir.

## Değişmeyen veri kaynakları
- Dondurulmuş 2025/26–2026/27 arşivi: 4413 satır, SHA256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- 2024/25 ek araştırma havuzu: 3576 maç, GitHub dosyası `data/staged_263/2024_25_identity_resolved_research_history.csv`, blob SHA `26aaa482fedfa8aee3ca147878332e41cbeb4f46`; ayrı kimlik katmanı `data/staged_263/2024_25_historical_identity_registry.json`.
- Sabit C3 `experiments/263/exp_263_batch.py` (Ridge=6); sabit M4 `experiments/263/m4_integrated.py` (360/4/48). Kaynak blob SHA'ları sırasıyla `ad0c620080aa98fd3ab339535f0f2824b823e586` / `645d907e8f5f38faaed4763ca557802cea766bc4`.
- Sadece GOL, 1X2, KG, 2.5 Alt/Üst. İlk 11, oran, EV, maç saati, xG gerçek olmayan bu gol arşivinde üretilmez.

## Tek faktöriyel batch: 8 + 2 kol
Sabit matematik: Poisson log-link, 2 lig saha genel intercept'i, takım hücum/savunma ve rakip gücü **yalnız bir defa**. Yeni adayların tümünde ortak takım Ridge=6; varsa takım-özel-saha Ridge=48; varsa zaman ağırlığı yarı ömür=360 gün, ortalama ağırlık=1'e normalize. 2×2×2 faktöriyel:
| Kol | 2024/25 eklensin | Zaman ağırlığı | Takıma özel saha | Ortak Ridge |
|---|---|---|---|---:|
| F000 — orijinal C3 | Hayır | Hayır | Hayır | 6 |
| F100 | Evet | Hayır | Hayır | 6 |
| F010 | Hayır | Evet | Hayır | 6 |
| F110 | Evet | Evet | Hayır | 6 |
| F001 | Hayır | Hayır | Evet | 6 |
| F101 | Evet | Hayır | Evet | 6 |
| F011 | Hayır | Evet | Evet | 6 |
| F111 | Evet | Evet | Evet | 6 |
| L000 — kilitli M4 | Hayır | Evet | Evet | 4 |
| L100 — eski M4 + 2024/25 | Evet | Evet | Evet | 4 |

Bu kolların parametreleri **sonuca göre değişmeyecek**. F011 ile L000 arasındaki fark, aynı zaman/saha etkisinde ortak Ridge 6 vs 4'ün etkisini ayırt etmeye yarar. F000 ve L000 eski modellerin matematik kıyas referanslarıdır; kodları orijinal dosyalarda değiştirilmez. Rastgele ağırlık araması yok.

## Veri bölümü ve kaçak önleme
- 2025/26 geliştirme kohortu: 2025-11-15 ve sonrası. Orijinal M4'ün seçildiği 2025/26 fold'ları daha önce kullanıldı, burası da bağımsız son test değildir.
- 2026/27 tekrar kullanılmış retrospektif kohort: dondurulmuş 880 maç; bu sezondan önce sonuçlar 2024/25 ve 2025/26 ile birlikte kesim tarihine göre alınabilir.
- Her hedef için `match_date < kickoff_date`; aynı gün sonuçları, final ve sonrası **eğitim verisi olarak geçemez**. Her adayın 60 tamamlanmış önceki lig maçı minimumu sağlanmalı; ayrıca raporda başarısız kapsama kaydedilmeli. Tüm kolları adil karşılaştırmak için **aynı hedef maçların kesişim kümesi** kullanılacak.
- 2024/25 normal lig maçları **birincil eğitim**. ENG2/BEL1'in toplam 78 playoff/finali *önceden seçilmiş tek ikincil duyarlılık* olarak ayrıca etiketleyip karşılaştır. 78 maç karışınca lige özgü takımların güç düzeyleri değişebilir.
- Eski 4413 arşivini veya eski immutable `M4 lock` dosyasını yeni geçmişle güncelleme; adaylar izole tarihsel deneydir.
- 2024/25'te 20 yeni kulübün ayrı tarihsel kimlikleri kontrollü olarak kullanılır; 171 eski UUID yeniden kullanılmalı, yeni sezondaki ID'lere hiç dokunulmamalıdır.
- Lige giren/çıkanlar, 2025/26 olmayan takımın 2024/25 aynı lig geçmişi bulunması ve bulunmaması ayrı sınıflandırılır; **yeni takım yok diye 0 maç / 0 güç gibi değer üretme**.

## Karar tablosu (deney öncesi)
- Birincil: 1X2 *aynı maçlarda* log-loss farkı; ayrıca çoklu Brier, 1X2 isabet, KG/2.5 iki sınıflı log-loss, kalibrasyon, kapsama ve tarih-blok bootstrap %95 belirsizlik.
- Sabit kesimler: 2025/26 geliştirme, 2026/27 görülen tarihsel; 10 lig; önceki sezon aynı ligde var/yok; güncel bağlam 0–3 / >=4; lig, sonuç tipi ve >80% güven.
- Her hücre N, model kapsamı, hata ve belirsizlik yazılacak. Aynı maçta kapsama yoksa eşleştirme dışında kalacak ama neden ve miktar raporlanacak.
- Model üstünlüğü ancak istikrarlı, ligler boyunca anlamlı, birden fazla gol pazarında kötüleşmeyen sonuçlarla **araştırma sinyali** sayılır. Bu deneyden otomatik yeni model veya eşik çıkarmaya izin yok.
- Beklenen çıktı: `stage4_one_batch_2024_context_YYYY_MM_DD.json` + `stage4_paired_matches.csv` + **TEK** karşılaştırmalı Mühendislik Raporu. Gerçekleşene dek denendi/başarılı iddiasında bulunma.

## Tek işlem kuralı
Önce bütün kod, test ve veri-kimlik kontrollerini hazırlayıp tek kapalı/kilitli toplu karşılaştırma çalıştır. Çalışma sırasında formül veya hiperparametre ayarı değiştirme. Teknik hata varsa *nedenini* belgeler, sadece gerekçeli hata düzeltmesi yapar, aynı sorunsuz testleri sırf yeşil olsun diye tekrarlamaz. İlgili tek rapor oluşmadan sonraki xG aşamasına geçilmez. **Main**, canlı M0/M4, T−60 kilitleri ve ileri maç pilotu etkilenmez.
