# 2.6.3 — ANA TERCİH MEKANİZMASI: İKİNCİ MÜHENDİSİN NİHAİ KARAR NOTU
**Tarih:** 20 Kasım 2026
**Durum:** Test tamamlandı, CI başarılı, **yalnız araştırma dalı**.
**Test:** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44813754512

## 1. Kesin problem tanımı

Makinede iki farklı problem vardır. **(a) Modellerin belirli MS/KG/2.5 olayları için olasılığı doğru ve kalibre etmesi; (b) birbirinden ayrı olasılık ailelerinde üretilmiş yedi market tahmininden maç için tek ana tercihi seçmesi.** Salt 0,64 > 0,62 diyerek sıralama yapmak, KG/2.5 ve MS kalibrasyonu eşit değilse yanlış seçime neden olabilir.

Canlıya yakın model-first kural, **M4'ün Ağustos 2026'dan dondurulmuş ortak gol kalibrasyonuyla hesaplanan MS1/MSX/MS2** üçlüsü + **ham C3 KG Var/Yok ve 2.5 Üst/Alt**. Bundan önceki 873 maçlık ayrıştırma testi MS M4'ün ham yüzdesini kullandığı için canlıya tam yakın değildi. Bu yeni testte orijinal M4 maç-günü lambda değerleri **yeniden tarih öncesi hesaplandı**, orijinal M4 MS/KG/2.5 çıktıları ile rakamsal tutarlılık doğrulandı, ardından **canlı M4 August ortak MS kalibrasyonu** uygulandı.

Kritik tarih kısıtı: August'ta öğrenilen MS parametresini August performansında geleceği görmüş gibi test etmedik. Eylül **328**, Ekim **293**, toplam **621** maçın **615**'inde M4 ve C3 ortak hesaplanabilir. Ayrı 8 Kasım gerçek maç öncesi SHA sonuçları **39** karşılaşmadır; tek maç günü.

## 2. Tam gerçekçi eksik parça

Üretim yönlendirme modülü `historical_probability_reliability_263.py` ve `normal_historical_reference_263.py` maç önü mühürlü geçmiş olaylarla ana seçim skorunu düzeltiyor; bu kaynak mevcut dizinde sadece **8 Kasım tek günün 39 tamamlanmış maçına** dayalı. Bu kayıtlar 13 Kasım'dan itibaren kullanılabilir; Eylül, Ekim ve 8 Kasım maçlarını test ederken bu gelecekteki sonuçları yapay biçimde geçmişe taşıyamayız. Dolayısıyla aşağıdaki `LIVE_SHAPED` araştırma varyantı **M4 August MS + C3 ham KG/2.5 yüzdelerinden en yükseği sıralayan** çekirdeği ölçer; canlıda 13 Kasım sonrasındaki tarihsel 39 kayıtla güncellenen birebir sıralama algoritmasını kanıtlamaz.

**Saptanan ayrı risk:** `rank_candidates` yetersiz veri statüsünde (ör. aynı market/olay çevresinde yalnız 2 maç) bile `(20 × model yüzdesi + gözlenen isabet sayısı) / (20 + n)` ile ana tercih skorunu hareket ettiriyor. Oysa yazılı politika `fall_back_when_sparse: MODEL_PROBABILITY_WITH_EVIDENCE_LABEL` diyor. Bu yüzden küçük ve **tek günlü** n değerleri çok yakın seçeneklerin sırasını değiştirebilir. Daha fazla maç günüyle bağımsız kanıt olmadan bu hareketi güvenilir kalibrasyon olarak göstermek doğru değil.

## 3. Eylül–Ekim (615 ortak maç) aynı maçta tek ana tercih

| Araştırma seçicisi | n | Ana tercih isabeti | Ortalama bildirilen % | Seçilen olay Brier |
|---|---:|---:|---:|---:|
| M4 Ağustos ortak MS + C3 ham KG/2.5 (`LIVE_SHAPED`) | 615 | **%56,42** | %62,48 | 0,243082 |
| M4 aynı MS + C3 KG/2.5 %25, lig geçmişi %75 | 615 | **%57,07** | %59,78 | 0,239392 |
| M4 aynı MS + yalnız lig geçmişi KG/2.5 | 615 | **%57,56** | %60,12 | 0,238904 |

Bu değerler **istatiksel olarak net kazanan** demek değildir. Aynı 615 maçta %25 karışım, ham M4(Ağustos)+C3 seçicisinden **+0,6504 yüzde puan** daha çok gerçekleşti fakat maç günü bloklu %95 aralık **[-2,977; +4,762]**. Brier farkı +0,003690 (%95 **[-0,004180; +0,012583]**). Böyle bir kanıtla aktif sistem değişmemeli.

## 4. Daha yeni ayrı Ekim (293)

| Kural | Ana tercih isabeti | Ortalama verilen % | Seçilen Brier |
|---|---:|---:|---:|
| M4 Ağustos MS + ham C3 | **%55,97** | %63,12 | 0,244754 |
| M4 Ağustos MS + KG/2.5 %25 C3 + %75 lig | **%57,68** | %60,42 | 0,239103 |
| M4 Ağustos MS + yalnız lig KG/2.5 | **%59,73** | %60,74 | 0,238619 |

Ekim'de %25 karışım ana seçimi hamdan **111/293** maçta değiştirdi; +1,7065 yüzde puan isabet ve +0,005652 seçilmiş Brier iyileşmesi, **ama %95 gün-blok belirsizlik isabet [-4,000; +10,345]**, Brier [-0,007488; +0,024969]. Sıfır içeriyor: kesin üstünlük iddiası yok.

## 5. Kasım 8 SHA — bir maç günü, 39 karşılaşma

| Kural | Ana tercih isabeti | Ortalama verilen % |
|---|---:|---:|
| M4 Ağustos MS + ham C3 | **%69,23** | %63,23 |
| M4 Ağustos MS + KG/2.5 %25 C3 | **%69,23** | %60,12 |
| M4 Ağustos MS + yalnız lig geçmişi | **%69,23** | %60,10 |

Aynı isabet yüzdesine rağmen farklı **ana olaylar** seçildi (karışım hamdan 11/39 maçta farklı). **Bu 39 maç bir tek gün**; güvenirliği kanıtlanmış pazarı seçmeyi doğrulayan yeni dönem serisi değildir. Skorların hepsi bağımsız resmi maç ID ile doğrulanmış değil. Bu 39 maç kendi kararını eğitip kendini test etmek için kullanılmadı.

## 6. Ana tercihte sıranın çok yakın olması

Eylül–Ekim'de ham canlıya yakın modelin 615 seçiminden **%30,41**'inde birinci ile ikinci en yüksek olasılığın farkı **en fazla iki yüzde puanı**. %25 karışımlı modelde bu oran **%42,60**. Özellikle örneğin MS1=%62, 2.5 Üst=%64 farkı sadece iki puandır ve farklı kalibrasyonlu ham aileler için gerçek güven farkı anlamına gelmez.

**Karar araştırma biçimi:** Aynı model versiyonu ve aynı maç gününden önce öğrenilmiş pazar/aile bazlı kalibrasyonla yüzdeleri karşılaştır. Birinci ve ikinci çok yakınsa bunları `YAKIN ADAYLAR / AYIRT ETME GÜVENSİZ` diye etiketle; kendiliğinden yapay ayrık bir %63/%64 güveni varmış gibi iddia etme. Bu işaretleme otomatik `PAS`, bahis tavsiyesi veya fiyat kullanımı değildir. Ana tercih kaydedilecekse algoritmanın seçtiği olay kaydedilir, fakat sınır durumu yanında belirtilir.

## 7. Bağımsız mühendisin kararı

**M4/C3 altyapısı 'kusursuz' değil, ancak MS'de yararlı ve KG/2.5'te kalibrasyon ihtiyacı belirtileri tutarlı. Şimdi iş gerçekten ana seçim mekanizmasının yanlış güven karşılaştırmasını azaltmaya yönelmeli.** MS ham M4 değil **mevcut dondurulmuş Ağustos ortak MS kalibrasyonu** canlı seçimde kullanılmalı. KG ve 2.5'e %25 C3 + %75 geçmiş lig oranı araştırma/gölge adayına öncelik verilebilir; çünkü ana isabetten çok **seçim olasılığı ile gerçekleşmenin daha iyi uyuşması** umudu var. Fakat 2025/26 M4 ayar dönemiydi ve 2026/27 daha önce araştırıldı, dolayısıyla bu yöntem **kesin kazanmış, terfi etmiş değil**.

**En önemli bulgu:** Mevcut `historical_probability_reliability_263.py`, yetersiz gerçek mühürlü örneklemin olasılık skorunu hareket ettirmesine izin veriyor. Öneri, az veri halinde geçmiş oranı yalnız açıklama olarak kullanmak ve sıralama ağırlığını sıfırda tutmak; gerçek maç-günü mühürlü arşiv farklı günlerde yeterince büyüdüğünde bunun kronolojik bağımsız etkisini test etmek. Bu kullanıcıdan yeni bir pilot istemek değildir; **halihazırda var olan mühür sonuç otomasyonu** ile oluşacak veri dışında yeni kaynak gerektirmez. Canlı kodu şimdi değiştirmek için onaylı bağımsız kanıt yok.

**Eylem:** Ana 2.6.3, eski SHA mühürler, haftalık/günlük planlar, xG veri kaynağı sorunları ve PDF iş akışı **dokunulmaz**. Oran/EV/ROI/oynama ve başarı garantisi iddia edilmedi.

## Kanıtlar

- [Başarılı gerçek M4 August MS seçici kontrolü](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44813754512)
- [Ham sonuç ve belirsizlik](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/12_main_choice_layer_result.json)
- [Yeniden çalıştırılabilir kaynak](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-independent-math-audit/research/263_independent_audit/audit_main_choice_layer.py)
- [Kullanılan canlı karar modülü](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/model_first_decision_263.py)
