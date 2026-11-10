# 2.6.3 — 99 yeni aday / Salı verisi birleştirme ve ENG2 dokuz eski kayıt kök neden analizi

**Mühendislik durumu (10 Kasım 2026):** `RESEARCH_SHADOW_READY / ORIGINAL_4518_PROTECTED / NEW_99_NOT_ACCEPTED_AS_TRAINING`.

## I. Veri eşleştirme tamamlandı, 9 eski satır mutasyonu ortaya çıkarıldı

- Değiştirilmeyen ana kaynak: **4.518** maç, SHA256 `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`.
- Salı `experiment/263-toplu-karsilastirma/data/staged_263/extended_history.csv`: **4.617** maç, SHA256 `7f005d88465fa742354854a0459f06fbb17efe9fbb648e26a18844d0f7753958`.
- Başka türlü doğrulanmış bütün 99 araştırma maçının anahtarları (**lig, maç günü, iç/dış sahadaki kanonik kimlik**) Salı dosyasındaki **99 yeni satırla birebir aynı**; **99/99 skor da aynı**. Yeni maç eksik 0, açıklanamayan yeni maç 0, skor çelişkisi 0. Bu **sağlayıcı/araştırma gözlemi uyuşmasıdır**, resmî federasyon benzersiz fixture-ID attestasyonu **değildir**.
- Salı dosyasında ana 4.518 maçın hiçbiri düşmemiş, fakat **9 eski ENG2 maçının 17 alanı değişmiş**: `source_row`, `source_url`, HT gol/sonuç, şut, isabetli şut, korner, faul, sarı/kırmızı kart. Eski tam maç sonuçları ve lig/tarih/takım kimlikleri **değişmemiş**.
- Kök neden: 9 maç eskiden Soccerway tabanlı manuel çapraz araştırmayla, **gol/skor bazında** eklenmişti. Eski kayıtlar HT, şut ve benzeri alanları boş bırakıyordu. Salı veri hattı kaydı Football-Data kaynaklı yeniden oluşturmuş; bu alanlara değerler getirirken kaynak adres/satır kimliğini değiştirmiş. Kaynağın şu anda doğru olması muhtemel olmakla beraber **önceden kabul edilmiş kaynak/istatistikleri sessizce değiştirmek yasaktır**. [Eski dokuz ENG2 kaynak kapsamı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/data/staged_263/2026_11_03_eng2_9_sources.json).
- Salı `refresh_audit.json` açıkça `provider_fetch_independently_verified:false`, `status:STAGED_UNVERIFIED_SOURCE_FILES` diyor. Sayıların eşleşmesi bunun yerine geçmez.

## II. Gerçek uygulama: “güvenli ekleme” araştırma hattı

Çalışan ve GitHub Actions tarafından test edilen kod **4518 özgün kaydı hücre/hücre koruyor**, Salı dosyasının bu dokuz maç için ürettiği değişiklikleri **reddediyor**, yalnız 99 benzersiz yeni maçı ekliyor. Böylece 4.617 satırlık, **üretimde kullanılmayan geçici gölge CSV** oluşuyor.

- Üretim kabulünden önce dosya yalnız job geçici dizininde üretilip siliniyor. Telif/sağlayıcı satırlarını yeniden yüklemeden tekrar oluşturabilmek için **gölge CSV'nin SHA256 parmak izi** rapora kaydedildi: `6e7d6c4b74babe985132f4d73df142b70ef6a90e4cf34517df9546507248ecde`.
- Orijinal 4.518 satırın DictReader ile okunan bütün alanları gölgede **aynı**.
- 99 yeni satır orijinal 4518 ve üç kaynak kanıt grubuyla anahtar/sonuç eşleşmesi yapmadan üretilemiyor.
- 9 eski ENG2 satırı kaynak istatistiklerini değiştirmeden bırakılıyor. Yeni HT/şut/korner verileri ancak ayrıca ve açık provenance düzeltme onayıyla **ayrı enrichment kaydı** hâline gelebilir; orijinal kaydı silerek/yazarak değil.
- GitHub Actions kodu **eski kaynağı yeniden indirmiyor**. GitHub içindeki Salı staging dosyasını geçici olarak okuyor. Olasılıkları üretimde değiştirmiyor.

**Bu aşamada `accepted_history=4518`, `production_or_M4_updated=false`, `99_new_matches_fully_officially_verified=false`.**

## III. Testler / kalıcı kaynaklar

- [4.518 – 4.617 – 99 üçlü karşılaştırma](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-staged99-evidence-join-20261110/research/opponent_goals/reports/staged4518_4617_published99_comparison_20261110.json) — 99/99 eşleşir, eski 9 satır yüzünden `HOLD`.
- [Dokuz ENG2 satırın hangi alanları değişmiş](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-staged99-evidence-join-20261110/research/opponent_goals/reports/accepted_old9_stage_field_changes_20261110.json).
- [4518+99 append-only güvenli gölge veri manifestosu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-staged99-evidence-join-20261110/research/opponent_goals/reports/append_only_4518_plus99_provisional_manifest_20261110.json).
- [99 kayıt ve eski 9 neden-sonuç QA](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42793860163), [dokuz alan testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42794135649), [güvenli append-only gölge testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42794593044). Üçü de GitHub Actions `success`; birincinin içerik sonucu bilinçli `HOLD`, bu çelişki değildir.
- Git kaynak karşılaştırmasında `m4_integrated.py`, `m4_lock.json`, `data/quad_accepted_263/extended_history.csv`, B/C2/C3/M4 karar kodu ve **40 orijinal SHA mühür / 40 karar dosyası** değişmedi. Salı `data/staged_263` dosyası veri kabulü değildir; ayrı dal.

## IV. Artık tekrar edilmeyecek iş ve kalan gerçek kabul kapısı

**Tekrarlama yok:** 99 maçı tekrar arama, eski 4.518'i yeniden kurma, 984 gol maçının retrospektif Brier denemesini tekrar koşma, altı yeni model düşünme, source supplier haftalık kotasını aşma.

**Üretime kabule kalan tek teknik işler:**
1. 99 aday için yerel resmî lig/federasyon maç kimliği ve teyit edilebilir skor ile hak/yeniden kullanım koşullarını eşleştirmek. İlk 28'de önceki iki kaynak uyuşması var ancak tekil ID yok. Diğer 71'de aynı kaynak satırının yeniden bağımsız gözlemi eksik. Bunlar kabul yapılmadan `4518 -> 4617` ana veri yükseltmesi **yok**.
2. 9 ENG2 maçın yeni istatistiklerinin ayrı `source-enrichment` gözlem sınıfıyla kaynağını doğrulamak; orijinal satırları sessizce yeniden yazmamak.
3. Yeni, bağımsız mühürlü maçlar biriktikçe **KG Var, Üst 1.5 / 2.5 / 3.5 ve MS** yüzdelerinin farklı lig, güç bandı ve hafta zaman kesimlerinde ne kadar kalibre olduğunu ölçmek. Retrospektif geçmişe baktıktan sonra onun üzerinden doğrudan yüzde ayarlama **yok**.

**Karar:** Bugünkü turla veri birleştirme tarafındaki somut eski-kayıt bozulma hatası tespit edildi, güvenli append-only ayrık çözüm oluşturuldu ve test edildi. Resmî skor ve veri lisansı kanıtı olmadığı için ana 2.6.3 matematiği/yüzdeleri, orijinal 4.518 maç ve tarihsel pilot/otomasyonlar **değiştirilmedi**.
