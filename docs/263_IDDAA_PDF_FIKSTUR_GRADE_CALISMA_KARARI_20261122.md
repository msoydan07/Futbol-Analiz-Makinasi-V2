# 2.6.3 — Resmî fikstür kapısı / PDF kaynaklı hesaplama (22 Kasım 2026)

**Güncel operasyon kararı.** Önceki model matematiği ve mühürler aynen korunur.

## Hata ve kanıt

22 Kasım 2026'da 8 ayrı kullanıcı iddaa PDF'sinde 25 maç vardı. Eski zorunlu federasyon-lookup kontrolü 16 maçı matematiğe sokmadan bloke etti. Bu 16 **ana model arızası değildir**. Aynı 25 maçın PDF kaynaklı ayrı araştırma çalışması M4-MS ve C3-KG/2.5 sabit hesaplarıyla **25/25** matematiksel ana tercih verdi; 24 P0 tam, Twente-Willem II MS1 yayımlanmamış. 25/25 **resmî federasyon onayı anlamına gelmez**.

### Doğrulayıcı neden aksıyordu?

- Premier League kodu genel güncel maç veri akışı yerine bir dönemsel maç revizyonu haberini okuyordu.
- LaLiga kodu sezonun belirli bir eski haftasına sabitliydi.
- Serie A kodu belirli bir hakem duyurusu haftasına sabitliydi.
- Belçika kodu sabit, geçmiş bir KV Mechelen-Genk eşleşmesine özel yazılmıştı.
- Racing Santander, AC Milan, Standard Liege PDF yazımları eski kanonik kulüp kimliğiyle birebir aynı değildi; yeni sözlükte kesin eşleşme, federasyon tarafından önceden doğrulanmış mevcut UUID'ye bağlandı. Küme dışı/fuzzy isimler varsayılmaz.

Resmî doğrulayıcıların bu yetersizlikleri düzeltilmiş olarak **sunulmaz**. Resmî site bulunamadıysa kaynak durumu **doğrulanamadı** kalır.

## Kalıcı iki kanallı hesaplama

| Yol | Kaynak | Ana M4/C3 | P0/P2 | Resmî mühür / pilot |
|---|---|---|---|---|
| **OFFICIAL_VERIFIED** | Taze, gerçekten doğrulanmış federasyon fikstürü + SHA'lı kullanıcı ilk PDF'si | Mevcut `forward_quad` + `model_first_decision.select` | İlk SHA'lı PDF ve iki bağımsız zirve | Mevcut tüm resmi kısıtlar geçerse evet |
| **PDF_SOURCE_ONLY** | Orijinal iddaa PDF'si, takımın mevcut kanonik UUID'si, Türkiye saatli KO ve SHA-checked geçmiş | Aynı dondurulmuş M4/C3 çekirdek hesapları; bağımsız araştırma katmanı | Tam pazar varsa P0; P2 iki bağımsız lideri kontrol eder | **HAYIR**. Federasyon doğrulandı, resmî SHA tahmini, pilot girdi denemez |
| **ROW_REVIEW** | Takım kimliği, tarih, orijinal fiyat, saat ya da veri kontrolü geçemiyor | Yüzde uydurulmaz | Yalnız doğrulanabilen fiyatlar | Hayır |

Kullanıcı ilk PDF'yi bir kez gönderir. `iddaa_pdf_one_step_263.py` aynı işlemede önce resmî denemeyi çalıştırır. Resmî parser başarısız olursa `iddaa_pdf_source_fallback_263.py` kabul edilmiş 4413 ya da kaynaklı 4617 geçmiş verisiyle ve aynı sabit kalibrasyonla **ayrı PDF kaynaklı matematiksel araştırma** gerçekleştirir. Normal resmî pilot/önceki mühür kodlarına asla sahte `VERIFIED` göndermez.

Araştırma kendi içerik SHA'sına ve orijinal PDF SHA'sına sahiptir; kayıt yeni `calibrated_session.json` ve tek `toplu_analiz_onayli.pdf` içinde ilgili kartta **PDF KAYNAKLI · RESMÎ ONAY YOK** etiketiyle sunulur. Uyum denetimi farklı tercihlerde yüzde farkı uydurmaz. İlk oranı boş favori varsa aynı şekilde boş tutar.

İkinci PDF geldiğinde `iddaa_pdf_last_review_263.py`, kaynak türünü korur; ilk ana/alternatif/P0 kararlarını yeniden hesaplamaz. Kullanıcıya onaylı tekli V3 görünümü verilir ve PDF kaynaklı maçta resmî onay yok etiketi görünür.

## Güvenlik ve sınırlar

- **Kesin kaynak çelişkisi istisnası:** Resmî kaynakta maçın farklı tarihi/saati veya takım sırası açıkça doğrulanmışsa PDF'ye geri düşülmez; maç manuel incelemeye ayrılır. Resmî fixture geçip model geçmiş veri kontrolü reddettiyse model matematiği de daha düşük güvenli bir kaynakla zorlanmaz. PDF-only ayrı hesap sadece resmî lookup adapterı kaynağa erişemediğinde veya eşleşme bulamadığında kullanılabilir.
- Geçmiş maç sonucu, mevcut maçın başlangıcı veya sonrası hiçbir tahmin hesabına giremez.
- Orijinal PDF'nin SHA kaydı, 7 oranın doğru kolonlarda okunması, kaynak saati, mevcut takım ID'si, accepted 4413/4617 tarihi, son maç boşluğu ve model kilidi kontrol edilir.
- Yeni 4617 verisi için orijinal sabit 4413 kaynağının ve tarihsel kabul kanıtının doğrulaması sürer. Onaysız CSV'ye gevşetme yapılmaz.
- Eski resmî tahmin SHA'ları ve 96/100 pilotları değişmez.
- Fikstür parser hatası **model arızası**, resmî maç yokluğu veya piyasanın MS1 fiyatı yokluğu diye raporlanmaz.
- Resmî maç doğrulama adaptörlerinin güncel ve genel veri kaynaklarına güncellenmesi ayrıca incelenecek; eski sabit haftaları resmî doğrulama olarak yeniden sunmak yasaktır.
- Bu iki farklı kaynak kalitesi başarı/isabet raporlarında birleştirilmez.

## Kabul

`.github/workflows/263-iddaa-pdf-source-fallback-acceptance.yml` ile orijinal ilk/ikinci V3 rapor üreticileri, 2.6.3 donmuş M4/C3 yüzdeleri, iddaa fiyat sütunları, Twente yayımlanmayan favori fiyatı, kaynak SHA bütünlüğü ve geçmiş resmî rapor testleri sınanır.

**Durum:** Araştırma dalında kabul edildikten sonra ilgili kod ve belge mevcut 2.6.3 aktif araştırma dalına aktarılır. `main` veya eski mühürlere otomatik yazılmaz.
