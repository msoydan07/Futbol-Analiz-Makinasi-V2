# Futbol Maç Analiz Makinası 2.6.3 — KARAR DEFTERİ (tek geçerli karar özeti)

**Sürüm:** 2026-11-19 / v1  
**Dal:** `research/263-13-lig-22-havuz-20261113` (yalnız araştırma/dokümantasyon)  
**Amaç:** Kullanıcıyla karara bağlanan konuları unutup yeniden “açık soru” gibi sunmamak; konuşma kararı, kod uygulaması ve canlı doğrulamayı birbirinden ayırmak.  
**Bu dosya:** Kural kayıt ve yorumlama belgesidir; çalışan kodu kendiliğinden değiştirmez, otomatik ajan belleği değildir.

## 0. Karar yönetimi protokolü (uygulanacak işlem sırası)

1. Futbol 2.6.3'te yeni öneri, yeni kod işi, devir teslim veya maç günü akışı öncesinde **bu defteri ve işin özgün kodunu oku**.
2. Karar defterinde **KİLİTLİ** başlıklı bir hususu, “henüz karar vermedik / yeniden seçelim” diye sunma. Sorulursa mevcut kararı söyle; uygulama veya kanıt eksikse **yalnız onu** iş olarak aç.
3. Çelişen bir yeni kullanıcı ifadesi varsa önce bu defterdeki eski kararla farkını göster; kullanıcı açıkça önceki kararı değiştirmedikçe yeni alternatifle sessizce yer değiştirme. Kullanıcı kendi ifadesini düzeltirse **son açık düzeltme** esas alınır.
4. Değişiklik ancak şu kayıtla olur: **ID, önceki kural, yeni kural, gerekçe, onay tarihi, hangi kararı geçersiz kıldığı (supersedes), kod durumu, test kanıtı**. Önceki kayıt silinmez.
5. Her işin üç ayrı durumu zorunlu: **(A) KARAR ALINDI / (B) KODA İŞLENDİ / (C) GERÇEK AKIŞTA DOĞRULANDI**. Birini diğerinin yerine kullanma. “Bitti” yalnız gerekli test ve kabul kanıtıyla denir.
6. Güncel ve eski dokümanlar çelişirse ilk kaynak **kullanıcının en son açıkça teyit ettiği karar**, ardından bu kayıt ve ilgili kod/kanıttır; eski dokümanı tarihsel belge olarak tut, onu sessizce güncel uygulama sayma.
7. Bilinmeyen kritik bilgi / kaynak yoksa **UYDURMA**. Başarısızlık “teknik engel”, hesap var ama değer yoksa “PAS” olarak ayrı gösterilir.
8. Test sırasında araştırma dalı kullanılabilir; ana üretim M4, mevcut 2.6.3, diğer projeler ve SHA mühürlü maç önü tahminler kullanıcı kararı olmadan değiştirilmez.

## Karar kaydı D-ODDS-001 — 2 İddaa PDF, TEK mühür (KİLİTLİ)

**Teyit:** 2026-11-19, kullanıcı tarafından eski yanlış tarif düzeltilerek açıkça onaylandı.

**Kesin algoritma:**

- **Sabah (1. PDF):** Kullanıcı `iddaa.com` kaynağından maç sabahı PDF gönderir. Yalnız 10 mevcut kapsam ligi uygun maçları ele alınır. PDF'deki **MS 1/X/2, KG Var/Yok, 2.5 Alt/Üst** (7 fiyat) alınır. Orijinal PDF ve SHA saklanır; resmî fikstür/kimlik karşılaştırılır.
- **Tek sabah matematiği:** B, C2, C3 ve M4 uygun geçmiş verilerle hesaplanır; geçmiş kalibrasyon, modellerin MS/KG/Alt-Üst pazarlarındaki güvenilirliği ve önceden tanımlı model-içi karar kuralları ile **oranlardan BAĞIMSIZ olarak** ana tercih / en fazla bir alternatif / PAS üretilir. Tahmin ve tercih SHA ile **bir kez** mühürlenir. İlk PDF oranları aynı anda yalnız bağımsız piyasa referans karşılaştırmasına bağlanır; **oran, marjsız piyasa olasılığı, EV veya piyasa hareketi model tercihini, model yüzdesini ve PAS kararını yönetemez**. Matematiğe sonradan aynı maçın sonucu veya xG'si girmez.
- **İlk 11 sonrası (2. PDF):** Kullanıcı **aynı iddaa.com kaynağından** yeni PDF yollar. Bu **ikinci analiz, ikinci model hesabı, yeni piyasa-değeri kararı veya tahmin güncellemesi değildir**. Yalnız sabah ve son fiyatlar (ve marjsız piyasa olasılığı farkı) karşılaştırılır. Yeni PDF'nin maç/eşleşme/zaman kontrolü yapılır.
- **Futbol içi YORUM:** İlk 11, sürpriz yedekler, kaleci/sakatlık, rotasyon, diziliş, ceza, taktik vb. **kanıtlanabilir** değişiklikler varsa oran hareketiyle **olası ilişki** yorumlanır. Sebep kanıtlı değilse “neden belirsiz” yazılır; oran değişimini otomatik olarak şu oyuncuya mal etme. Yorum kaynağı ve saatiyle **ayrı, ekleme-only** arşivlenir.
- **DEĞİŞTİRME YASAĞI:** İkinci PDF sonrasında sabah tahmini, model yüzdeleri, ana tercih, alternatif, PAS, sabah fiyatı, mühür/SHA ve seçim gerekçesi değişmez. **Sadece maç öncesi gözlem ve yorum eki** oluşur.
- **Maç bitince:** Önceden mühürlenmiş sabah tahmini ve ayrıca kaydedilmiş futbol yorumu, resmî sonuç karşısında **ayrı ayrı** analiz edilir. Geriye dönük değiştirme/ikinci pilot yoktur.

**Temsili vaka:** Beşiktaş-Kasımpaşa MS1 ilk fiyat 1.60, ikinci fiyat 1.75. Forvetin yedek, kalecinin sakat olduğu kaynaklarla teyit edilirse piyasa algısına *olası* etkileri yorumlanır. Bu, oran hareketinin kesin nedeni değildir. Sabah MS1 tahmini ve tercihi değişmez.

**Kesin biçimde GEÇERSİZ öneri:** “İkinci PDF gelince son oranla yeni ana tercih/EV/PAS üretelim.” Bu, kullanıcı tarafından düzeltilerek reddedildi; **yeniden önerilmez**.

**Kod referansları (inceleme 19 Kasım):**
- `experiments/263/iddaa_pdf_one_step_263.py`, `iddaa_pdf_session_263.py`, `iddaa_pdf_first_quote_263.py`, `four_model_value_policy_263.py`: ilk PDF ve sabah kararı.
- `experiments/263/iddaa_pdf_last_review_263.py`: ikinci PDF oran karşılaştırması, kadro bilgisi ve futbol yorumu eki; dosya açıkça `math_refitted=False`, `forecast_shas_replaced=False`, `second_model_seal_created=False` döndürür.
- `.github/workflows/263-single-seal-second-pdf-lineup-review-once.yml`: ikinci aşamanın yalnız **çevrimdışı sentetik test** iş akışı; gerçek iki PDF maç günü saha testi olduğu varsayılmaz.

**Durum:** (A) KARAR KİLİTLİ. (B) Her iki aşamanın kod iskeleti araştırma dalında VAR. (C) İlk gerçek kapsam ligi iddaa PDF'siyle iki aşamalı *tam saha kabulü* KANITLANMADI. İlk 11 kaynağı program tarafından otomatik bağımsız kontrol edilmiş sayılmaz.

## D-SCOPE-002 — Kapsam ve arşiv (KİLİTLİ)

- **Bugün çalışan 10 maç analiz ligi:** ENG1, ENG2, GER1, ESP1, ITA1, FRA1, NED1, TUR1, POR1, BEL1.
- **Genişleme hedefi:** 13 analiz ligi, toplam 22 liglik araştırma/eğitim havuzu; 13 ve 22 sayıları şimdiki 10 liglik canlı akışın fiilen genişlediği anlamına gelmez.
- **Yalnız** 2025/26 ve 2026/27 sezonları; araştırma için kabul edilen **4.618 maçlık xG'li dondurulmuş özel snapshot** (kullanıcı onaylı). Bu kabul edilmiş özel veri GitHub'daki eski 4.413/4.617 kayıtlarının otomatik yenilendiği anlamına gelmez.
- xG'nin beş ligde elle, beş ligde otomatik sağlanması; elle girilen veride mümkün olan durumda xGEdge kaynağı tutarlılığı. **Lisanslı/özel ham xG kamu GitHub deposuna yüklenmez.**
- Günlük gerçek maç öngörüsünde yalnız hedef maçtan **önceki tarihli maç** verisi kullanılabilir.

**Durum:** (A) KİLİTLİ. (B) Araştırma ve canlı veri bağlarının kapsamı kısmen farklı. (C) 4.618 maçın canlı maç günü akışına tam bağlantısı doğrulanmadı.

## D-MODEL-003 — Matematik / model değişikliği (KİLİTLİ)

- B / C2 / C3 / mevcut M4 korunur. Ana M4, 2.6.3 ana sistem, mühürlü tahminler ve 96 geçmiş pilot kaydı **dokunulmaz**.
- xG/xGA **ayrı bir bahis tahmin makinesi hedefi değildir**. Var olan matematik modellerine fayda kanıtlanırsa geçmiş pozisyon kalitesi girdisi olarak katılacak; mevcut M4 bu alanı henüz ana kodunda kullanmaz.
- M4+xG araştırma adayı özellikle 2.5 Üst için umut verici ama **üretime terfi etmedi**. Elo katkısının M4'e otomatik eklenmesi **onaylanmadı**.
- Dört modelden ana tercih seçen karar araştırması ayrı; kalibrasyonun hedef döneme sızması, tek modelin yüksek yüzdesini doğrudan en iyi bahis ilan etme ve tutarsız market olasılıkları yasak.
- Tek maç ekranı **oranlardan bağımsız** ana tercih, en fazla bir farklı pazar ailesi alternatifi veya **model güvenirliği gerekçeli PAS** verebilir. Oran yoksa piyasa karşılaştırması `VERİ_YOK` olarak işaretlenir; bu durum sırf kendi başına matematiksel seçimi değiştirmez. İstenirse EV yalnız **ayrı betimsel karşılaştırma** olarak gösterilir, karar eşiği değildir.

**Durum:** (A) KİLİTLİ araştırma sınırları. (B) Model ve karar kodlarının bazı parçaları var. (C) Son araştırma karar adaptörünün gerçek ilk PDF ve model akışına tümüyle entegre edildiği kanıtlanmadı.

## D-OPER-004 — Uygulama ve güvenli teslim (KİLİTLİ)

- Kullanıcı “yap” dediğinde eski testleri sıfırdan tekrarlamak yerine GitHub kodları, geçmiş raporları, mevcut arşiv kontrol edilir; eksik parça hedeflenir.
- **Beyan kontrolü:** “Kodu yazdım” ≠ “GitHub'a kaydettim” ≠ “CI geçti” ≠ “gerçek maç günü doğrulandı”.
- Eksik model, bozuk/eksik PDF, bilinmeyen takım, geç/stale maç veya fiyat sorunu **tek maç için teknik engel** olarak açıklanır; başka maçlar engellenmez; teknik engel sahte PAS veya sahte tahmin olmaz.
- Dosyalar/GitHub durumları teyitsiz `tamamlandı` diye bildirilmez.
- Her yeni sohbette mevcut durum için önce bu karar defteri; ancak veri/ürün gerçekten değiştiyse son açıklanmış sürüm ve uygun test kanıtları kontrol edilir.

**Durum:** (A) KİLİTLİ süreç kararı. (B) Bu defterde yazılı; tüm diğer giriş noktalarını zorlayan otomatik enforcement **henüz yok**. (C) Proje genelinde kesintisiz otomatik uyum iddiası yok.

## Uyuşmazlık / tarihsel karar dizini

| Eski anlatım veya plan | Son geçerli karar | Statü |
|---|---|---|
| İkinci PDF sonrası tekrar model / fiyat-odaklı ana seçimi hesapla | D-ODDS-001: yalnız oran hareketi + kanıtlı futbol yorumu | **İPTAL / superseded** |
| Oran için serbest Pinnacle, Nesine, başka kaynak arayışı | D-ODDS-001: kullanıcı iddaa.com sabah + ikinci PDF; tarihsel Pinnacle bağımsız araştırmadır | **GEÇERSİZ canlı iş akışı önerisi** |
| M4 zaten xG, Elo ve ilk 11'i otomatik kullanıyor | D-MODEL-003: mevcut M4 gol-tabanlı; xG araştırma, Elo onaysız, ilk 11 yorum katmanı | **YANLIŞ olgusal varsayım** |
| 22 lig analizi şu an canlı aktif | D-SCOPE-002: şimdilik 10; 13 analiz/22 toplam genişleme hedefi | **YANLIŞ gerçekleşme iddiası** |
| Yerel test geçti = canlı maç günü hazır | D-OPER-004: gerçek PDF ve resmî as-of kabulle ayrı doğrulama gerekli | **YANLIŞ başarı iddiası** |

## Güncelleme kuralı ve örnek şablon

```text
Karar ID:
Tarih ve onay:
Önceki karar (varsa) / supersedes:
Kesin yeni kural:
Önceden değiştirilmeyecek alanlar:
Kod dosyası / commit:
Test kanıtı:
Durum A - karar:
Durum B - kod:
Durum C - gerçek akış:
Açık engel:
```

**Yeni sohbet başlatma kontrolü:** “Mevcut kararları kontrol ettim: D-ODDS-001, D-SCOPE-002, D-MODEL-003. Şu an gündemdeki konu bu kayıtlarda çözülmüş mü? Çözülmüşse yalnız yapılmamış teknik kısmı konuş.”

## D-READY-005 — Maç sabahı teknik hazırlık durumu (19 Kasım 2026)

**Karar değişmedi:** D-ODDS-001 iki PDF / tek mühür kesinlikle aynen geçerli. Oran kaynaklarını yeniden seçme veya ikinci fiyatla tahmin güncelleme işi **AÇILMAZ**.

**Yeni teknik denetim:** [Ayrıntılı kanıt ve açık engeller](263_MAC_SABAHI_HAZIRLIK_KONTROL_20261119.md). 4.618 kabul edilmiş özel maç kaydı ile 4.413 özgün skor kaydı birebir karşılaştırıldı; özgün 4.413 değişmeden ve 205 yeni skor eklenerek **yalnız özel araştırma alanında** 4.618 satırlık eski şemayla uyumlu skor projeksiyonu üretildi. Özel xG satırları kamu GitHub'a yüklenmedi.

**Durumlar:** (A) Tek mühür iki PDF kuralı KİLİTLİ; (B) 4.618 skor-şema köprüsü yerel ve 7 bütünlük testi başarılı, GitHub canlı veri bağı/uygun kaynak kabulü TAMAMLANMADI; (C) ilk gerçek PDF'den son yoruma operasyon dalı uçtan uca kabulü YOK. Mevcut 10 günlük stale kodu, 96 vs 100 sınırı, operasyon dalındaki ikinci PDF modül farkı ve eski DEV kalibrasyon bağlantısı da henüz açık.

**Bir sonraki teknik işlem:** Eski dondurulmuş matematik ve mühürleri değiştirmeden yukarıdaki P0 engellerini **research dalında** çöz/test et; ancak gerçek maç günü kanıtıyla canlı kabul yap. Eksik kod/kanıt sebebiyle oluşan **teknik engeli** modelin değer bulamaması sonucu oluşan **PAS** ile karıştırma.

## D-MARKET-006 — Piyasa BEŞİNCİ REFERANS, karar verici DEĞİL (KİLİTLİ, 2026-11-19)

**Kullanıcı teyidi:** 2026-11-19: “Oran bizim tahminimizi yönetmesini istemiyoruz. Oranda bir modül; güçlü tahmin yüzdesi yüksek bir modül, biz onu kendi modülümüzle karşılaştırma amaçlı yapmıştık.”

**Önceden zaten alınmış kararın geri kazanımı:** `docs/263_bahis_piyasasi_besinci_referans_2026_11_04.md` ve `docs/263_piyasa_referansi.md` kaynaklı piyasa beşinci referans sözleşmesi. **Bu yepyeni tartışma konusu DEĞİL**, yanlışlıkla sonraki koda/karar notuna yansıtılmamış eski anlaşmanın düzeltmesidir.

**Kesin davranış sözleşmesi:**
1. **Dört model B/C2/C3/M4** kendi geçmiş matematiğiyle hedef maç için MS1/MSX/MS2, KG Var/Yok, 2.5 Alt/Üst olasılıklarını hesaplar. Daha fazla xG girdisi ancak doğrulanmış ayrı model geliştirmeyle mümkündür.
2. **Tek seçim motoru yalnız dört modelin geçmişte ölçülen, sızıntısız, kalibre güvenilirlik verisi ve sabit matematiksel kuralı** ile ana sonuç + en fazla bir alternatif veya model-gerekçeli PAS belirler. **Piyasa olasılığına benzerlik de tek başına seçim ölçütü değildir.**
3. **İlk iddaa PDF'sindeki oranlar ve aynı maçın marjsız piyasa yüzdeleri yalnız MARKET / 5. referans karşılaştırmasına girer.** İstatistiksel uzaklık, farklılık, oran ve istenirse betimsel EV *sonradan ayrı raporlanabilir*. Bunlar **model yüzdesini, model sırasını, ana/alternatif seçimini, PAS sonucunu değiştiremez**. İlk PDF hiç yoksa ticari piyasa karşılaştırması eksik görünür; model hesabı veri/fikstür elveriyorsa yapılabilir. Ancak kullanıcının sabah işlem başlangıç yöntemi hâlâ ilk iddaa PDF'sidir.
4. **İkinci iddaa PDF'si** yalnız sabah-son oran hareketi ve gerçek futbol içi olası nedenleri kontrol eder. **Tahmin, ana tercih, alternatif, PAS ve SHA hiçbir aşamada değişmez**. Yorum ayrı append-only not olarak kalır.
5. **Maç sonrası:** Mühürlü ilk tercih, modeller ve MARKET beşinci referans **aynı maçlarda** ayrı ayrı Brier/log-loss/isabet karşılaştırmasına alınabilir. Piyasayı modelin içine sessizce katma, sadece piyasanın fikrini kopyalama veya sonuca bakarak seçimi geriye dönük değiştirme yasaktır.

**Düzeltmeyle geçersiz kalan önceki yanlış ifade:** “İlk PDF oranı / no-vig edge / beklenen değer, ana tahminin veya PAS'ın şartı olsun.” Hem bu defterdeki önceki D-ODDS-001 cümlesini hem ilerideki kararlarda EV-merkezli seçim tavsiyesini **D-MARKET-006 supersede eder**.

**Kod/uygulama farkı (gizlenemez):** `experiments/263/four_model_value_policy_263.py` halen `ev<.05`, `edge<.03`, `NO_SYNCHRONIZED_ODDS` / `NO_VALID_PDF_QUOTE` gibi **oranı seçim/PAS kapısı yapan** kurallar içeriyor. `experiments/263/iddaa_pdf_value_bridge_263.py` de bu aday çıktısını sabah PDF raporuna bağlıyor. Yalnız belgeyi değiştirmek **bu davranışı değiştirmez**. Araştırma dalında model seçimini ayrıştırıp referans oran alanlarını yalnız okuyan bir adaptör/test hazırlamak gerekir; ana M4 ve mühürlü tahminler aynen korunacak.

**Durum:** (A) KARAR KİLİTLİ ve önceki tarihsel kayıttan doğrulandı. (B) Karar defteri D-ODDS-001 uyumlu düzeltildi; **mevcut seçici kod uyumsuz, henüz düzeltilmedi**. (C) Canlı ilk PDF → model seçimi → beşinci referans → ikinci PDF yoru﻿mu bütünsel kabulü **YOK**.


## D-READY-008 — Model-only piyasa karşılaştırma uygulama aşaması (19 Kasım 2026)

**D-MARKET-006 KİLİTLİ kuralı DEĞİŞMEDİ:** iddaa oranı beşinci referanstır; ana/alternatif/PAS'ı yönetemez. Sabah tek mühür, ikinci PDF yalnız futbol içi gözlem.

**Kod karşılığı:** [Yeni model-first GitHub araştırma dosyaları, testler, retrospektif risk ve blokajlar](263_MODEL_FIRST_FIFTH_REFERENCE_RESEARCH_STATUS_20261119.md) kapsamlı biçimde kaydedildi. Yeni `model_first_decision_263.py` ve `iddaa_pdf_model_first_one_step_263.py`, eski EV-merkezli karar rotasını **silmeden** ayrı model-first yol sağlıyor. Eski `four_model_value_policy_263.py` hâlâ fiyat/EV'yi seçim eşiği olarak kullanır; eski giriş noktası güncel kararımızın yerine geçmez.

**Durum A — KİLİTLİ:** Fiyat yönetsin önerisi İPTAL. **Durum B — KISMEN KODLANDI:** Araştırma dalında bağımsız modüller/PDF köprüsü ve sentetik testler eklendi, çalışan operasyon dalına geçirilmedi. **Durum C — YOK:** GitHub CI sonucu ve gerçek ilk iddaa PDF uçtan uca maç sabahı kabulü doğrulanmadı.

**Kritik matematik uyarısı:** 496 geçmiş maçtaki 286 adayın ortalama model güveni %69,53 fakat gerçekleşmesi %62,59. Bu yüzden yeni seçici üretime terfi etmedi; geçmiş sonuçlara bakıp sessizce eşik ayarı yapılmayacak. Eski kaynak/10 günlük güncellik engelleri de açıktır.

## D-READY-007 — 4.618 özel skor SHA + takvim güncelliği araştırma kapısı (19 Kasım 2026)

**Karar değişmedi:** D-ODDS-001 (iki iddaa PDF / tek mühür) ve D-MARKET-006 (piyasa yalnız beşinci referans) aynen geçerli. **Eski M4, 96 pilot, mühürlü tahmin ve çalışan otomasyonlar değiştirilmedi.**

**Kodlandı:** `experiments/263/private_4618_matchday_preflight_263.py` — eski 4.413 satırın birebir korunması, özel 4.618 skor projeksiyonu SHA denetimi ve 10 günlük yapay tarih sınırı yerine tamamlanmış maçlar için **tam resmî takvim kapsama sözleşmesi**. Tamamlanmış aradaki bir maç kaynakta yoksa başarısız, takvim gerçekten boşsa yalnız *araştırma adayı*; doğrulanmamış resmî kaynak URL'si üretim onayı sayılmaz. xG/özel CSV GitHub'a yüklenmedi.

**Yerel test:** 15/15 sentetik durum ve gerçek dosyanın SHA/4.413+205 bütünlük kontrolü başarılı. GitHub test workflow'u eklendi; CI'nin çalışıp başarılı olduğu **ayrı henüz onaylanmadı**.

**Gerçek sınır:** Resmî sonuç takvimini baştan sona çekip eksiksizliğini bağımsız kontrol eden adaptör, 4.618 özel dosyanın canlı forecast kaynak kabulü ve mevcut `forward_quad.py` içindeki 10 gün şartının yeni güvenli kanıtla uyumlu bağlantısı **henüz yok**. İlgili envanter: [maç sabahı takvim kapısı raporu](263_4618_MATCHDAY_CALENDAR_PREFLIGHT_20261119.md).

**Durum:** (A) Yapılacak teknik iş kapsamı kilitli. (B) Güvenli araştırma *ön kapısı* kodlandı ve yerelde test edildi. (C) **Canlı maç sabahı kabulü yok**. Gelecek adım yalnız resmî sonuç adaptörü ve 4.618 özel kaynağın as-of model/ilk PDF bağlantısı; geçmişte çözülmüş oran kuralı tekrar tartışılmaz.


## D-READY-009 — 10 lig resmî maç arası ve eksik skor kaynak kontrolü (19 Kasım 2026)

**Kilitli iş akışı değişmedi:** D-ODDS-001 (ilk iddaa PDF ile TEK tahmin ve mühür, ikinci PDF yalnız futbol analisti yorumu), D-MARKET-006 (oran yalnız MARKET beşinci referansı) geçerli. Yeni fiyat tabanlı tercih veya ikinci mühür açılmadı.

**Araştırma kodu/kanıt:**
- [10 ligin resmî sonraki normal maç hafta başlangıçları](263_OFFICIAL_NOVEMBER_2026_CALENDAR_SOURCE_SUMMARY.md): boşluğun millî maç arasıyla uyumlu olduğunu gösterir; arada tek maçlık erteleme olmadığını kapsamlı sonuç listesi olmadan ispatlamaz.
- `experiments/263/official_full_season_gap_guard_263.py`: sadece tam sezon resmî fikstür kapsamı varsa takvim boşluğu adayı üretir; tek tur/kulüp haberini tam kapsama saymaz.
- `experiments/263/public_provider_2627_gap_audit_263.py`: mevcut 10 Football-Data sezon kaynağından son kabul sonrası bitmiş maçları salt-okunur **ikincil** kontrol eder; federasyon resmî sonucu yerine geçmez.
- KNVB `knvb.nl` Eredivisie izin listesine eklendi.
- **33/33 yerel sentetik test** başarılı (16 + 9 + 8); ilgili research CI dosyası güncellendi. GitHub Actions çalışmasının başarı sonucu ve resmî tam kapsam canlı kabulü **henüz yok**.

**Durum A — DEĞİŞMEDİ:** Oran ve mühür kararları sabit. **Durum B — ARAŞTIRMA KODU VAR:** Veri SHA, takvim ve provider ön denetimleri research dalında. **Durum C — CANLI ONAY YOK:** Eski modeldeki 10 gün engeli, 4.618 özel dosyanın canlı kaynak kabulü ve ilk PDF'den uçtan uca model bağlantısı hâlâ açık. Sonraki iş bu üçü; eski kararları yeniden tartışma.

## D-READY-010 — 4.618 veriden sabah PDF araştırma entegrasyonu (19 Kasım 2026)

**Değişmeyen kilitli kararlar:** D-ODDS-001 (sabah 1 PDF = B/C2/C3/M4 tahmini + tek SHA; ilk 11 sonrası 2 PDF = yalnız oran hareketi ve futbol yorumu), D-MARKET-006 (oran asla ana/alternatif/PAS tercihini yönetmez), D-MODEL-003 (M4, önceki 96 pilot ve tarihsel SHA'lar dokunulmaz).

**Gerçekten kodlandı:** Ayrı `private_4618_quad_forward_263.py`, `private_4618_empirical_baseline_263.py`, `private_4618_provider_bundle_263.py`, `private_4618_pdf_session_263.py`, `private_4618_iddaa_model_first_one_step_263.py`, `private_4618_retry_guard_263.py`. Kaynaklar 4.618 özel skor SHA ve orijinal 4.413 koruma kapısı üstünden birleştirildi. Model matematiği mevcut modüllerden türetilerek, eski çalıştırıcı değiştirilmeden kullanıldı. Bu bir **research-only alternate entrypoint**; orijinal otomatik sabah workflow'u kendiliğinden bu koda yönlendirilmiş DEĞİL.

**İkincil güncellik kontrolü:** Kullanıcı PDF'sindeki her lig için `football-data.co.uk` 2026/27 sezon sonuçları oturumda kayda alınır; hedef maçtan önce tamamlanmış ancak dondurulan 4.618 veri kaynağına girmemiş skor görünürse o lig bloke edilir. Bu **resmî lig takvimi tam kapsama tasdiki değildir**, `production_approved=False`.

**Yeni mühürsüz tekrar deneme:** Ağ kesilmesi veya kaynak sorunu sonucunda hiç tahmin mührü oluşmamışsa önceki denemeye dokunulmaz; aynı ilk PDF SHA için ayrı `-retry-N` klasörü açılabilir. Herhangi bir önceki SHA'lı tahmin varsa ikinci üretim yasaktır.

**Test/beyan:** Gerçek özel dosya SHA kontrolü ve ilgili 46 yerel güvenlik/bütünlük testi başarılı. GitHub'da ilave 13 entegrasyon sözleşmesi + 6 mühür güvenliği testi ile CI import/compile workflow'u eklendi; bunların **başarılı GitHub run'ı henüz doğrulanmadı**. Gerçek 10-lig iddaa PDF'siyle canlı uçtan uca kabul henüz YOK; yeni kalibre yüzdeler geçmiş veride olduğundan fazla güvenli olabilir.

**Durum:** A = önceden alınmış kararlar korundu; B = araştırma entegrasyonu GitHub'da yazıldı; C = canlı maç sabahı onayı yok. Ayrıntılar: [4618 araştırma entegrasyonu raporu](263_PRIVATE_4618_MODEL_FIRST_PIPELINE_20261119.md). **Sonraki iş:** gerçek kaynak/gerçek PDF/gerçek ilk 11 sonrası ek yorum ve CI teyidi; fiyat yönetimli seçime, yeni 96 pilotuna veya M4 matematiğini değiştirerek eskiye dönülmez.

## D-READY-011 — 19 Kasım doğrulama: kaynak sayımı, yüzde güvenilirliği ve CI

**Mevcut kilitli kararlar değiştirilmedi:** D-ODDS-001 ve D-MARKET-006 gereği fiyat yalnız beşinci referanstır; ikinci PDF yalnız futbol yorumu, sabah SHA ve model kararı değişmez. M4 matematiği ve eski mühürler korunmuştur.

**(1) Kaynak karşılaştırması:** 4.618 özel skor SHA'sı ve 4.413 eski skor SHA'sı yerelde doğrulandı. 2026/27'nin **10 liginde 10/10 sayılar**, ayrı `oladeeayo/open-matchday` ikincil GitHub skor kaynağıyla **8 Kasım'a kadar** aynı; on ligde toplam kaynak sayıları tek tek eşleşti. Ancak dokuz kaynak son kez 10 Kasım, Portekiz kaynağı 16 Kasım güncellenmiş; **9–19 Kasım'ın hiçbirinde ertelenmiş lig maçı oynanmadığının tam ve güncel resmî tasdiki YOK**. Bu kapı açık; uluslararası ara varsayımıyla otomatik kabul yapılmaz.

**(2) Tarih-sıralı güvenilirlik:** Aynı eski 496 maçlık araştırma örneğinde 286 ana aday, 210 PAS; genel aday %69,5 ortalama olasılık vs %62,6 gerçekleşme. 9–25 Ekim (161 aday) ile eğitilen tek sabit logit kalibrasyon düzeltmesi 26–31 Ekim (47) ve 1–8 Kasım (78) sonraki gözlemlerde **Brier'i kötüleştirdi**; bu yüzden otomatik genel yüzde düzeltmesi canlıya terfi ettirilmez. Özellikle **2.5 Alt: 30 adayı 11 isabet ve tahmin ort. %65,1** önemli kalibrasyon alarmı. Bu, geçmişte tekrar kullanılan seçimli test kohortudur; bağımsız 2026/27 son holdout sayılmaz; yeni model/PAS eşikleri sessizce değiştirilmez.

**(3) GitHub CI hatası düzeltildi:** Yeni `.github/workflows/263-private-4618-model-first-integration-ci.yml` işinin geçersiz sayıyla başlayan iş kimliği araştırma dalında düzeltilerek `private-4618-pipeline-contract` yapıldı. Gerçek GitHub Actions run [44560118778](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44560118778) **SUCCESS**: Python derleme, kontrat testleri, matematik modül importları ve eski model koruma adımları başarılı. Bu **gerçek maç öncesi PDF uçtan uca kabulü** anlamına gelmez.

**Üç durum:** A=eski iki PDF / fiyat beşinci referans kuralı KİLİTLİ. B=veri bütünlüğü, ikinci kaynak karşılaştırması ve kalibrasyon araştırma denetimi tamamlandı; CI başarıyla doğrulandı. C=**resmî tam 9–19 Kasım sonuç aralığı + gerçek iddaa PDF ve ilk 11 yorumuyla tam canlı kabul HÂLÂ YOK**. Ayrıntı: [19 Kasım sade rapor](263_KALAN_ISLER_GUNCELLIK_KALIBRASYON_CI_20261119.md).

**Devam:** Yeni test pilotu veya yüzde değişikliği değil; yalnız resmî kalan tam sonuç kanıtı ve ilk gerçek PDF geldiğinde bir kez gerçek maç günü kabulü. Eski M4/96 kayıtları değiştirilmeyecek.

## D-READY-012 — 19 Kasım resmî tablo sayımı + kullanıcının eski gerçek PDF'si düzen incelemesi

**Son durum (A/B/C):** A: D-ODDS-001 ve D-MARKET-006 kilitli, değiştirilmedi. B: 4.618 özel skor SHA'sı ve 10 liglik 2026/27 sayımı yeniden doğrulandı; **GER1 81 / NED1 108 / TUR1 99 / BEL1 99** resmî güncel puan tablolarıyla eşleşti. Diğer liglerde normal 9–19 Kasım arası resmî programın millî ara olduğu doğrulandı ancak tüm ertelenen maçların tam resmî FT satırları henüz kontrol edilmedi. **ESP1=119 ve POR1=98**, ilgili tam haftanın 120/99 teorik maç sayısından birer az olduğu için erteleme durumu seçili maç günü öncesi kaynaktan doğrulanmalı. C: gerçek yeni tarihli 10-lig iddaa PDF → SHA → maç sonrası tam canlı kabul henüz **YOK**.

**Gerçek PDF biçim kanıtı (geçmiş, 11 Kasım):** Kullanıcının daha önce yüklediği gerçek iddaa PDF'si salt okunur kontrol edildi: 3 sayfa, 30 tanınan fikstür satırı, **28 adet 14-sütunla uyumlu** ve **2 adet 13-sütun hizası eksik**; bu iki satır kesinlikle fiyat satırı olarak tahmin edilmemeli. 10 üretim ligi kapsamına düşen maç yok, eski PDF'den yeni maç tahmini/mühür üretilmedi. PDF baytları GitHub'a konmadı.

**Dosya ve kanıt:** [19 Kasım resmî kaynak / eski PDF düzen raporu](263_19KASIM_RESMI_LIG_GAP_VE_GERCEK_PDF_DUZEN_DENETIM.md). 4.618 özel skor SHA: `54250bb6107250d0623b74ad9c56f90731f02d10dab3bf386deefb27aae487ea`. **Kaynakların normal lig arası oluşunu, erteleme dahil mutlak sıfır sonuç kabulüne dönüştürme.** İddaa oranları yalnız beşinci referans; ana M4/96 pilot/otomasyon/önceki SHA mühürleri değiştirilmedi.

**Takip işi:** Aynı veri-açığı ve model kararı baştan tartışılmaz. Seçili maç günü geldiğinde tam resmî sonuç yeniliği + **yeni kullanıcı ilk iddaa PDF'siyle tek uçtan uca kabul**; kullanıcı ikinci PDF gönderdiğinde yalnız append-only futbol yorumu. Geçmiş %69,5 vs %62,6 örneğinden kaynaklanan kalibrasyon ihtiyatı hâlâ açık; kanıtsız kalibrasyon terfisi yok.
