# Futbol Makina 2.6.3 — bağımsız ikinci mühendis kapanışı (10 Kasım 2026)

**Özet teknik hüküm:** Makine üretimdeki M4 hesaplarını ve 40 gerçek maç önü mührü koruyarak çalışmaya devam edebilir; ancak “%70 diyorsa gerçekten %70 gerçekleşiyor” ve “bütün belirsizlikler giderildi, tam doğrulanmış” iddiaları **kanıtlanmış değil**. İkinci mühendis, karar/sunum katmanında **somut bir ortak olasılık tutarsızlığı** buldu. Sadece etiketleme/gösterim düzeltildi, matematik seçimi veya mühürler **değişmedi**.

## 1. Yalnız gerçek kanıta dayanan bulgular

- 8 Kasım `new100`: GitHub'daki iki batch'te **40** SHA-tutarlı maç önü mühür; sonradan web araştırmasında **39** skor ve **1** erteleme. Sonuçların **35'i** lig/kulüp kaynaklı, **4'ü** medya çapraz kontrolüyle yorumlanmış. Bunlar bağımsız resmî sonuç sağlayıcısı doğrulamasına / insan onaylı `sabah_postmatch_inputs` attestasyonuna eşdeğer değildir.
- 40 mühürde kullanılabilir ham B/C2/C3/M4 maç tahminleri için **H+D+A=1**, KG Var+Yok=1, gol çizgisi Üst1,5 ≥ Üst2,5 ≥ Üst3,5 ve tamamlayıcı alt çizgileri tutarlı çıktı. Bu, tahminin doğru olacağını değil olasılığın matematiksel bütünlüğünü gösterir.
- **Asıl tespit:** Karar motoru geliştirme (DEV) kalibrasyonunda MS1, MSX ve MS2'yi ayrı pazar / baz / ağırlıkla işlediğinden 40/40 geçmiş karar dosyasında üç bireysel `calibrated_probability` **toplamı 1 değil**. Örneğin bir dosyada toplam **1,089548 (%108,9548)**. Ham M4 üçlü dağılımı bozuk değildir. Üç bağımsız kalibre `q` rakamını *ortak 1-X-2 olasılık dağılımı* olarak göstermek yanlıştır. Bu sonuç, ayrı her marketin EV hesaplamasının otomatik olarak matematiksel olarak yanlış olduğunu kanıtlamaz; ancak üçlü vektör gibi sunulamaz.
- **%70 denetimi:** M4'ün en yüksek MS yön olasılığı %65–75 olan **4** web araştırması maçında **4/4** yön doğru, ortalama tahmin **%68,87**; bu sadece **tek UTC maç günü**. Basit Wilson %95 referans aralığı yaklaşık **%51–100**, aynı gün maç bağımlılığı ve kaynak belirsizliği hesaba katılmıyor. **%70'in güvenilir olduğuna kanıt değildir**.
- Aynı M4 araştırma web kümesinde %65–75 tahmin dilimi için KG Var **4/6**, Üst2,5 **5/7**, Üst1,5 **9/11**. Farklı marketler ve aynı maçlar korelasyonlu; 4+6+7+11 toplanıp “28 bağımsız %70 örneği” yazılmaz. Birincil kaynak sınıfında M4 en yüksek MS yönünde bu dilim **3/3**, sadece bir gün.
- 39 web araştırması skorunda M4 MS Brier **0,509959**, yön doğru **25/39**; KG Brier **0,248164**, Üst2,5 Brier **0,262744**. Aynı 39 maçta C3 Üst2,5 Brier **0,247555** ile daha düşük. Fakat bu aynı gün ve önceden incelenmiş veri olduğundan M4 yerine C3'e otomatik geçilmedi.
- Önceden görülen **896** adet haftalık aynı-bilgi kesimli tarihsel M4–XGBoost karşılaştırması, 896 gerçek sabah mühürlü ileri maçın kalibrasyon kanıtı değildir. Bu bağlam eski araştırma olarak ayrı tutulur.

## 2. Ne doğru yapıldı, neyi yaparken başka bir hata üretildi?

| Katman | Sağlam kazanım | Kalan sorun / yeni yanlışın kaynağı | Bu tur mühendis kararı |
|---|---|---|---|
| Tahmin matematiği | B/C2/C3/M4 ham MS/KG/Alt-Üst yüzdeleri tutarlı; kronolojik model denemeleri var | Bu yüzdelerin veri-kalite ve lig/olasılık dilimine göre gelecekte kalibre olduğu tam gösterilmedi | **Model aynı**, yüzde güvenilirliği ayrı izlenecek |
| Karar / DEV kalibrasyon | Pazar bazında geliştirme becerisi ve PAS mantığı var | Bağımsız MS1/X/2 kalibrasyonları ortak dağılım vermiyor (40/40), farklı anchor modeli seçiyor | **Matematiği çarpıtıp normalize etme YOK; tek pazar açıklaması zorunlu** |
| Kullanıcı telefon/PDF | Tekli ve toplu ekran SHA mühürlerinden okuyor, fiyat yoksa piyasa çizgi | Daha önce “Kalibre MS yönü” ifadesi ortak tutarlı 1X2 olasılığı izlenimi verebiliyordu | İfade **gerçek 2.6.3 deney dalında değiştirildi**; ekran testi yeşil |
| Skor ve kanıt | 40 gerçek pre-KO mühür, 39 web-araştırma skoru, ertelenen maç ayrımı | Sonuç tarafı lig+takım adıyla eşlendi; **aynı kanonik fikstür ID'siyle bağımsız sonuç teyidi / kalıcı attestation yok** | Araştırma/kanıt kategorileri karıştırılmayacak |
| Fikstür/veri | Resmî kaynak kapısı, lig kimliği ve sabah zamanı doğrulama kontrolleri var | Bazı liglerde tam fikstür, oyuncu/kadro, kupa rotasyon bilgisi, as-of xG ve hak/lisans kabulü eksik | **Eksik veriyi uydurma yok; güven/pas etiketi** |
| Piyasa değeri | Sabah tek seferlik fiyat / S2 / marjsız fiyat koruma sözleşmesi var | 8 Kasım batch'te oran API çağrısı 0 ve bütün kararlar araştırma PAS; fiyat/ROI doğrulaması yok | **Kârlılık/EV başarısı iddiası yok** |
| Dağıtım/operasyon | Araştırma dalında birden fazla başarılı CI ve manuel Git kaynak köprüsü var | Varsayılan `main` henüz bu 2.6.3 altyapısının dağıtılmış sürümü değil; tek komutla her koşulda uçtan uca canlı kabul garanti değil | **Canlı tam hazır etiketi YOK** |

## 3. Bu turda gerçekten uygulanan düzeltme

- Ayrı araştırma dalı `research/263-second-engineer-audit`: `second_engineer_calibration_263.py`, `second_engineer_decision_263.py`, sentetik ve gerçek 40 mühür üzerinden hata denetimleri, salt-okuma kanıt raporları:
  - [39 maç / %70 dilimleri raporu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-second-engineer-audit/reports/263_second_engineer_70pct_webreview_2026-11-10.json)
  - [40/40 DEV üçlü toplamı tutarsızlığı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-second-engineer-audit/reports/263_second_engineer_dev_ms_2026-11-10.json)
  - [Araştırma CI başarılı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42714988285)
- Kullanılan gerçek 2.6.3 dalı `experiment/263-toplu-karsilastirma`: sadece `sabah_mobile_screens_263.py`, `sabah_mobile_approved_pdf_263.py` **sunum etiketleri değiştirildi**. Görünüm hâlâ aynı siyah-beyaz/yüzde/PAS düzeninde. “DEV tek-market, 1X2 dağılımı değildir” vurgusu eklendi. Araştırma/deney dalında özgün 40 mühür ve 40 karar dosyası içerik hash'i **birebir aynı**.
- Sadece bu metin/sunum güncellemesi için kabul testi: [mobil+PDF güvenlik kabulü](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42715307526) **success**; [sabah entegre bileşenler](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42715307404) **success**.
- Orijinal `m4_integrated.py`, `four_model_value_policy_263.py`, `sabah_batch_263.py`, `sabah_postmatch_new100_263.py`, `forward_calibration_bridge_263.py`, 4.518 kabul edilmiş tarihsel veri CSV SHA'sı, eski 40 forecast ve 40 decision dosyasının Git blob SHA'sı **değişmedi**. `main`, LITE, futbol otomasyonunun sabah saatleri, bahis oranı hakkı ve basketbol projesi değiştirilmedi.

## 4. Nihai karar ve sonlu bekleyen dış kanıt

**Bu tur için DENETİM TAMAMLANDI / SOMUT SUNUM HATASI DÜZELTİLDİ / MATEMATİK TERFİSİ YOK.**

Teknik öncelik 1: Orijinal 40 maç ve gelecek mühürler için resmî maç kimliğiyle eşleşen ve kaynak/sonuç zamanı teyit edilen postmatch kayıtları. Eksikse *eksik* kalsın; isim eşleştirmesiyle otomatik resmî onaya geçmesin.

Teknik öncelik 2: Zaman içinde biriken, birbirinden ayrı maç günlerindeki aynı pazar/bant tahminlerinin **gerçek kalibrasyon** testleri (ör. M4 MS en yüksek %65–75). Tek bir gün ve n=4 üzerinden güven katsayısı uydurma. Etkin hata izleme: kalibrasyon, Brier, log loss, yön, model kapsamı ve kaynak tabakası. İncelenmiş kümeye hiperparametre ayarı yok.

Teknik öncelik 3: Gerçek kullanılacak sabah isteğinin `2.6.3 GitHub request → resmî kaynak → mühür → kullanıcı mobil görünüm → bağımsız skor` zincirinin güncel lig/gün bazında doğrulanması. Eksik rota/veri/oyuncu ile sonuç olasılığı değiştiriliyormuş gibi yapma.

**Amaç sürekli yeni pilot ve yeni motor değil.** M4 mevcut çalışma motoru olarak kalır; doğrulanamayan bilgide `PAS / VERİ YETERSİZ / BİLİNMİYOR` kullanılır. Bir sonraki aşamanın kapanması için yeni resmî kanıt gerekir. Bu kayıt “makine başarı garantisi verdi” anlamına gelmez.
