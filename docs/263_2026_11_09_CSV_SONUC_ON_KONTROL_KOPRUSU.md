# 2.6.3 — Ücretsiz skor kaynağı ön kontrol köprüsü

**Karar:** Mevcut M4 ana analiz motoru kilitli kalır. B/C2/C3, old96, LITE ve daha önceki SHA kayıtları değişmez.

## Gerçekte ne kuruldu?
- `sabah_postmatch_csv_bridge_263.py` kaydedilmiş new100 SHA tahminlerini ve ilk kayıt oluşturulurken commit edilmiş isimli batch bağlantılarını okur. Maç öncesi SHA, kaynak kapısı ve kickoff zamanları doğrulanır.
- `football-data.co.uk` lig/sezon CSV'si yalnız ücretsiz sonuç **ön kontrolü** için okunur. Başka kaynaktan kalıcı, resmî, insan onaylı skor uydurulmaz.
- Aynı tarih/lig/kanıtlı takım isimleri birebir eşleşirse skor karşılaştırılır; 8 Kasım daha önce kaydedilen web araştırmasıyla aynıysa `CSV_AND_WEB_REVIEW_AGREE_NOT_OFFICIAL`, değilse çelişik/eksik kayıt **bekleyen** olur.
- MS yön, Brier, log-loss, KG ve 1.5/2.5/3.5 Üst tanımlayıcı değerlendirmeleri güncellenebilir. Olasılıklar yeniden üretilmez.
- Testler sunucuda 40 gerçek SHA üzerinden, **tamamen sentetik CSV girdisiyle** çalışır. Bunu geçen test gerçek CSV skorlarının doğrulandığını söylemez.

## Kanıt düzeyi ve kırmızı çizgiler
Bu bağlantının **resmî federasyon sonuç doğrulayıcısı olmadığını** açıkça gösteriyoruz. Existing `263-sabah-new100-postmatch-readonly.yml` içindeki resmî insan teyitli sonuç hattı ayrı kalır ve kendiliğinden oluşturulmaz. Kaynak erişimi yoksa, lig verisi değişmişse veya kimlik eşleşmezse **puan verilmez**. Oran API çağrısı, bahis ROI iddiası, geçmiş maç için pilot mühür, model eğitimi ya da ana dala geçiş yok.

## 9 Kasım gerçek kaynak denetimi — ölçülen sonuç
- [İkinci GitHub çalışması #42609268097](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42609268097): **5/5 sentetik güvenlik testi PASS**; **9/9 gerekli ligin** CSV'si HTTPS kaynaklarından indirildi ve kaynak sınıfı korundu.
- Kayıtlı gerçek 8 Kasım mühürleri: **40**.
- Dış CSV + önceki web araştırma skorlarıyla aynı maç, aynı skor ve aynı tarih şartlarını sağlayan: **38**. Bu **38 provisional/araştırma eşleşmesidir**; resmî insan onaylı veya bağımsız federasyon doğrulaması değildir.
- Bekleyen 1: **Estoril–Marítimo** — mevcut araştırma kaydında resmen ertelenmiş, güncel sezon CSV'sinde nihai skor yok.
- Bekleyen 2: **Çorum FK–Fenerbahçe** — 8 Kasım resmî TFF skor kaydı web incelemesinde **0-5**, ancak dış CSV ile güvenli tarih/takım kimliği eşleşmesi elde edilemedi. **Tahmin skoruna zorla eklenmedi; 39. kayıt** daha önceki bağımsız `nov8_webreview` araştırma raporunda görülebilir. Kaynak: https://www.tff.org/Default.aspx?macId=317879&pageId=29
- Böylece **otomatik resmî puanlanan sonuç hâlâ sıfır**, ama dış kaynak skorlarıyla eşleştirme ve makine başarı ölçümü **38 maçta gerçek veriyle yapılabilir duruma** geldi.
- Güncelleme 1: Kaynak adresinin `www.football-data.co.uk` → `football-data.co.uk` gibi kanonik HTTPS yönlendirmesine, **sadece aynı tam CSV yolu içinde** izin verildi. Başka dosyaya veya alan adına yönlendirme reddedilir.

## GitHub işletimi — 9 Kasım son kabul

- **Günlük kontrol zaten kurulmuş:** ChatGPT otomasyonu `2.6.3 Maç Sonu Kontrolü` etkin; Türkiye saatiyle **her gün 10:00**, ilk planlanan gün **10 Kasım 2026**. GitHub'da yalnız deney dalına, `experiments/263/postmatch_refresh_requests/YYYY-MM-DD.json` biçiminde, günde bir kere salt-okunur sonuç kontrol isteği bırakması tanımlanmış. 9 Kasım isteği depoda zaten mevcut, **yeniden yaratılmaz**.
- Otomasyonun hedeflediği **gerçek iş akışı**: `.github/workflows/263-postmatch-csv-bridge-readonly.yml`, kaynak kodu: `experiments/263/postmatch_csv_bridge_263.py`. 9 Kasım gerçek koşusu **#42607872712** [GitHub Actions](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42607872712), **6/6 güvenlik testi geçti** ve gerçek ücretsiz lig CSV'leri ile **40 kayıt / 38 geçici skor eşleşmesi / 2 bekleyen** üretti. Ayrı skor köprüsü `263-postmatch-csv-provisional-readonly.yml` de geçmiş bir araştırma denemesi olarak bulundu; bunlar **aynı 38 maçın iki ayrı sonucu gibi toplanmaz**.
- **9 aktif ligin 9/9 CSV'si çekildi** (kayıtlı `new100` karşılaşmaları olan ligler; 10. lig için mühürlü maç yoksa boş sayılır). CSV + önceden kaydedilmiş web araştırma skoru ile **38 kayıt tutarlı**. Başarı tablosu tanımlayıcıdır; otomatik **resmî lig/federasyon teyidi = 0**, üretilmiş insan attestation dosyası = **0**.
- **İki istisna açıkça korundu:** `Estoril–Marítimo`: ertelenmiş, skor yok. `Çorum FK–Fenerbahçe`: TFF web araştırmasında skor var ama dış CSV ile güvenli maç kimliği eşleşmedi; otomatik köprü onu puanlamadı. Başka skoru zorlama, geçmiş tahmini yeniden hesaplama yok.
- Yalnız mevcut GitHub deney dalındaki değişmez SHA mühürleri, B/C2/C3/M4 tahminleri, takım kimlikleri ve ücretsiz haricî sonuçlar kullanılıyor. **Ücretli oran, bahis, yeni pilot veya LITE'a aktarım yok.** Varsayılan `main` dalı değiştirilmedi.
- Günlük otomasyonun **yarınki ilk planlı çalışması henüz gerçekleşmediği için** gelecekteki çalışmayı şimdiden başarılı diye ilan etmiyoruz. Başarısızlık veya yeni çelişki, günlük denetimde raporlanır; sistemin normal kullanım kararı ertelenmez.

## Nihai mühendislik kullanım kararı

**2.6.3'ün analiz amaçlı kullanım sürümü M4 merkezli olarak sabitlendi.** B/C2/C3 kıyasları korunur. Gerçek sabah analiz→kalıcı SHA→mobil ekran→ücretsiz skor eşleştirme→tanımlayıcı performans raporu zincirinin her bir parçası çalıştırılmış ve mevcut kapsamı kanıtlanmıştır. Resmî sonuç kabulünün ağ üzerinden otomatik tam doğrulanması ise ayrı bir güven düzeyi sorunudur ve **tamamlandı diye sunulmaz**. Bu nedenle tahmin kayıtları ve raporlar dürüst kaynak etiketleriyle kullanılır; bahis avantajı garanti edilmez.

**Yeni pilot zorunluluğu yok.** Günlük kullanım ve veri/performans güncellemeleri devam eder; yeni model geliştirme veya testler ancak belirli bir hipotez ve kazanç beklentisiyle ayrı araştırma kararı olarak ele alınır. 96 adaylık geçmiş çalışmayı tekrar başlatma yok.
