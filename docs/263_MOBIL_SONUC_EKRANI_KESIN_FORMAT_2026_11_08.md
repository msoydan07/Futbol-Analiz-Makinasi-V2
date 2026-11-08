# Makina 2.6.3 — KESİN MOBİL SONUÇ EKRANI (8 Kasım 2026)

## Onaylı görsel referans
Kullanıcının 7 Kasım 2026 tarihli **2026-11-07_ESERIMIZ_44_MAC_MOBIL.pdf** ekran görüntüsü.
8 Kasım 2026'da kullanıcı bu düzenin **tüm günlük maç sonuçları için korunmasını** tekrar açıkça istedi.

**Kural:** Excel veya yalnız geniş düz Markdown tablo, onaylı telefon sonucunun yerine geçemez. Kullanıcıya öncelikle bu görselin biçimine sahip **A4 portre, telefon uyumlu, satır-satır mobil PDF** verilir. Kaç maç varsa sayfalar boyunca aynı düzen devam eder.

## Her maç için değişmeyen görsel sıra

Üst başlık: `N MAÇ | BİZİM % + PİYASA % + KG + ÜST`.
Açıklama: Türkiye saati, maç günü, MS piyasa olasılığı için marj çıkarma yöntemi, KG/Üst verilerinin ham model medyanı olduğu.

| TSİ | Maç | Bizim % | Piyasa % | Fark (yp) |
|---|---|---|---|---|
| 18:00 | Ev sahibi – Deplasman | MS1 **%55,0** | **%49,0** | **+6,0** |

Maçın hemen altında **aynı genişlikte dört açık mavi kutu**:
`KG Var %...` • `1,5 Üst %...` • `2,5 Üst %...` • `3,5 Üst %...`.

- Önceki onaylı görünümdeki lacivert üst şerit, açık mavi başlık, dönüşümlü açık mavi/beyaz maç satırları, yeşil/kırmızı fark değerleri ve telefonla okunabilir yazı ölçüleri esas alınır.
- Kullanıcı oran da görmek istiyor: maç adı altında küçük puntoda `1/X/2: ev / beraberlik / deplasman` yazılır; bulunamayanlar `—` kalır.
- `Bizim %` sadece **hangi MS pazarının** yüzdesi olduğunu belirtir. MS1/MSX/MS2 ayrı tekli kalibrasyon değerleri normalize dağılım gibi toplanmaz.
- `Piyasa %` yalnız gösterilen **aynı MS** tarafının 1/X/2 oranlarından marjı çıkarılmış payıdır; `Fark` = bizim kalibre MS − bu piyasa yüzdesi. KG veya Üst tarafındaki fiyatı MS farkıyla karşılaştırma.
- KG Var/Üst kutuları varsa modellerin **ham medyanlarıdır**, kalibre edilmiş ana bahis kararı değildir.
- Eş zamanlı doğrulanmış oran yoksa üçüncü taraf referansı **etiketli** gösterilir; kaynak yoksa fiyat/piyasa/fark hesaplanmış gibi gösterilmez. Eski fiyat canlı Pinnacle veya onaylı değer seçimi sayılmaz.
- Ertelenmiş maç açıkça `ERTELENDİ` belirtilir; maç öncesi tahmin saklanmaz veya sonradan üretilmez.

## Ayrıca istenen 10 güçlü seçim ekranı
Kullanıcı 10 maç istediğinde **42 maçlık onaylı ana PDF yanında** benzer tasarımda ayrı kompakt **10 maçlık mobil PDF** hazırlanır.
Her maçın kendi içinde MS1/MSX/MS2, KG Var/Yok, 2,5 Alt/Üst karşılaştırılır; en uygun tek ana pazar seçilir, sonra farklı maçların adayları sıralanır. **Çifte şans otomatik birincil seçim değildir; 1,5 Üst yüksek yüzdesiyle tüm listeyi tekelleştirmez.**
Bu ikinci ekranda sütunlar: TSİ, Maç/Ana tercih, Bizim %, **seçilen pazarın oranı**, Gerekli % (1/oran). Alt dört kutu ve sınırlamalar korunur. Tek fiyat üzerinden piyasa marjı yokmuş gibi `marjsız piyasa` denmez.

## Veri / karar bütünlüğü
- Sadece gerçekten üretilmiş ve tarihi kanıtlı modeller kullanılır; analize girmemiş maçın yüzdesini doldurma.
- B,C2,C3,M4 bulunabilirliği maç bazında görünür.
- Pilot, geçmiş tahmin, model kaynak ve karar katmanı bu görsel düzenle **değiştirilmez**.
- Oran/EV doğrulanmayan kayıt **RESEARCH_PAS**; güzel ekran güvenilir bahis önerisi veya kanıtlanmış başarı anlamına gelmez.
- Raporun kaynağı, model/quote saati, geçici araştırma mı yoksa SHA mühürlü pilot mu olduğu net belirtilir.

## 8 Kasım 2026 üretim kontrolü
- `ANA_263_08_KASIM_ESERIMIZ_42_MAC_MOBIL.pdf`: 42 maç, 4 sayfa, referans görünüm.
- `ANA_263_08_KASIM_EN_YUKSEK_10_MOBIL.pdf`: 10 ana seçim, 1 sayfa, eş görünüm.
- PDF'ler sohbet çalışma alanında oluşturuldu; bu GitHub belgesi **biçim kontratıdır**, otomatik rapor üreticisinin bütün günlük akışlara bağlandığı iddiası değildir.


## 8 Kasım 2026 — KULLANICI TARAFINDAN ONAYLANAN V2 TASARIMI (KALICI)

**Durum: KESİN ONAYLANDI.** Kullanıcı yeni V2 PDF görünümünü açıkça beğenip, "her maç analizinden sonra bu konuşma olmasın; lütfen kaydet" diye özellikle talep etti.

Bu bölüm, yukarıdaki önceki görsel tanımlardan **tipografi, renk ve kart görünümü konusunda önceliklidir**. Maç verisi, gerçek model yüzdeleri ve karar/mühür güvenliği konularındaki eski kurallar geçerlidir.

### Zorunlu görünüm

- Öncelikli çıktı: **telefon uyumlu A4 portre PDF**. Kullanıcı her analiz istediğinde ayrıca PDF biçimi sorulmaz.
- Her maç **ayrı, yuvarlatılmış köşeli, ince açık-mavi çerçeveli kart** içine alınır; kartlar arasında net boşluk olur. Bir maçın KG/Üst verisi başka maçla görsel olarak birleşmez.
- **Okunabilir iki ana yazı tonu:** ana metin/kulüp/saatler koyu füme `#1F2933`, sayısal vurgu ve başlıklar canlı lacivert `#0F4C81`. Alt bilgide yumuşak gri `#52606D`.
- Fark pozitifse belirgin yeşil `#14804A`; negatifse belirgin kırmızı `#C33D3D`. Kartlar sırayla beyaz `#FFFFFF` ve çok açık mavi `#F7FBFE`; dört alt pazar kutusu `#EAF4FB`, çerçeveler `#B9D8EC`, başlık satırı `#D9EDF9`.
- Yazı tipi: okunabilir **DejaVu Sans / DejaVu Sans Bold** ya da Türkçe karakterleri eksiksiz destekleyen benzer sade bir sans-serif; gereksiz sıkışık veya yoğun ince fontlar kullanılmaz.
- Sıralama korunur: başlık ve açıklamalar; **TSİ / Maç / Bizim % / Piyasa % / Fark (yp)**; maç adı altında kaynağı doğrulanmış **1/X/2 oranları + model sayısı**; aynı maç kartında yan yana **KG Var / 1,5 Üst / 2,5 Üst / 3,5 Üst**.
- Ayrı 10 maç görünümünde **TSİ / Maç + Ana tercih / Bizim % / Seçilen pazar oranı / Gerekli %**; altta aynı dört pazar kutusu. **10 maç PDF'si 2 sayfada** daha büyük ve ferah kartlarla sunulur; tek sayfaya sıkıştırılmaz.
- Günlük maç sayısına göre 42 maç örneğinde ana PDF 6 sayfa; satırları taşırıp kesmeden kaç sayfa gerekiyorsa o kadar kullan.
- Kullanıcının özellikle istemediği **çifte şansın otomatik en yüksek seçilmesi** ve 1,5 Üst'ün bütün listeyi tekelleştirmesi yapılmaz; yüksek yüzdeye dayalı seçim analizi model onayı veya bahis garantisi değildir.
- **Model ve fiyat verileri her zaman kaynaklarından okunur**: araştırma PDF'si resmî SHA mühürlü pilot kaydı gibi sunulmaz. V2 renk/çerçeve değişikliği hiçbir model sonucunu, onay eşiğini veya kayıt SHA'sını değiştirmez.
- Oran yoksa `—`, fiyatın kaynağı belirsizse `doğrulanmadı` yaz. Üçüncü taraf oranı kesin Pinnacle fiyatı gibi gösterme.
- **Her maç analizinde bu V2 görünümü varsayılandır**; kullanıcıya tekrar "hangi tasarım" sorulmaz veya onay istenmez. Farklı tasarım yalnız kullanıcı özellikle isterse uygulanır.

### Kabul edilen görsel dosyalar (8 Kasım 2026)
- `ANA_263_08_KASIM_ESERIMIZ_42_MAC_MOBIL_V2.pdf`: ayrı kartlar, 6 sayfa.
- `ANA_263_08_KASIM_EN_YUKSEK_10_MOBIL_V2.pdf`: aynı tema, 2 sayfa.

**Not:** Bu depo belgesi kesin kullanıcı tercihini kalıcı olarak belgeler. Her yeni raporu otomatik üretmeye yarayan genel bir renderer'ın tüm akışlara bağlanmış olduğunu ayrıca kanıtlamaz; üretim sırasında bu şartname uygulanmalıdır.
