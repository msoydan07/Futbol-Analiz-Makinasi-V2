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

