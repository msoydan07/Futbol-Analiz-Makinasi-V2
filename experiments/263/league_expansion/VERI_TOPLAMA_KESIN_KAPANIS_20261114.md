# 22 lig × iki sezon — VERİ TOPLAMA AŞAMASI KESİN KAPANIŞ
**14 Kasım 2026 · Son maç kesimi: 13 Kasım 2026 · Sadece araştırma dalı**

## Amaç ve sınır
22 lig (13 analiz hedefi, 9 yalnız eğitim araştırması) için 2025/26'nın kaynak arşivi ve 2026/27'nin 13 Kasım'a kadar gözlenen sonuç kaynaklarının tekilleştirilmiş envanteri üzerinde **tek seferlik, kaynak SHA sabitli seçim** yapıldı. Bu kapanış, 2026/27'nin ileride oynanacak maçlarının tamamlandığını veya 13 aktif üretim ligine yükseltme yapıldığını iddia etmez.

## Sonuç — GitHub Actions doğrulanmış
- GitHub Actions PASS: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43620094675
- Ana 10 ligdeki önceki **4.617 sonuç satırı**: aynen korunur, `EXISTING_CORE_4617_FROZEN_RESULTS_ONLY`. Yeni bir 4.617 resmî maç doğrulaması yapılmadı; son 99 kayıttan 43'ü yalnız kısmi resmî eşleşmeyle arşivli.
- Genişleme araştırma kaydı **4.843** = eski 4.505 + 331 Segunda normal lig + 6 Segunda play-off + 1 Belçika resmî karşılaşma.
- Genişlemede **4.218 skor olgusu** kaynak / sonuç kalite denetimi açısından araştırmada kullanılmak üzere seçildi: `SCORE_FACT_RESEARCH_ONLY_QA_PASS`.
- Genişlemedeki **625 kaynak kaydı temiz skor-olgu havuzundan çıkarıldı**: 296 eski tarih/skor HOLD, 325 üst kaynak kullanım hakkı belirsiz, 3 Avusturya lig dışı Conference play-off, 1 Bastia–Red Star terk edilmiş (sahte tamamlanmış 0–0). Kaynak satırları denetim için korunmuştur, **silinmemiştir**.
- **9.460** kaynak-maç satırı = 4.617 eski + 4.218 araştırma skor-olgu uygun + 625 dışlanan; **9.460 yeni eğitim örneği değildir**.
- **Yeni model eğitimine otomatik kabul: 0**. Eski ana M4, model ağırlıkları, oynanmış maç mühürleri ve xG Excel'i değiştirilmedi.

## Kanonik teslim
1. [Satır bazlı kararlar — 9.460 kaynak işaretçisi, skor yeniden yayımlaması yok](./FINAL_9460_SOURCE_ROW_DECISIONS_NO_SCORE_REHOST_20261114.csv). Alanlar: kaynak yolu, 1 tabanlı satır numarası, lig, sezon, anonim maç anahtarı SHA256, kaynak blob SHA, karar, gerekçe.
2. [Toplu makinece okunabilir envanter](./FINAL_9460_RESEARCH_SCORE_FACTS_FILTERED_20261114.json). Kapalı kaynak kümesi, karar sınıfları ve test sayıları.
3. [Tekrarlanabilir SHA sabitli filtre](./final_9460_selection_closeout_20261114.py). Eski dış kaynakları yeniden indirmeden yerel kayıtları denetler. Script yalnız araştırma dalında çalışır.
4. [Tek-seferlik kabul testi](../../../../.github/workflows/263-final-9460-source-selection-closeout.yml). Sayılar kayarsa hata verir, uygunsuz maçları otomatik kabul etmez.

### Kayıtların kullanımı
- `SCORE_FACT_RESEARCH_ONLY_QA_PASS` sadece **maç sonucuna ilişkin araştırma/kalite karşılaştırması için** kullanılabilir; o maçın maç sonrası FT, HT veya xG'si aynı maçın **maç öncesi tahmin girdisi olamaz**. Play-off/lig geçiş maçları normal sezon sonuçlarından ayrı tutulur.
- `EXISTING_CORE_4617_FROZEN_RESULTS_ONLY` kullanıcı tarafından daha önce izin verilen mevcut bazdır; bu seçim eski 4.617'yi yeniden sertifikalandırmaz.
- `EXCLUDED_*` kayıtları seçilmiş veri görünümüne veya yeni modele alınmaz. Hukuki hak veya yeni kaynak kanıtı ortaya çıkmadıkça tekrar test başlatılmaz.
- Kaynak ve özellik kullanım hakkı, gerçek maç önü gözlem zamanı, önceki maç için sonucunun hedef maçtan önce erişilebilir olması, takım kimliği, kronolojik ayrım ve ileriye bakış hatası ayrı bir eğitim kabul sözleşmesidir. Eski geçmişe sahte `available_at` yazılmaz.

## Bilinçli olarak dışarıda kalanlar
- 2026/27 canlı API araştırma kaynağına erişilen, fakat kalıcı yeniden yayımlanabilir arşivi olmayan **633 karşılaşma**: ENG5 190, ESP2 141, ITA2 110, FRA2 108, DNK1 84. Kullanım hakkı netleşene kadar GitHub'a ham kayıt taşınmaz.
- İskoçya, İsviçre, Yunanistan ve Avusturya'da kaynaktan fazla görülen **118 olası güncel maç** yalnız toplu sayı farkıdır, bağımsız tek tek maç kimliği kanıtı değildir. 9.460'a dahil edilmez.
- **1.855 eksik maç sonrası xG** kullanıcı Excel'inde: 90 güncel + 1.765 geçmiş, ayrıca önceki sağlayıcıyla tek taraflı 56. Bu veri ayrı, kullanıcı tarafından ve kaynak izinleriyle tamamlanır.
- 2026/27 devam eden bir sezondur. Sonraki maçlar haftalık yeni veri rutininde ayrı kesim olarak işlenir; kapanmış 13 Kasım arşivine gelecekteki maç eklenmiş gibi davranılmaz.

## Döngü kilidi
Eski 1.775/461/1.268/106/8 doğrulamalarını ve eski 296 HOLD denetimlerini **aynı kaynak SHA ile yeniden çalıştırma**. Önceki kaynakları yeniden indirme, `main` dalına otomatik birleşme yapma, yeni pilot başlatma, M4'ü veya mühürleri değiştirme. Veri toplama projesi bu kesit için **KAPALI**; model mühendisliği ayrı sonraki aşamadır. Haklar/kimlikler onaylanmadan 13 analitik lig üretime alınmaz.

**Kapanış kararı:** Kullanılabilen sonuç kaynaklarını sakla ve karar manifestinden seç; uygun olmayanları görünümden çıkar; erişim veya hak engeli olanları dürüstçe dışarıda bırak; kaynak toplama için aynı döngüyü tekrarlama.

## 14 Kasım ek mühendislik denetimi — düzeltme / gerçek kapanış sınırı

Bir önceki kapanıştaki 625 dışlanan kaynak satırının **200'ünde** (ENG3 + ENG4, 2025/26) daha önce bağımsız olgusal teyidi yapılmış doğru kaynak karşılığı vardı. Salt kötü eski satırı filtreleyip düzeltmeyi kaybetmek sakıncalıdır. Bu nedenle:
- **178 yanlış FT skorunun** tarih ve takım kimliği aynı kalmak üzere, üçüncü kaynakça teyit edilen CC BY özgün yayıncı kaynağına birebir karşılıkları bulundu.
- **22 yanlış maç tarihinin** daha önce tek tek editoryal veya resmî karşılaşma sayfasıyla doğrulanmış doğru tarih ve skor kaynağına birebir karşılığı bulundu.
- [200 doğrulanmış düzeltme için kaynak satırı işaretçileri](./CORRECTED_200_ENG3_ENG4_SOURCE_POINTERS_NOT_ADDITIVE_20261114.csv) ve [makinece okunabilir kontrol raporu](./CORRECTED_200_ENG3_ENG4_RESEARCH_ONLY_NOT_TRAINING_20261114.json) eklendi. Önceki 200 hatalı kaynak satırı HOLD kalır; kaynak değeri üstüne yazılmaz. **Düzeltmeler 200 yeni maç değildir ve eski 9.460 kaynak satırına otomatik eklenmez.** Doğru kaynağa erişim ayrı karar nesnesiyle sağlanır.
- İngiltere National League'in geriye kalan 96 uyuşmazlık HOLD'u üçüncü kaynağın bağımsızlığı ve haklar tam kanıtlı olmadığı için düzeltilmiş eğitim verisine alınmaz.
- 4.617 ana bazın, 4.218 araştırma olgusu seçiminin ve yeni modele **0** kabul kararının sayıları değişmedi.
- [Düzeltme Github Actions kalite testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43621178442) başarılıdır.

**Kritik nitelik ayrımı:** Kaynak skor olgusu güvenilirliği, kaynak/yeniden kullanım hakkı, kronolojik bilgi güvenliği ve yeni modellerde performans kazanımı dört ayrı kabul kapısıdır. 4.218 araştırma olgusuna `SCORE_FACT_RESEARCH_ONLY_QA_PASS` yazılması diğer üç kapıyı geçmiş oldukları anlamına gelmez. Mevcut çalışma yalnız skor-olgusu arşivine ilişkin *koşullu kapanıştır*, 22 ligin tüm kayıtları için tam kalite sertifikası değildir.

**Bir sonraki mühendislik işi:** Yeni toplu kaynak hasadı değil; mevcut 4.617 geçmiş çekirdek sonucu, 4.218 araştırma skor-olgusu kaynak seçimini ve 200 düzeltme işaretçisini ayrı tutarak kronolojik tahmin/özellik kullanım kurallarını sağlamlaştırmak. Kaynak hakları veya gerçek geçmiş `available_at` kanıtı bulunmadan yeni eğitim satırlarını üretime sokmamak. Elle yapılacak 1.855 xG girişi bağımsız devam edebilir.

## 14 Kasım akşamı — Kullanıcı xG girişine kadar yalnız veri bütünlüğü denetimi
**GitHub Actions PASS:** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43633162817

- Aynı SHA'lara bağlanan **32 yerel kaynak dosyasından**, **9.460 satır işaretçisi** gerçekten yeniden çözüldü; orijinal skor tablosu değiştirilmedi.
- Araştırmada skor kalitesi açısından seçilmiş **4.218 kaynak satırında**, *tam eşleşen takım adı/tarih* tekrar sayısı **0**, noktalama ve aksan farkı kaldırılarak bulunan aynı-gün tekrar adayı **0**, aynı ikili için **1–2 günlük olası tarih kayması** adayı **0**. Bunlar kanonik tüm kulüp takma adlarının veya farklı maçların asla çakışmadığının evrensel ispatı değildir; normalleştirme bilerek dar tutulmuştur. Eski 10 ligin takım UUID'leri ile araştırma kulüp adları arasında yeni eşleştirme uydurulmadı.
- **200 eski hatalı skor/tarih kaydının** önceki kaynak-düzeltme bağlantıları yine geçerli: **178 FT**, **22 tarih**. Bunlar 200 yeni maç değildir; düzeltilmiş hedeflerden **13'ünün** özdeş kaynak kimliği zaten seçilmiş araştırma listesindedir, burada yeniden ekleme yapılmadı.
- [Tek-seferlik salt okunur çapraz kaynak kimlik kanıtı](./CROSS_SOURCE_9460_200_IDENTITY_POINTERS_AUDIT_20261114.json) ve [tekrarlanabilir doğrulayıcı](./audit_9460_200_cross_source_identity_without_refit_20261114.py). Kaynak sonuç sitelerine yeniden istek yapılmadı; matematik modelleri, ana M4, 10 lig üretimi, xG dosyası veya tahmin mühürleri değişmedi.
- **Kalan eksik iş, çözülmüş gibi ilan edilmedi:** Canlı API hakları belirsiz 5 lig × güncel sezon **633 erişilen fakat arşivlenemeyen sonuç**; 4 ligin güncel sezonunda kimliği birebir doğrulanmamış **118 kaynak sayımı farkı**; sonuç ve hak HOLD'ları; manuel **1.855 xG**. Bunların kapatılması için **gerçek kaynak/izin veya maç kimliği kanıtı** gerekir. Aynı 9.460 eski satır yeniden taranmayacak.
- Yeni araştırma skorundan **model eğitimine alınan satır sayısı yine 0**. Bu bilgi, kullanıcının “önce veriler, sonra matematik” talimatıyla uyumludur.

**Operasyonel karar:** Kalıcı eski kaynakların kaynak-SHA ve temel kimlik kontrolü bu turda bitti; açık kaynak hakları/maç kimliği meseleleri açık kalır. Bu belge 22×2 sezonun %100 tam olduğuna dair bir beyan değildir.
