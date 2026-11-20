# 20 Kasım 2026 — 39 yerine binlerce maç: ana tercih güvenilirlik testinin kararı

## Neden 39 değil?

İlk referansın **39 maçı**, 8 Kasım'dan gelen gerçek **maç başlamadan önce SHA ile mühürlü**, sonuçlanmış **tek bir maç günüdür**. Bu sınır, modelin geçmişe dönük hesabına engel değildir. Bugün bu eksikliği giderdik: orijinal SHA doğrulanmış 4.413 maçlık arşivde 2025/26 için **2.922** ve 2026/27 için **880**, toplam **3.802** maçın tarih sıralı olasılıklarını kullandık. Ortak M4+C3 pazarları **3.771** maçta üretilebildi (2025/26 **2.898** + 2026/27 **873**). Bu 3.771 test, mühürlü maç sayısını artırmaz.

Tüm karşılaştırmalar maçın içinde bulunduğu güne ait sonuçları hariç tutar; önceki günlere ait tarih sıralı rekonstrüksiyondan geçmiş benzer oranlar alınır. 2025/26 sezonu M4 parametre seçiminde kullanıldığı, 2026/27 daha önce araştırıldığı için **bağımsız kör final kanıt değildir**.

## Geniş tarihsel dönemlerde karar vericilerin ölçümleri

**Amaç:** MS1/MSX/MS2, KG Var/Yok ve 2.5 Alt/Üst arasından her maç için yalnızca bir olay seçmek. Pazar oranı/EV/ROI test edilmiyor. 

| Seçici | 2025/26: 2.898 maç isabet | 2026/27: 873 maç isabet | Birleşik 3.771 isabet |
|---|---:|---:|---:|
| Ham yüzde en yüksek | **%57,246** | %57,617 | %57,332 |
| Mevcut geçmiş formülünün geriye dönük benzeri; destek sınırı yok | %55,590 | %58,992 | %56,378 |
| Benzer olay geçmişi en az 20 ise düzelt, değilse ham | %56,108 | %59,450 | %56,881 |
| Benzer olay geçmişi en az 50 ise düzelt, değilse ham | %56,522 | %60,023 | %57,332 |
| Pazar geçmişini bütün 10 ligden havuzla | %56,073 | **%61,168** | %57,253 |
| En az 20 destekli geçmiş + aile normalizasyonu | %56,729 | %59,908 | %57,465 |
| M4 ham MS; KG/2.5 için %25 C3 ve %75 geçmiş lig oranı | %56,970 | %59,794 | **%57,624** |

2026/27'de havuzlanan 10-lig geçmiş yaklaşımı hamın üzerinde **+3,551 puan** isabet gösterdi, tarihe göre gün-bloklu %95 belirsizlik **[+0,556; +6,963]**. Ancak **2025/26'da hamdan 1,173 puan daha düşük** çıktı. Bu ikisi, modelin pazarların tümünde kanıtlanmış genel üstünlüğü anlamına gelmez. Birçok aday görüldüğü için bunlar bağımsız seçim/çoklu test düzeltmesi yapılmış sonuçlar değildir.

İki sezon birleştirilince KG/2.5 için %25 C3 kuralı hamdan sadece **+0,292 puan** fazla isabet verdi (3.771 eşit maç); gün-bloklu %95 fark **[-1,051; +1,837]**. Ancak seçilen tek olayın Brier puanında ham **0,247542**, %25 karışım **0,240926** çıktı, gün-bloklu iyileşme aralığı **[+0,003793; +0,009907]**. Bunun da 2025/26 model geliştirme veri sızıntısı / çoklu seçim bağlamında değerlendirildiği unutulmamalı.

## Canlıya daha yakın M4 Ağustos ortak MS kalibrasyonlu ayrı dönem

Ağustos 2026'da öğrenilen M4 ortak MS kalibrasyonu Ağustos'a uygulanmadı. Eylül–Ekim'in **621** maçında, **615** ortak M4+C3 tahminine sahip maç; **39 farklı maç günü** üzerinde katmanlı tarihsel karar formülü test edildi. Burada önceki sezon raw M4 MS tahminlerini yeni kalibre MS tarihçesiymiş gibi göstermedik.

| Seçici | Eylül–Ekim 615 maçta ana isabet |
|---|---:|
| Kalibre M4 MS + ham C3 KG/2.5, salt en yüksek yüzde | %56,423 |
| Aynı pazarların geçmiş referans formülü, destek sınırı olmadan | %57,073 |
| En az 20 örnek varsa tarihsel düzeltme | %58,211 |
| En az 20 destekli düzeltme, her ailede toplam 1 normu | **%58,537** |
| KG/2.5 %25 C3 + %75 geçmiş lig | %57,073 |

Bu farkların maç günü bootstrap güven aralıkları ana isabet açısından **sıfırı kesiyor**, yani birebir üretime geçmek için kesin kanıt sayılmaz.

Ekim tek başına (%95 belirsizliği daha yüksek): ham %55,973; geçmiş formülü %57,679; destekli aile normalize %57,338; %25 karışım %57,679.

## Ana mesele

1. **39'a takılmak gereksizdi; geçmiş gerçek sonuçlar + tarih öncesi model hesapları 3.771 test maçı sağladı.** Asıl eksik SHA geçmişi ile retrospektif as-of gözlemini yanlışlıkla aynı veri türü gibi sunmamaktır.
2. Ana pazar seçimi ham olasılığın en yüksek olmasından ibaret kalmamalı; ama geçmiş başarı formülü de daha çok veri görünce tutarlı kesin kazanan olmuyor: 2025/26 ve 2026/27 yönleri değişiyor.
3. **Az geçmiş veriyle ana tercihin gizlice değişmesi riski** sürüyor. Üretimde aynı market/aynı model sürümüne ait benzer ihtimal sayısı azsa ham modele dönmek, en azından araştırma düzeyinde anlamlı bir güvenlik kuralıdır; bunu canlıya şimdiden geçirmek için bağımsız kanıt yeterli değil.
4. xG yok. MS/KG/2.5 olasılıkları ve kendi pazar kalibrasyonuyla çalıştık; yedi olayı yedi bağımsız maç gibi saymadık.
5. 4.518/4.617/4.618 gibi ayrı havuzlar farklı kökenli; eşleştirilmeyen gelecek tarihli oranlar/gol verileri sessizce karıştırılmadı.
6. **Ana makine, SHA'lar, otomasyonlar, kilitli karar katmanı, PDF ve mevcut ligler değişmedi.** Ayrı research dalında bitmiş denetim, kod ve tam ham sonuç var.

## Tekrarlanabilir araştırma
- [Başarılı 3.802 maç kaynaklı geçmiş güvenilirlik test akışı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44815020650)
- [Tam JSON, dönemler ve gün-bloklu belirsizlik aralıkları](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/15_historical_ranker_large_sample.json)
- [Çalışan test kodu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/audit_ranker_large_sample.py)
