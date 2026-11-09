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

## GitHub işletimi
`.github/workflows/263-postmatch-csv-provisional-readonly.yml` GitHub Actions'ta push ve manuel `workflow_dispatch` ile çalışır. **Bu iş akışı deney dalında olduğundan otomatik günlük saat planı henüz kurulmamıştır.** Günlük programlama için GitHub'ın varsayılan dalında uygun dağıtım veya mevcut programlı işin açık bağlantısı gerekir. `main` dalını değişmeden bıraktık.

**Son durum:** Günlük işlem zincirindeki resmî skor eksikliği araştırma amaçlı ön kontrolle kısmen kapandı; resmî/onaylı kalıcı skor hattı otomatikleştirilmiş kabul edilmez. Kullanım kararı: M4 ile analiz yapmaya devam.
