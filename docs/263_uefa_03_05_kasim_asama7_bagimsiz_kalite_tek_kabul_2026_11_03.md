# Futbol Maç Analiz Makinası 2.6.3 — UEFA 3–5 Kasım / AŞAMA 7 BAĞIMSIZ KALİTE KABULÜ

**Tarih:** 3 Kasım 2026 (Türkiye). **Kapsam:** 17 fikstür, 34 takım, Şampiyonlar Ligi + Avrupa Ligi.  
**Teknik karar:** **BAĞIMSIZ HAM VERİ + MATEMATİK DENETİMİ KABUL.** **Tahmin kalibrasyonu / isabet başarısı onaylanmadı.** **Tahmin kilidi / pilot başlatılmadı.**

## 1. Tek kanıtlı toplu koşu

- GitHub Actions: **[41594756152](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41594756152)** — **SUCCESS**.
- **14/14 yeni (Aşama 6'dan ayrı) matematik ve veri güvenliği testi başarılı**. Önceki 124 retrospektif maç veya Aşama 6'nın 14 testi yeniden koşturulmadı.
- Yeni gerçek veri denetimi **bir kez** çalıştırıldı; bütün girdiler daha önceki dört GitHub artifact kaydından SHA-256 doğrulamasıyla okundu. Veri sağlayıcılarına yeni dış ağ çağrısı yapılmadı.
- Tek kanıt çıktısı: GitHub artifact **13211860984**, adı \`263-uefa-17-stage7-independent-quality-NO-PREDICTIONS\`, içinde yalnız \`17_match_independent_quality_NO_PREDICTIONS.json\`. JSON SHA-256 **6dc733f8394833733c902d4702c9c945a757c48abdc06f840b48266da3fb6097**.
- Denetim saati **2026-11-03 07:12:27 UTC (10:12:27 TSİ)**; ilk seçili UEFA başlangıcı **2026-11-03 17:45 UTC (20:45 TSİ)**. Ancak bu saat **tahmin kaydedildiği anlamına gelmez**; yalnızca denetimin o tarihte gerçekleştiğini kanıtlar.
- Değişiklik yalnız \`experiment/263-toplu-karsilastirma\` dalında. \`main\` değişmedi.

## 2. Gerçek veri kaynağının ikinci, bağımsız okuması

Aşama 4'ün oluşturduğu özetleri kabul etmekle yetinilmedi. **9 gerçek sağlayıcı CSV'si** yeniden (offline, arşivden) okundu. Aşama 4'ün veri işleyicisi çağrılmadan, farklı bir hesap uygulamasıyla:

- **812** tamamlanmış 2026/27 yerel lig sonucu skor/tarih/lig ve kulüp kimliğine göre çözüldü; arşivdeki her kaynağın SHA-256 değeri önceki denetimde saklanan değerle karşılaştırıldı.
- **34 takım için** ev/deplasman maç sayıları, her rolde atılan/yenilen gol, lig toplamları ve son beş maçın puanları tekrar üretildi.
- **170/170** son beş maç rakibinin **o geçmiş maçtan *önceki*** yerel lig PPG istatistiği bağımsız olarak tekrar hesaplandı ve tam eşleşti.
- Fikstürlerin sonuçları veya maçın kendi günü / sonrasındaki yerel lig sonuçları veri hesaplarına girmedi. Aynı gün skorlu veya gelecekteki satır kaynakta bulunursa denetim reddediyor.
- Dokuz ligin her birinde arşivin son tamamlanmış maç tarihi **1 Kasım 2026**. Bunlar maç önü sonuç veri kaynaklarının tutarlı olduğuna dair kanıt; her sonucun bağımsız federasyon düzeyinde ikinci kaynakla teyidi anlamına gelmez.

| Lig | Arşivdeki 2026/27 tamamlanmış maç |
|---|---:|
| İngiltere Premier League | 89 |
| Almanya Bundesliga | 72 |
| İspanya La Liga | 108 |
| İtalya Serie A | 98 |
| Fransa Ligue 1 | 80 |
| Hollanda Eredivisie | 99 |
| Portekiz Primeira Liga | 88 |
| Belçika Pro League | 89 |
| Türkiye Süper Lig | 89 |
| **Toplam** | **812** |

## 3. Matematik için bağımsız doğrulama: iki karşılaştırma kolu

Aşama 6'nın kullandığı tarihsel Poisson hesaplarını birebir kopyalamak yerine, ikinci denetleyici:

1. Takımların kendi ligleri içindeki **rol bazlı ev/deplasman gol katsayılarını** bağımsız cebirsel gösterimle hesapladı; yalnızca dondurulmuş **M0 UEFA 2025/26 eğitim tabanları** ve \`k=5\` yumuşatma kullandı.
2. **M0+Elo** kolunda aynı M0 değerine yalnız daha önce ölçülmüş, **üretime onaylanmamış** \`β=0,525476...\` ve ortak beyondELO farkı \`(Ev−Dep)/400\` uyguladı. İkinci bir ülke bonusu, yerel Elo, haber/kadro katsayısı veya son rakip PPG düzeltmesi uydurulmadı.
3. Orijinal Poisson hesaplayıcısının 26 gol seviyeli kestirimi yerine, **0–60 gollü bağımsız dağılım ve farklı toplam yöntemi** ile 1X2, 2,5 Üst ve KG değerlerini hesaplayıp 17 maç × 2 kol boyunca bellek içinde karşılaştırdı.
4. **En yüksek mutlak hesap farkı: 8,881784197001252×10⁻¹⁶**, yalnızca kayan nokta hassasiyeti düzeyinde. 61 gollük ayrık dağılımın en büyük normalizasyon kaybı **2,220446049250313×10⁻¹⁶**.
5. **0 kez beklenen gol uç aralığına kırpma** (0,15 veya 5,00) gerçekleşti. Matematik sonucu sınırlar tarafından yapay olarak şekillendirilmedi.
6. Birim denetiminde aşırı düşük/yüksek gol parametrelerinde olasılık toplama, simetrik gol oranı, ev/deplasman yönü, 2,5 Üst ve KG kapalı formülleri, sıfır Elo farkı, Elo etkisinin tek bağımsız değişken olması, kasıtlı bozulmuş hash ve geçmiş deneye izinsiz model onayı verilmesi kontrol edildi.

**Denetim başarılı demek tahminin yüksek isabetli olduğu demek değildir.** Yanlış model de matematiksel olarak doğru uygulanabilir. Kalibrasyon, keskinlik, geçmiş testin bağımsızlığı ve gerçek ileriye dönük tahmin kalitesi **henüz kanıtlanmadı.**

## 4. Bilinçli olarak açık kalan güvenilirlik sorunları

- **Elo β katsayısı** 124 maçlık geriye dönük keşif deneyindendir. Ocak holdout'ında sıfırı içeren belirsizlik aralığı ve geçmiş kaynakların *first_seen* kanıt eksikliği nedeniyle **resmî/üretim katsayısı değildir**.
- UEFA maçının kulüp ID'si ile kendi yerel kanonik takım ID'miz arasında ortak, bağımsız resmî UEFA numerik ID doğrulaması henüz yok. 17 maç kimliği resmî UEFA maç sayfasına ve kanonik lig kayıtlarına dayalı, ancak bunu ortak kulüp ID kanıtı gibi raporlamıyoruz.
- Avrupa Ligi oyuncu/sakatlık haberleri ikincil kaynaklı; kulüp teyidi ve resmî maç günü ilk 11'ler henüz doğrulanmadı. **İlk 11 açıklanmadı diye veri/matematik analizi durmaz.**
- 17 maçlık üç günlük ileri dönem deneyine bakarak modelin geniş futbol evreninde istatistiksel olarak üstün olduğunu ilan edemeyiz; ilk testler ancak ileri dönem veri birikiminin başlangıcı olur.
- UEFA sayfasının GitHub Actions tarafından canlı okunmasındaki daha önce belgelenmiş ağ engeli sürüyor. Fikstürün resmî kaynaklı **web destekli** doğrulanması ile GitHub'ın canlı otomatik doğrulaması ayrı tutuluyor.
- **Tahmin kayıtları hâlâ SIFIR.** Aşama 6/7 geçici matematik hesapları sonradan gerçek bir *maç önü tahmin* gibi gösterilmeyecek.

## 5. Nihai mühendislik kararı ve sonraki safha

| Konu | Karar |
|---|---|
| Aşama 7 — gerçek arşiv kaynağı bütünlüğü | **KABUL** |
| Aşama 7 — 34 rol profili ve 170 geçmiş rakip kıyası | **KABUL** |
| Aşama 7 — bağımsız iki kol Poisson matematiği | **KABUL** |
| Canlı model isabeti / güven kalibrasyonu | **HENÜZ KANIT YOK** |
| Elo katsayısını ana modele geçirmek | **ONAY YOK** |
| Aşama 8 — iki modelin değişmez maç önü tahmini kilidi | **HENÜZ YAPILMADI** |
| Ana 10 lig, B/C2/C3/M4, oran/EV, pilot | **DEĞİŞMEDİ** |

**Aşama 7 sonucuyla: teknik mimari ileriye dönük *gölge kayıt deneyi hazırlığı* için incelenmiş durumda.**

**Aşama 8, kullanıcı açıkça geçmemizi söylediğinde** ayrı, kontrolü kapalı tutulmuş bir adım olarak açılmalıdır. O safhada her maçın gerçek başlangıcından önce iki modelin tahminleri ve kaynak SHA'ları birlikte yazılıp kilitlenmeli; GitHub commit ve gerçek UTC işlem anı kontrol edilmeli; başlama saati geçmiş maç *asla geriye dönük prematch kayıt* olarak yazılmamalıdır. Güncelliği aşmış 5 Kasım kaynak ve EL haberleri yeniden kaynak kontrolünden geçirilmelidir. Maç sonrası gerçek sonuçlar daha sonra ayrı toplu karşılaştırmada skorlanacak; pilot 0/100 değişmeyecek.

**Tek rapor; yeni açık veri problemi olmadıkça bu deneyin kontrolünü veya 124 maç retrospektif karşılaştırmasını tekrar çalıştırmayın.**
