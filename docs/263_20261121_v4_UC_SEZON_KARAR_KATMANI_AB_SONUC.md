# 21 Kasım 2026 — V4 karar katmanına 2024/25 ek sezon A/B araştırması

**Durum:** RETROSPECTIVE_RESEARCH_ONLY · MODEL TERFİSİ YOK · MEVCUT V4 VE SHA MÜHÜRLERİ KORUNDU

## Hipotez
Temel gol modellerine katkısı görünmeyen 2024/25'in, **karar katmanının kalibrasyon için daha fazla maç görmesi** sayesinde KG ve 2.5 olasılıklarını ve MS/KG/O2.5 arasından tek tercihi iyileştirmesi mümkün olabilir. Bu ayrı olarak sınandı.

## Salt araştırma kaynakları
- Eski ZIP: `M4_Asama4_On_Kollu_Tek_Toplu_Deney_2026_11_03.zip` (SHA256 `239f853da519400dbc89b3d3c4d3253badf9ce60804a79c82d7e59dbe3c7076b`).
- İçerik: 2024/25 normal lig maçları 3.498; 2025/26 + 2026/27 4.413 sonuç, eski maç bazında C3 logloss kayıtları ve M4/C3 kaynak kodu.
- 2024/25 ilk 120 maç/lig sonrası **2.284** maçta as-of C3/lig oranı yeniden hesaplandı. 2025/26 önceki ZIP C3 kayıtlarından **2.247** eğitim maçı. Üç sezon eğitim **4.531**; karşılaştırma eski 2026/27 ortak **873** maç.
- Matematik sabit: M4/MS; C3/KG/2.5; yeni seçim **yedi olaydan en yüksek olasılık**. Aday kalibratörlerde aynı lojistik öğrenme ve sabit L2=1, sadece eğitim maçı kümesi değişiyor. 2026/27 sonuçları eğitime girmedi.
- **Regresyon kapıları geçti:** M4 ham MS log-loss 0,999336 (önceki 0,999336); C3 KG ve 2.5 eski log-loss eşleşti.

## Asıl iki eğitim kolunun aynı 873 maçtaki karşılaştırması
Düşük log-loss/Brier iyi.

| Ölçüm | 2025/26 eğitim (2.247) | 2024/25+2025/26 eğitim (4.531) | Ek geçmiş etkisi |
|---|---:|---:|---|
| KG log-loss | 0,677158 | 0,677827 | +0,000669 kötü |
| 2.5 log-loss | 0,670784 | 0,673874 | +0,003090 kötü |
| Seçilen 7 olaydan tek ana tercihin gerçekleşmesi | 537/873 = %61,512 | 524/873 = %60,023 | **−13 maç** |
| Seçilen tek tercih log-loss | 0,656040 | 0,661466 | +0,005426 kötü |
| Karar değişen maç | — | 114 | daha fazla eğitim kazandırmadı |

Tarih-blok 3.000 bootstrap, fark = üç sezon − iki sezon: KG log-loss %95 [−0,001764; +0,003276]; 2.5 [+0,000756; +0,005408]; seçilen ana tercih gerçekleşme oranı farkı [−0,028336; −0,002938]. Bunlar daha önce defalarca incelenen tarihsel değerlendirme maçlarıdır, kör bağımsız sonuç değildir.

## Dondurulmuş gerçek v4 katsayıları, sadece lig geçmiş oranı uzatılırsa
**MS/M4 ve C3 ham KG/O2.5 ve v4 katsayıları aynı**; yalnız lig tabanı geçmişine 2024/25 normal maçlar eklendi.

| Aynı 873 maç | Güncel v4 araştırma referansı | v4 + eski lig oranları |
|---|---:|---:|
| KG log-loss | 0,677944 | 0,679060 |
| 2.5 log-loss | 0,672473 | 0,673508 |
| Tek tercih gerçekleşmesi | 541/873 = %61,970 | 534/873 = %61,168 |
| Farklı karar | — | 57; net 7 daha az doğru |

Ek tarihsel sonuçlar bu giriş etkisi yoluyla da performansı yükseltmedi.

## Önemli sınır
**Operasyonel v4 C3 kalibratörünün orijinal eğitim sayısı 2.898, burada araştırma A/B'sinin ortak 2025/26 örnek sayısı 2.247'dir.** Bu test orijinal kilitli v4'ün tam yeniden eğitimi değildir; aynı formülle öğrenen **iki araştırma gölge adayının** kontrollü kıyası ve orijinal kilidin lig tabanına +2024 duyarlılık sınamasıdır. 2024/25 C3 tahminleri 2026'da geriye dönük ama her maçın tarihinden önceki skorlarla üretildi; orijinal 2024 tarihinde SHA mühürlü değildi. 2024 skorlarının tümü iki bağımsız kaynaktan teyitli değil. Bu 873 maç daha önce incelenmiştir; geleceğe ilişkin kesin anlamlı üstünlük veya zarar iddiası kurulmaz.

## Mühendislik kararı
**2024/25 geçmişi ARŞİVDE KALIR, bu yeni karar-katmanı gölge adayı CANLIYA TERFİ ETTİRİLMEZ.** M4, C3, v4 politika kilidi, 21 Kasım 50 maç mühürü, 10 lig kapsamı, oran kaynağı ve diğer kayıtlar **dokunulmadı**. Yeni gelecek SHA mühürleri üzerinden bağımsız değerlendirme geçerliliğini korur; aynı geçmiş üzerinde ilave hiperparametre taraması açılmaz.

## Deney çıktıları
Kullanıcıya bu sohbette ayrı indirilebilir dosyalar sağlandı:
- `shadow_v4_season_calibration_ab_20261121.py` — SHA256 `a36f68be9b14a2a59d6049f497b89950ae5d7b23b8f2bc4b3175448e993cd4de`.
- `263_v4_uc_sezon_karar_katmani_shadow_AB_20261121.json` — SHA256 `9fc9c8c735e17f22622d1a336d3ea5c07530cb86b910c407ef2ee422b8b2803d`.
- `263_v4_uc_sezon_karar_katmani_873_mac_20261121.csv` — SHA256 `3b444eef114440221b9f70a475cffb0c3737187d1ca711b6d2c15c560af5d550`.
- `263_V4_2024_25_Karar_Katmani_Uc_Sezon_Tek_Toplu_Rapor_20261121.md`.

**Bu doküman operasyonel aktif karar değildir; araştırma sonuç kayıt belgesidir.**
