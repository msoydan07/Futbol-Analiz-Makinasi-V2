# FUTBOL ANALIZ MAKINASI 2.6.3 — KULLANIM KARARI VE PILOT KAPANIS NOKTASI
**Tarih:** 9 Kasım 2026  
**Karar türü:** Mevcut kanıta dayalı mühendislik/işletim politikası; yeni performans iddiası veya yazılım dağıtımı değildir.  
**Kapsam:** 10 liglik ana 2.6.3; LITE 1.3 kesinlikle ayrıdır.

## 1. YÜRÜRLÜKTEKİ MODEL KARARI
**Ana tahmin motoru: kilitli, mevcut M4.** B, C2, C3 karşılaştırma/yardımcı görüş olarak aynı kod ve parametrelerle kalır. Herhangi bir maçta kullanılabilirlik, doğrulama, kalibrasyon, PAS ve veri yetersizliği etiketleri saklanır. Kullanıcıya sunulan olasılık, garanti veya kupon vaadi değildir.

**Karar verildi; yeni bir pilotun tamamlanması bu kararın ön şartı değildir.**
Yeni araştırma, öğrenme, yeni test ve maç-sonu değerlendirmesi kullanıma paralel devam edebilir. Sırf son maç sonuçları beklentiden farklı çıktı diye modeli yeniden ayarlama veya pilot sayacını sıfırlama yoktur.

**Terfi edilmeyen adaylar:** XGBoost, otomatik model kapısı/karışım, KG-Alt/Üst gol hızı değişimi ve MS-korumalı skor kalibrasyonu. Adaylar araştırma dalında saklanır; üretimde M4'ün 1X2, KG ve 1.5/2.5/3.5 pazarlarını değiştirmez.

## 2. HANGİ KANITLA BU KARAR?
- `research/model-challenge` dalındaki **TENLEAGUE_263_FINAL_MS_MODEL_DECISION_2026_11_09.md**: eşit haftalık kesimde 896 ortak tarihsel maç; M4 1X2 yön %53,35; XGBoost %51,12. M4'ün olasılık hatası da bu karşılaştırmada daha düşüktür. Bu hafta-özel geriye dönük değerlendirme gerçek sabah mühürlü 896 maç değildir.
- `research/model-challenge` dalındaki **KG_GOALS_JOINT_CALIBRATION_DECISION_2026_11_09.md**: 397 ortak tarihsel maçta dört gol pazarını iyileştiren MS-korumalı dağılım adayı, sonuçlar görüldükten sonra tasarlandığı için bağımsız üstünlük kanıtı sayılmaz. Üretime aktarılmaz.
- Kullanıcının ChatGPT Library arşivindeki **2026-11-07_MAKINA_263_TAM_44_MAC_ANALIZI(1).json**, **ANA_263_7_KASIM_2026_SONUC_DENETIMI.md** ve **ANA_263_7_KASIM_GOL_PAZARLARI_MUHENDISLIK_KARARI.md**: 44 maç önü araştırma tahmini; 43 raporlanmış skor, 1 ertelenen maç; 35 dört-model ortak 1X2 karşılaştırmasında M4 19/35, B 17/35, C3 16/35, C2 15/35. Sonuçların bağımsız resmî ağ doğrulaması tüm maçlarda yapılmış değildir. Kalibre tek MS eğilimi tanımlı 25 maçtan 15'i doğru; bu, bahis veya tam pilot başarı yüzdesi değildir.
- **ANA_263_2026_11_08_42_MAC_DORT_MODEL_GERCEK_RAPOR.md**: 8 Kasım için 42 ayrı araştırma adayı; 34 hesaplama, 8 kimlik/kaynak engeli. Bu araştırma raporu 40 kalıcı NEW100 mührü ile aynı kayıt kategorisi değildir.

## 3. 96 SAYISININ DÜRÜST YORUMU VE ARŞİV AYRIMI
- **legacy96**, önceden sabitlenmiş **96 adaylık kohortun adıdır**, 96 farklı maçta doğrulanmış mühür + final skor bulunduğunun kanıtı değildir. Özgün kohort dosyaları değiştirilmez.
- Depoda mevcut SHA-kontrollü maç önü mühürleri: 6 Kasım `forward_quad_263` altında **4**, 8 Kasım `forward_morning_263` altında **40**. `forward_acceptance_263` içindeki 7 Kasım 3 kabul kaydı araştırma/teknik kapsam dışında ayrıca sınıflandırılmalıdır; bunlar otomatik olarak maç sonucu eşleşmesi sayılmaz.
- **7 Kasım 44 maç araştırması** ayrı kategoridir; NEW100'a geçmişe dönük mühür eklenemez.
- **8 Kasım 42 aday/34 araştırma hesabı** ayrı kategoridir; 8 Kasım 40 ön maç sabah mührüyle körlemesine toplanamaz veya eşleştirilemez.
- `experiments/263/sabah_postmatch_inputs/` altında mevcut araştırma dallarında **0** resmî sonuç-attestation dosyası görülmüştür. Bu yüzden 96/96 veya 95/95 'resmen doğrulanmış ve puanlanmış' iddiası yapılmaz. Kayıt eksikliği yeni pilot başlatmaya gerekçe olamaz; mevcut sonuçlar kendi kanıt kategorisinde ölçülür.
- İleriye dönük kayıt ve sonuç eşleme yapılırsa **aynı SHA, lig, kanonik takım kimliği, kickoff ve sonradan resmen doğrulanan skor** kullanılmalıdır. Tahminler kesinlikle geriye dönük değiştirilmez.

## 4. GÜNLÜK KULLANIM POLİTİKASI (ŞİMDİDEN SEÇİLDİ)
1. Kullanıcının belirttiği veya açıkça istediği tarihteki **başlamamış** kapsam içi maçları mevcut doğrulama kapısından geçir; kapsam dışı maç LITE 1.3'e gider (ayrı çalışma, ayrı arşiv).
2. Maç sabahı mevcut B/C2/C3/M4'ten uygun olanları hesapla; M4'ü ana matematiksel referans olarak kullan. İlk 11 henüz yoksa tek başına durdurma; güncel sakatlık/rotasyon verisi yalnız doğrulandığı ölçüde raporlanır.
3. Hesabı maç başlamadan önce, yeniden hesaplayıp değiştirmeden **kalıcı SHA/commit ile** mühürle. Tekli ve toplu ekran aynı kaydı okusun; MS1/MSX/MS2 ile KG Var, 2.5 Üst yüzdelerini okunabilir göster. Tekil kalibre edilmiş MS pazar yüzdelerini yanlışlıkla normalize 1X2 olarak sunma.
4. Pinnacle fiyatı günlük lig bazında bir kez, ancak açık ve yetkili ücret politikasına uygun koşullarda istenir; yoksa model yüzdesi yine gösterilir ama **değer/EV ve bahis tercihi doğrulanmış gibi sunulmaz**. Ana/alternatif/PAS karar sözleşmesi korunur; sırf %1.5 Üst yüksek diye otomatik tercih yapılmaz.
5. Ertesi gün skorları ayrı sonuç kaydıyla eşleştir; Brier, log-loss, yön, pas ve kapsam istatistiklerini güncelle. Eğitim/iyileştirme olabilir fakat **bu işleme başlamak için yeni pilot eşiği gerekmeyecek**.

## 5. GERÇEK YAZILIM DURUMU VE SINIR
- 9 Kasım itibarıyla varsayılan `main` dalı bu kapsamlı 2.6.3 dosyalarını taşımıyor; çalışan kod/raporlar esas olarak `experiment/263-toplu-karsilastirma` dalında. Bu karar metni **ana dala dağıtım, sistemin uçtan uca otomatik çalıştığı veya canlı kaynak doğrulaması** iddiası değildir.
- `.github/workflows/263-sabah-live-batch.yml` eski manuel akışı bilerek engelliyor; `263-sabah-new100-on-request.yml` yönlendirmesi var. Mevcut günlük otomasyon ve kullanıcı komutlarının her durumda bu iş akışını çalıştırdığı henüz teyit edilmiş değildir.
- Tahmin mührü/sonuç sözleşmeleri, kalibrasyon kilitleri, API günlük kredi korumaları, mevcut otomasyonlar ve LITE ayrımı değiştirilmemiştir.

## 6. SONLU MÜHENDİSLİK TAKİBİ
**Durum defteri:** Son karar = mevcut M4 ile düzenli kullanım politikası; başarı kanıtı = tarihsel kıyaslar + sınırlı gerçek maç araştırması; mevcut engel = sonuç arşivinin farklı kategori ve dallarda olması, sabah istek köprüsünün gerçek üretim uçtan-uca doğrulanmamış bulunması. 

**Öncelik 1:** Sadece mevcut kohort ve dosyaları, skor/kaynak/eşleşme durumlarıyla *tek kez* sayıp açıklayıcı pilot kapanış raporu üret. Eksikleri 'eksik' olarak kapat; mevcut olasılıkları geriye dönük değiştirme.  
**Öncelik 2:** Halihazırdaki sabah new100 köprüsünün pratik giriş, kalıcı SHA, mobil gösterim ve sonuç-eşleştirme zincirini statik inceleme + ihtiyaç varsa **tek** bütünleşik teknik kabul ile doğrula; gerçekleşmeyen bağlantıyı 'hazır' ilan etme.  
**Öncelik 3:** Gerçekten gerekli tek paket düzeltmeyi ayrı dal/PR'da öner; ana `main` ve veri kilitlerine otomatik müdahale etme. M4 kullanım kararı bu teknik takip boyunca değişmez.

**Bitiş şartı:** 'Yeniden pilot bekliyoruz' değil; **'Kilitli M4 ile analiz kullanım kararı alındı, teknik çalışma akışının tespit edilmiş eksikleri sınırlı şekilde gideriliyor'**. Başarısız bahis veya matematik üstünlüğü iddiası yok.
