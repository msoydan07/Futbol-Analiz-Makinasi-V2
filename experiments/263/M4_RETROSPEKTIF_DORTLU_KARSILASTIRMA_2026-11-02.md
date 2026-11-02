# 2.6.3 M4 — Tek geçmiş maç karşılaştırması (2 Kasım 2026)

**Durum:** RETROSPECTIVE_ONLY / NO_MODEL_PROMOTION / LIVE_FORWARD_100_PENDING

## Veri, yöntem ve değişmezler
- Arşiv: 4.413 tamamlanmış gerçek maç, 10 lig, 2025/26 3.533 ve 2026/27 880. SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- Dört model, 2026/27'nin 880 maçında, yalnız **maç gününden önceki** maç sonuçlarını kullanarak tarih sıralı yeniden değerlendirildi.
- M4 ayarı **değişmedi:** yarı ömür 360 gün, ortak Ridge 4, saha Ridge 48. Ayar seçimi daha önce 2025/26 gelişim bloklarıyla yapılmıştı.
- B (C1), C2 (k=5/w=0.5/min 4 bağlamsal maç) ve C3 (Ridge 6) model formülleri korunmuştur. Mevcut üretim modüllerine hiçbir terfi/uyarlama yapılmamıştır.
- Tutarlılık kontrolü: aynı 614 maçtaki B 0,9965338918 ve C3 0,9859468940 log-loss değerleri eski kanıtla birebir eşleşti.
- **Büyük sınır:** 2026/27 daha önceki deneylerde görülmüştü. Bu, bağımsız dokunulmamış son test DEĞİLDİR; geçmişte mühürlenmiş tahmin kaydı gibi de gösterilemez.

## Kapsama ve kendi örnekleminde ölçüm
| Model | Tahmin sayısı / 880 | 1X2 log-loss | Çoklu Brier | Doğru 1X2 |
|---|---:|---:|---:|---:|
| B | 616 | 0,9970 | 0,5946 | %51,3 |
| C2 | 105 | 1,0365 | 0,6232 | %48,6 |
| C3 | 873 | 0,9971 | 0,5946 | %51,5 |
| M4 | 880 | 1,0012 | 0,5969 | %51,5 |

Buradaki örneklemler farklı olduğundan doğrudan sıralama için kullanılamaz.

## Dört modelin ortak ürettiği 79 maç
| Model | 1X2 log-loss | Brier | isabet | KG log-loss | 2.5 gol log-loss |
|---|---:|---:|---:|---:|---:|
| B | 1,0171 | 0,6083 | %50,6 | 0,6765 | 0,6765 |
| C2 | 1,0189 | 0,6092 | %48,1 | 0,6985 | 0,6911 |
| C3 | 1,0035 | 0,6007 | %51,9 | 0,6698 | 0,6660 |
| M4 | 1,0015 | 0,5981 | %51,9 | 0,6739 | 0,6706 |

## İkili adil eşleştirmeler: referans eksi M4
Pozitif log-loss farkı M4 lehine. Gün bazlı blok bootstrap (1200 tekrar) %95 aralıkları yalnız retrospektif belirsizlik içindir.

| Referans | Ortak N | Referans log-loss | M4 log-loss | Fark | Bootstrap %95 |
|---|---:|---:|---:|---:|---:|
| B | 616 | 0,9970 | 0,9865 | +0,0105 | [+0,0036; +0,0172] |
| C2 | 105 | 1,0365 | 1,0219 | +0,0147 | [-0,0171; +0,0663] |
| C3 | 873 | 0,9971 | 0,9993 | -0,0022 | [-0,0065; +0,0026] |

Aynı 873 maçta KG Var/Yok log-loss: C3 0,6826 ve M4 0,6852; 2,5 Alt/Üst: C3 0,6852 ve M4 0,6907. Bu iki fark için anlamlılık testi yapılmadı.

**Kalibrasyon riski:** M4'ün %80 üstü en olası sonuç verdiği 24 maçta ortalama güven %84,1, gerçek isabet %62,5. N küçük; uç güven kalibrasyonu ileri pilotta incelenmeli.

## Kesin mühendislik kararı
- **M4 ana üretim motoruna ALINMADI.** C3 karşısında kapsamlı veride pozitif fark gösterilemedi; C3 üstünlüğü de güven aralığı nedeniyle kesin değil.
- B/C2/C3 ve M4 pilot ayarları korunacak; yeniden geçmişe bakılarak katsayı oynanmayacak.
- 100 **yeni** resmî fikstür teyitli, maç önü mühürlü tahmin pilotu başlamış sayılmaz. 25 maçta teknik kontrol, 100 maç sonunda tek bağımsız ileri ölçüm ve manuel model kararı.
- xG, korner, ilk yarı, sakatlık, oran/EV, A/B/C onayı bu geçmiş maç deneyinde yoktur.
- Yerel yeniden üretim paketinde tüm 880 maçın model gözlemleri, toplu JSON, bootstrap/lig kırılımları ve tarih sıralı çalışma kodu tutulur. Bu dosya yalnız özet/karar kaydıdır.
