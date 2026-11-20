# 2.6.3 — Kalibrasyon mühendislik kararı ve iki sezon toplu denetim
**Tarih:** 20 Kasım 2026
**Dal:** `research/263-independent-math-audit` (canlı motoru değiştirmez)
**Tamamlanan bağımsız işler:** 4.413 maç kaynak SHA doğrulama; 2025/26 2.922 maç as-of geçmiş test; 2026/27 880 maç zaten oluşturulmuş as-of tahmin; 39 adet 8 Kasım maç önü SHA sonucu; farklı matematiksel adaylar; kalibrasyon eğitimi ve dört alternatifli MS/KG/2.5 ayrıştırması. 2.922+880=3.802 kronolojik tarihsel puanlanan maç (aynı anda tek bir kör holdout değil).

## 1) Takvim sıralı araştırma yaklaşımı

- 2025/26 arşivindeki **3.533** maçtan ilk **611** her ligde 60 maç altı olduğundan eğitim geçmişi; **2.922** tarih sıralı geriye dönük tahmine uygun. Önceden M4 hiperparametre belirlemede kullanılmış 702 geliştirme-bloku maçı ayrıldı, kalan **2.220** maçtan C3/M4 kalibrasyon ailesi ağırlıkları öğrenildi.
- Bu ağırlıklar 2026/27 **587 Ağustos–Eylül**, **293 Ekim** ve ayrıca 39 Kasım 8 SHA kaydına uygulandı. Kasım'ın aynı günün 39 maçından ibaret olduğunu ve bütün sonuçların federasyon seviyesinde bağımsız ID doğrulaması bulunmadığını unutma.
- **2026/27 daha önce çok kez araştırılmıştır; bu bir as-of rekonstrüksiyon olsa da tamamen kör bir dış test değildir.** 2025/26 M4 ayar dönemidir, dolayısıyla 2025/26 da sonradan bağımsız dış test değildir.
- Bütün sonuçlar orijinal **4.413** maç SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1` kaynağıyla eşlendi. Ayrı 4.518, 4.617, 4.618 havuzları ve 22 lig projeleri karıştırılmadı.
- Referans lig frekansı her maç günü yalnız önceki karşılaşmalardan üretildi.

## 2) 2025/26 ne öğretti?

Ham skorlar (Brier düşük iyi): C3 için MS=0,612732, KG=0,251771, 2.5=0,254894; M4 için MS=0,612355, KG=0,253779, 2.5=0,256044; yalnız eski lig oranı için MS=0,655071, KG=0,246342, 2.5=0,248558. Sonuç: takım/rakip bilgisi MS için değerli, ham KG/2.5 için basit referans bile daha iyi olabilir.

Bu dönemin **702 M4 geliştirme tarih bloğu hariç 2.220 maçından** eğitimle sabitlenen en uygun grid:
- C3 KG: **%25 model, %75 geçmiş lig oranı**.
- C3 2.5: **%25 model, %75 geçmiş lig oranı**.
- M4 MS: grid %75 model, %25 geçmiş lig oranı; fakat daha sonraki 2026/27 maçlarında MS ham M4 **daha iyi**. Bu yüzden ayrı ayrıştırma testinde MS ham M4 sabitlenmiştir. MS ham sabitleme **sonuçlara bakılarak tercih edilen araştırma varyantıdır**, yeni kör kanıt değildir.
- 2026 Ağustos-Eylül'de öğrenilen farklı karışım: C3 KG %50, C3 2.5 %25; MS M4 %100. Bu karışım sadece Ekim ve Kasım'da ölçüldü.

## 3) İkinci sezon: 880 maç, 873 ortak M4+C3 kapsaması

| Aile kuralı, maç başına tek olay | N | Toplam isabet | Ortalama belirtilen yüzde | Seçim Brier |
|---|---:|---:|---:|---:|
| Ham M4 MS + ham C3 KG/2.5 | 873 | %57,62 | %62,05 | 0,239537 |
| MS M4 ham + C3 KG ve 2.5 yüzde 25 | 873 | **%59,79** | **%59,34** | **0,233510** |
| MS M4 ham + KG/2.5 yalnız lig geçmişi | 873 | %60,14 | %59,70 | 0,233252 |
| M4 MS %75, KG C3 %25, 2.5 C3 %25 | 873 | %60,71 | %57,70 | 0,234120 |

Aynı 873 maçta bir maç tek bir olaydır; farklı modellerin farklı olay seçebilmesi nedeniyle isabet ve seçilmiş Brier, aile bazındaki aynı olay düzgün skorlarının yerine geçmez.

**As-of ortak aile Brier:** Ham M4 MS **0,595900**; yüzde-25 KG/2.5 modelinde MS **aynı 0,595900**, KG ham **0,244746** → ağırlıklı **0,243085**; 2.5 ham **0,245808** → ağırlıklı **0,241187**. MS üzerinde değişiklik yapılmadı.

Gün bazında 60 tarih bloğuyla ham kural karşılaştırması:
- %25 karışım **isabet artışı +2,176 yüzde puan**; **%95 gün-blok aralık [-1,099; +6,117]**. Sıfırı kestiği için kesin karar üstünlüğü göstermez.
- %25 karışım seçilmiş Brier iyileşmesi **+0,006026**; **%95 gün-blok aralık [-0,001103; +0,013978]**. Sıfırı kestiği için kesin kazanç ispatı değildir.
- Seçim olayı **358/873** maçta değişti; aynı örneklemde farklı seçilen sonuçlar karşılaştırılmaktadır.
- 2025 sezonu tabanlı ağırlıkları tam 2026/27'de uygularken pazar bazlı Brier'nin iyileşmesi gözlendi, ancak aynı pazar eşleşmiş bootstrap'ta KG/2.5 için %95 aralıklar da sıfırı kesti.

## 4) Dönem ve mühür duyarlılığı

| Dönem | Ham isabet (n) | Yüzde-25 isabet (n) | %25 karışımın +/- gün-block aralığı |
|---|---|---|---|
| Ağustos–Eylül | %57,59 (580) | **%60,52** (580) | artış +2,931 puan, %95 [-0,866; +6,316] |
| Ekim | %57,68 (293) | **%58,36** (293) | artış +0,683 puan, %95 [-5,578; +10,160] |
| 8 Kasım SHA | **%66,67** (39) | %61,54 (39) | tek maç günü; güven aralığı hesaplanamaz |

Kasım'da ham MS/C3 aile seçicisi tek gün üzerinden daha çok tuttu. Yüzde-25 modelin mutlak bir kazanan olarak ilan edilmesi bu nedenle yanıltıcıdır.

Farklı eğitimi olan ve **yalnız Ekim-Kasım'a** uygulanabilen KG C3 %50, 2.5 C3 %25 karışımı Ekim'de %58,70 (293); Kasım'da %64,10 (39) isabet verdi. Aradaki farklar küçüktür; farklı eğitimli adayları sonuçtan sonra seçmenin kazanç yanlılığı riski vardır.

## 5) Eşik tanıları: pas yanılgısı

2026/27 880 maç havuzunda güven skoru en az %65 olanlar:
- Ham aile: **251** seçim, %69,72 isabet, %71,60 ortalama öngörü.
- MS ham + KG/2.5 yüzde-25: **159** seçim, %72,96 isabet; bunlar önceki 251 ile aynı maçlar olmadığı için eşit nüfusta eşleştirilmiş bir kıyas değildir.
- Lig KG/2.5 sıfır modeli: **158** seçim, %70,89 isabet.
Böyle eşikler geriye dönük seçildiği için yeni bahis kararı/yüksek gerçekleşme garantisi olarak yorumlanamaz.

## 6) Nihai mühendislik kararı

**Değişmeyen gerçekler:** Bağımsız araştırmada mevcut Poisson altyapısı MS pazarı için faydalı; KG ve 2.5 ham olasılıklarındaki aşırı güven/kalibrasyon riski gerçek bir düzeltme önceliği. Saf yeni dağılım (DC/bivariate/NB) yöntemleri önceden çalışılmış dönemde net bir genel kazanan üretmedi. KG/2.5 için geçmiş lig oranıyla %25 C3 karışımı, farklı dönemlerde araştırma adayı olmaya değer; MS'de ham M4'ü bırakmak için kanıt yok.

**Karar:** Mevcut ana 2.6.3, üretim seçici, mevcut SHA mühürleri, otomasyonlar, 10 lig raporları, PDF, xG ve veriler **değiştirilmedi**. Yeni yaklaşım **araştırma/gölge aday** olarak kaldı. 2025/26 model ayar dönemi ve 2026/27'nin daha önce görülmüş sonuçları nedeniyle kör dış doğrulama olmadan terfi mühendislik açısından savunulamaz. Mevcut mühürlenen gerçek maçların zaten süren sonuç takibindeki verileri dışında kullanıcıya tekrar pilot yüklemek de gerekmiyor.

**Kâr, oran ve değer iddiası yok:** Matchday iddaa/market implied olasılığı, eşleşmiş snapshot oran ve EV/ROI bu deneyin parçası değil.

## 7) Reprodüksiyon

- [Bütün iki sezon kalibrasyon CI iş akışı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44811285583) — başarılı.
- [Son MS ve KG/2.5 ayrıştırması ve maç-günü bootstrap](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44811611637) — başarılı.
- [İki sezonun bütün ayrıntılı tarihli metrikleri](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/07_calibration_result.json)
- [Ayrıştırma: dört aday; dönemler, PAS, Brier, günlük güven aralıkları](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/09_decision_ablation_result.json)
- Kaynaklar: `audit_market_calibration.py`, `audit_decision_ablation.py`, daha önceki `audit_full_history.py`.
