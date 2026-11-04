# 2.6.3 — 880 maçlık gol/KG karar yöntemi: TEK mühendislik sonuç raporu
**4 Kasım 2026 — Deney dalı; üretim kararı verilmedi**

## 1. Provenans / çalıştırılmış kanıt

- Kaynak: **4.413** maçlık donmuş arşiv, SHA256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`. Son 4.509 insan kabulü bekleyen yeni aşamalı veri buraya karıştırılmadı.
- 2026/27: toplam **880** (Ağustos **259**, Eylül **328**, Ekim 29'a dek **293**).
- [İlk toplu gerçek as-of dört-model geçmiş test run 41836437930](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41836437930), başarılı; artifact **13327550424**: `first_goal_pas_report.json` + `first_goal_market_asof_predictions.csv`. Bu CSV **o maç gününde mühürlü gerçek tahmin değildir**, o gün öncesine kesilmiş verilerle **retrospektif simülasyon**.
- [İkinci hızlı kaynak tekrar kullanılma test run 41836896944](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41836896944), başarılı; artifact **13328090521**: `stage2_model_coverage_decision_research.json`. **Dört modelin geçmiş hesaplarını tekrar çalıştırmadı**; sadece birinci artefaktı okudu.

## 2. İlk test: C2 kanonik politika

| Kural | Ekim n | Ana aday | PAS | 1,5 Üst payı | Seçilmiş olay Brier | *Aynı olayın* geçmiş lig bazı Brier |
|---|---:|---:|---:|---:|---:|---:|
| T0: p ≥%75, stres ≥%70 | 293 | 89 | 204 | %76,40 | 0,209055 | 0,191152 |
| T1: p ≥%70, stres ≥%65 | 293 | 105 | 188 | %76,19 | 0,191618 | 0,175925 |
| T2: erken-season C2 kalibrasyonu | 293 | **0** | 293 | — | — | — |

**Kök neden:** Ağustos–Eylül 587 maçta **C2 kapsamı sıfır**, çünkü C2'nin mevcut sezon ev/deplasman bağlamı koşulu karşılanmadı. Ekimde bile C2 yalnız 105/293 maçta mevcut. Bu yüzden T2'nin 293 PAS'ı **kötü kalibrasyon kanıtı değil, hiç eğitilememiş bir sistemin başarısız kapsama testi**. T0/T1 sadece 1,5 Üst → 3,5 Alt gibi yüksek tabanlı pazarlara yığılmış; Brier'leri basit bazdan daha kötü.

## 3. Tekrar fit yapmadan ikinci karşılaştırma

M4 ve C3'ün aynı Ağustos–Eylül gelişim kayıtları sırasıyla **587 / 580** maçta mevcut; Ekim ikisinde de **293/293**. Her pazar için eğitim dönemindeki tahmin/baz/gerçekleşmeden **tek parametrik, 0..1 arası baz-çekmeli kalibrasyon** öğrendik; daha sonra Ekimde `p_kalibre ≥%60`, `p_kalibre - p_lig_bazı ≥2,5 yüzde puan`, önceden seçilen `lift +0.1*p` sıralamasıyla **iki araştırma seçici** oluşturduk: salt matematik filtresi ve buna ek olarak **DEV Brier skill >0** filtresi.

| Araştırma seçici | Ekim ana aday | PAS | 1,5 Üst | 3,5 Alt | Seçilmiş olay Brier−lig bazı |
|---|---:|---:|---:|---:|---:|
| M4, skill filtresi olmadan | 184 | 109 | 26 | 73 | **−0,023827** |
| **M4, DEV skill >0** | **141** | **152** | **0** | **73** | **−0,031387** |
| C3, skill filtresi olmadan | 178 | 115 | 30 | 81 | **−0,023962** |
| C3, DEV skill >0 | 156 | 137 | 0 | 81 | **−0,026927** |

- M4 skill filtresi ana aday dağılımı: **MS1 56**, **MS2 12**, **3,5 Alt 73**. Alternatif aday yalnız **3/141** maçta oluştu; ikinci bir seçim uydurulmuyor.
- M4 seçilenlerin gerçekleşme oranı **%65,25**; bu olasılık doğruluğunu tek başına anlatmaz. Seçilmiş aynı olayın Brier'i ile **kendi** eski lig bazını karşılaştırmak gerekir.
- **Etkili fakat tehlikeli:** 1,5 Üst payının sıfıra düşmesi, sistemin 3,5 Alt'a kayma eğilimini de gösteriyor. **Herhangi bir pazarın tekelleşmesi** (1,5 Üst, 3,5 Alt, çifte şans) izlenecek; bir pazarı keyfi yasaklama veya kota koyma yok.

## 4. Gün-gruplu ek duyarlılık (yerel, aynı eski CSV kullanılarak, yeni tahmin fit'i yok)

M4 DEV skill>0 seçici için Ekim **141 tercih, 16 farklı maç günü**. Seçilmiş olayın model Brier eksi **aynı olay** as-of lig baz Brier farkı `−0,031387`. Maç günlerini yeniden örnekleyen yaklaşık 5.000 tekrar içeren bootstrap `seed=20261104` ile **yaklaşık %95 örnekleme aralığı [−0,0534; −0,0068]**. Bu aralık pozitif bir iyileşme işaretidir; fakat Ekim daha önce incelenmiş, kümeli gün sayısı küçük ve sonuç liglere göre değişiyor. **Gelecekteki kârlılık veya genel hata üstünlüğü için güven aralığı değildir.**

Liglerde M4/skill>0 farkı: ENG2 **+0,0618**, NED1 **+0,0050** (bazdan kötü); ITA1 **−0,1601**, TUR1 **−0,0683** gibi başkalarında iyi. Örneklem sınırlı; lig bazında karar eşikleri öğrenmek için çok küçük.

## 5. SONUÇ: Ne yapıyoruz ve neyi YAPMIYORUZ?

**Kabul edilen mühendislik yönü:** Eski tarihlerde basit yüzdelere göre en olası pazarı sıralamak yerine, **pazarın kendi as-of tabanına göre gerçekten ek bilgi** getirip getirmediğini, geçmiş pazar bazlı Brier/log-loss ve modelin kullanılabilirliğini birlikte değerlendirmek. Mevcut çok sıkı C2 kanonik karar kuralı erken sezonlarda büyük boşluk yaratıyor; **M4/C3 geçmişe dönük destekleyici aday** ama C2 yerine otomatik yeni ana model ilan edilmedi.

**KANITLANMADI:** T2 yeni yaklaşımının canlı maçlarda iyi olduğu, M4'ün kanonik modele üstünlüğü, güvenilir gerçek tarihli bahis oranlarından EV veya ROI, 100 ileri maçta üstünlük. Ekim daha önce model karşılaştırmalarında kullanıldı; bağımsız final holdout değildir. Geçmiş günlere dönük simüle edilen tahminler real-time pre-KO kayıt sayılmaz.

**Sıradaki tek anlamlı aşama:** 6–8 Kasım'daki gerçek maçlar için **analiz anında mühürlü dört-model + aynı anlı doğrulanmış piyasa oranları**, gerçek sonuçtan sonra sabit Brier/LogLoss ve PAS/kapsama değerlendirmesi. T−60 insan kabulü, kaynak/fi̇kstür/fiyat kapıları sahte onay ile geçilmeyecek. Modüller/sayılar yeniden oynanmayacak; yeni maç sonuçları biriktikçe önce eski politikalar sabit koşullarda karşılaştırılacak. Geliştirilmiş seçici ancak ayrı ileri kanıtla terfi ettirilecek.

**Operasyon:** `main`, B/C2/C3/M4 formülleri, mevcut A/B/S1/S2 eşikleri, 96 aday kapsamı, resmî 100 maç ileri pilotu ve 4.413 maç kaynak SHA'sı değişmedi. Bu rapor **bir araştırma sonucudur; bahis önerisi değildir**.
