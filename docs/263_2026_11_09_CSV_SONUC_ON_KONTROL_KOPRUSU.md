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

## GitHub işletimi
`.github/workflows/263-postmatch-csv-provisional-readonly.yml` GitHub Actions'ta push ve manuel `workflow_dispatch` ile çalışır. **Bu iş akışı deney dalında olduğundan otomatik günlük saat planı henüz kurulmamıştır.** Günlük programlama için GitHub'ın varsayılan dalında uygun dağıtım veya mevcut programlı işin açık bağlantısı gerekir. `main` dalını değişmeden bıraktık.

**Son durum:** Günlük işlem zincirindeki resmî skor eksikliği araştırma amaçlı ön kontrolle kısmen kapandı; resmî/onaylı kalıcı skor hattı otomatikleştirilmiş kabul edilmez. Kullanım kararı: M4 ile analiz yapmaya devam.
