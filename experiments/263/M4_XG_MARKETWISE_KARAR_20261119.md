# M4'e xG katkısı — 19 Kasım 2026 matematiksel karar

**Karar:** xG zorunlu özellik değildir. Hedef olabildiğince doğru ve iyi kalibre edilmiş maç önü olasılıklarıdır.

## Kaynak ve yöntem
- 10 lig, 2025/26–2026/27; kilitli 4.618 kayıt, SHA-256 `3b13921daafab70aa121fe807fea0a74e0c72f0fc2381366b183f621edea762c`.
- Mevcut **gerçek ve SHA kilitli M4 matematiği**, SHA-256 `eac755e54086738f40d7f30a514b2c9bb789b2fd2b49bc45`, değiştirilmedi.
- 1 Ağustos–8 Kasım 2026 aralığında mevcut kodun **birebir** son 1.083 karşılaşmasında karşılaştırma; 1 M4 dışlanmış, 810'unda geçmiş xG uygun, 273'ünde güvenli fallback. Model ve xG her hedef maç için yalnız önceki günlerden veri kullandı.
- Her maçta ham M4 ile aynı uygulamadaki özel `m4_xg_support_263.py` (`alpha=0.438`, kaynak/kimlik/tarih kontrolü, son 12 ev/deplasman maçı, 6 lig öncülü) eşleştirildi.
- xG dosyasındaki skorlar araştırma M4 geçmişine de izdüşürüldü. Bu turda ayrı resmi skor CSV'si veya tarihsel yayımlanma zamanı bağımsız doğrulanmadı. Aynı sezon daha önce çalışıldığı için kör prospektif test değildir.

## Aynı maçlarda eşit kıyas

| Pazar | Ham M4 Brier | Mevcut xG kodu Brier | M4 − xG (pozitif xG iyi) | Tarih günü kümeli %95 fark aralığı | Karar |
|---|---:|---:|---:|---:|---|
| MS 1-X-2 (üç ihtimal ort. hata) | 0.195592 | 0.196817 | -0.001225 | -0.002265…-0.000236 | **M4 korunur** |
| 2.5 Üst/Alt | 0.247734 | 0.244649 | +0.003085 | +0.000613…+0.005660 | **xG araştırma seçimi** |
| KG Var/Yok | 0.245417 | 0.244185 | +0.001232 | -0.000644…+0.003293 | **M4 korunur; katkı belirsiz** |

2.5 Alt/Üst iyileşmesi 10 ligin 9'unda olumlu, 4 ayın tamamında olumlu, istisna **ENG1**. MS 10 ligin yalnız 2'sinde xG lehine. Tarihsel kaynak belirsizliği, çoklu karşılaştırma ve seçim sonrası aşırı uyum riski vardır.

Bu sonuç, önceki *ortak kalibrasyonlu* M4+xG testindeki sayılardan farklıdır; zira yeni, gerçekten entegrasyonda kullanılan kod **ham M4** ile karşılaştırılmıştır. İki araştırmayı birbirinin yerine koyma.

## Uygulanmış araştırma karar kuralı

1. **MS 1-X-2:** orijinal M4'ün üçlü olasılık vektörü (birlikte toplam %100).
2. **KG Var/Yok:** orijinal M4'ün ikili olasılık çifti (birlikte %100).
3. **2.5 Alt/Üst:** güvenilir, önceki tarihlere ait xG varsa xG'li M4'ün **iki olasılığı birlikte**; yoksa eski M4. 2.5 Üst yüzdesi, M4'ün 1.5 Üst / 3.5 Üst olasılıklarıyla matematiksel olarak çelişiyorsa otomatik eski M4 fallback. Tarihsel 810 uygun maçın sıfırında bu çelişki gözlendi.
4. Farklı pazar ailelerinin yüzdeleri farklı ortak Poisson dağılımlarından seçildiği için ortaya **tek ve tamamen tutarlı skor dağılımı çıktığı iddia edilmez**. Bu bir pazar bazlı araştırma politikasıdır.
5. `m4_integrated.py`, B/C2/C3, eski mühürler, odds, SHA ve mevcut resmî kararlar **değişmedi**. Model iyileştirmesi ya da canlı bahis yetkisi verilmedi.

## Doğrulama / sonraki kullanım

- Kod: `experiments/263/m4_xg_market_policy_263.py`; tüm özel xG yan dosyalarında `marketwise_research_policy` nesnesi bulunur.
- Özel karşılaştırma: `experiments/263/m4_xg_private_report_263.py` yeni politika kaynaklarını ve seçilen 2.5 yüzdelerini kullanıcıya gösterir.
- GitHub Actions bu özel dosyaya otomatik erişemez. Maç günü yalnız **yeni, gerçek, resmî kapıdan doğrulanmış ve maç başlamadan SHA mühürlenmiş** tahmin ile, yerel özel xG dosyası mevcutsa araştırma çıktısı oluşur.
- İlerideki teknik kararlar için Brier/logloss, aralık, as-of/izin, eksikliği ve gerçek maç önü kayıtları değerlendirilir; kullanıcıdan yeni pilot talep edilmez.
