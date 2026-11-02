# Futbol Maç Analiz Makinası 2.6.3 — Avrupa tek maç kapsamı, lig gücü ve Elo: bağlayıcı mühendislik kararı

**Karar:** 3 Kasım 2026. **Karar türü:** Avrupa analiz hattının kapsamı ve matematiksel doğruluk sınırları. **Bu bir model başarı testi veya canlı tahmin kabulü değildir.**

## 1. Kapsam — en önce ve sıfır ağ araştırması

Yalnız UEFA Şampiyonlar Ligi ve UEFA Avrupa Ligi maçları için:
1. Takımların ikisinin de istenen sezon itibarıyla mevcut on yerel ligden birine üyeliği kesin yerel kimlik diziniyle doğrulanmalı: `ENG1 ENG2 GER1 ESP1 ITA1 FRA1 NED1 TUR1 POR1 BEL1`.
2. Biri bile tanınmış fakat kapsam dışıysa **`ANALYSIS_SKIPPED_OUTSIDE_TEN_LEAGUES`**: **"Bu takım 10 liglik veri kapsamımızda değil; bu maç için analiz yapılamaz."**
3. İsim veya sezon üyeliği doğrulanamıyorsa **`ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED`**: **"Takımın kimliği veya 10 lig kapsamındaki üyeliği doğrulanamadı; analiz yapılamaz."** Bu, takımın kesinlikle kapsam dışı olduğu iddiası değildir.
4. STOP halinde UEFA, Elo, istatistik, oran, kadro veya model servisi **HİÇ ÇAĞRILMAZ**. Mevcut `uefa_ten_league_scope_gate_263.py` ile `preflight_then` bunu zaten uygular. Aynı kapı yeniden yazılmayacak.
5. İki takım kapsamdaysa yalnız **analiz için aday** olur; gerçek UEFA maçının varlığı/saati ve maç öncesi veriler bundan bağımsız doğrulanır. Kullanıcının verdiği maç tarihi araştırmayı başlatabilir; resmi teyit olmadan pilot/tahmin kilidi yapılamaz.

## 2. İki takım kapsam içindeyse kullanılabilecek bilgi

**A. Yerel lig gücü / gol verisi (birincil, gerçek sonuçlar):**
- Her iki takım için kendi liginde hedef tarihten önceki sonuçlar, gol atma/yeme, iç/deplasman dağılımı, rakip gücü ve mevcut ligdeki örneklem güvenilirliği.
- Farklı liglerin ham gol ortalamaları **doğrudan eşit güç ölçeği gibi kullanılmaz**. Önce kendi lig ortalamalarına göre göreli hücum-savunma performansı açıklanır. Sadece göreli oranlar bile ülkeler arası güç boşluğunu tek başına kapatmaz.
- Ligler arası mutlak güç farkı için ayrıca tarihsel önceden bilinen ve kalibrasyonu test edilmiş güç köprüsü gerekir. 2025/26 UEFA kapsamında yalnız dokuz lig bağlı ve M1 gücü henüz onaylanmadı. `ENG2` için otomatik `ENG1` puanı atama.

**B. Elo (yardımcı, kapsamlar arası ortak ölçek şart):**
- İki kulüp için aynı güvenilir yöntemde hesaplanan, **maç başlangıcından önceye ait**, tarih ve kaynak bilgisi doğrulanmış **ortak uluslararası Elo** karşılaştırılabilir. Aynı gün sonrasındaki güncelleme, güncel puanı geçmiş tarihe uygulama veya sonradan yenilenmiş rating KESİNLİKLE YASAK.
- Mevcut `audit_elo_auxiliary.py` yerel lig bazında her takım/lig için 1500 başlangıç ve kendi lig maçları üzerinden puan kuruyor. **Bu değerler farklı ülkeler arasında doğrudan karşılaştırılabilir değildir**; Avrupa maçına otomatik Elo avantajı olarak katılmaz.
- ClubElo tarihsel skorları uygun kaynak adayıdır, fakat eski CSV API'sinin 2026 Eylül'den beri çalışmadığı raporlanmıştır (https://github.com/probberechts/soccerdata/issues/977). Kaynağa erişilebilirlik, aynı ölçek ve arşiv tarihi kanıtlanmadan Elo puanı uydurulmaz.
- Kendi Avrupa Elo'muzu yeniden geliştirmek veya yeni 576 maçlık Elo projesi başlatmak **şimdilik kapsam dışı**.

**C. UEFA lig/ülke katsayısı:**
- Resmi UEFA association coefficients tarihi Avrupa performansını anlatır; **ligler arası güç göstergesi** olarak referans verilebilir (https://www.uefa.com/nationalassociations/uefarankings/).
- UEFA katsayısı *matematiksel maç kazanma olasılığı* veya futbol ligi kalitesinin eksiksiz ölçümü değildir. Global Elo aynı Avrupa sonuçlarını kapsıyorsa aynı ilişkiyi ikinci kez bağımsız kuvvet katsayısı diye saymak yasaktır.
- Championship gibi birinci lig olmayan ligi ülke katsayısından doğrudan Premier League'e eşitlemek yasaktır.

**D. Avrupa xG / H2H / fiyat:**
- İki taraf için xG, xGA, xG vekili ve xG kaynağı araştırması YOK. Kendi gol geçmişimizden türetilmiş Poisson lambda, ancak doğrulanmış ülkeler arası güç düzeltmesi ve kalibre edilmiş bağlantı olursa hesaplanabilir.
- Ayrı H2H modülü YOK. Oran bağımsız doğrulanmadan EV veya A/B/C bahis onayı YOK.

## 3. Kullanıcıya gösterilecek tek analiz durumları

| Kapı | Kullanıcıya sonuç | Tahmin yüzdesi |
|---|---|---|
| Tanınan kapsam dışı takım | `ANALYSIS_SKIPPED_OUTSIDE_TEN_LEAGUES` | HAYIR |
| Tanınmayan/üyeliği belirsiz takım | `ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED` | HAYIR |
| İki takım kapsamda, kaynaklar eksik | Yerel gol profili/eksikler verilir; `ULUSLARARASI_ELO_VEYA_LIG_GUCU_DOGRULANAMADI` | HAYIR |
| İki takım kapsamda, gücü ve Elo'su doğrulandı ama ortak tahmin kalibrasyonu yok | Kaynaklı lig/ortak Elo karşılaştırması; model `ONAYSIZ` | HAYIR |
| İki takım kapsamda, **ayrıca** geçmişte dış dönem doğrulaması yapılmış ortak model var | Tek maç analizi, kalibrasyonu ve güven aralığıyla olasılık hesaplama adayı | Ancak ayrı onaydan sonra |

**Kural:** A/B/C ve pilot kaydı kullanıcı tarafından ertelendi. Hiçbir **offline senaryo** gerçek maç öncesi tahmin kaydı sayılmaz.

## 4. Tek sonraki mühendislik işi — eski testleri tekrar etme

Mevcut kapsam kapısı + mevcut yerel gol / C2 motorunun yalnız güvenilir açıklayıcı alanları + kaynak/tarih damgalı **ortak ölçekli Elo** + referans UEFA lig gücü göstergesi, **tek Avrupa tek maç rapor bağlantısı** altında birleştirilecek. Bu iş yalnızca eksik entegrasyon ve kanıt yoksa kaynak `DOĞRULANAMADI` durumunu ele alır. Rastgele Elo ağırlığı, yeni takım puan katsayısı, 132/432/576 yeniden model deneyi veya 10 lig dışındaki takımın yerel verisini toplama **açılmaz**.

Matematiksel kazanma/yeni gol olasılıkları için **ayrı geçmiş dönem performans kanıtı** gereklidir. Bu belgenin kabulü böyle bir performans kanıtı değildir.

## 5. Korunanlar

`main`, B/C2/C3/M4, 10 lig veri hattı, 17 bölümlük 2.6.3 yerel rapor, maç günü T−60 ilk 11in blokaj olmaması, maç araştırmasında yedi günlük pencere, A/B/C, 100 maç pilot ve immutable kayıtlar **değişmedi**.

Mevcut tarihsel UEFA M0/M1 ve M2 denemeleri arşiv olarak kalır; **ürüne entegrasyon yetkisi yoktur**. GitHub değişikliği yalnız `experiment/263-toplu-karsilastirma` dalındaki bu karar dokümanıdır.
