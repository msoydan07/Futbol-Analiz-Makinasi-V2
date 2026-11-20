# 2.6.3 ana tercih: dondurulmuş çalışır aday kontrolü

Ana 2.6.3 değişmedi. Gölge karar modülü M4 Ağustos ortak MS ile C3 KG ve 2.5 için 2025/26 sezonuna göre öğrenilmiş sabit lojistik olasılık kullanır.

| Dönem | N | İsabet | Ortalama tahmin | Seçim Brier | Pure/sklearn farklı ana olay |
|---|---:|---:|---:|---:|---:|
| 2026_aug_oct_raw_ms | 873 | %62.543 | %59.721 | 0.2315073 | 0 |
| 2026_sep_oct_joint_ms | 615 | %59.512 | %60.129 | 0.2370109 | 0 |
| 2026_nov8_real_sha | 39 | %69.231 | %60.834 | 0.2053719 | 0 |

39 gerçek SHA üzerinde orijinal forecast/KO zamanlarıyla tam arayüz çalıştırıldı. Yanlış saat, eksik veri ve family normalization kontrolleri olumlu. Bu sonuçlar araştırmada daha önce görülmüş geçmiş veriyi tamamen bağımsız kör doğrulama yapmaz. Canlı üretim değişmedi.
