# 2.6.3 — Kullanıcının komutuyla 10 lig fikstüründen yeni100 istek köprüsü

**Karar:** 7 Kasım 2026. Kullanıcı maç sabahı “bugünün maçlarını getir, analiz et ve mühürle” diyerek işlemi kendisi başlatır. Sabit saatte kendiliğinden yeni pilot başlatılmaz. 09.00'da mevcut kontrol otomasyonuna dokunulmadı.

## Hazırlanan teknik köprü
`experiments/263/sabah_manual_preflight_bridge_263.py`

1. `review`: `sabah_10league_manifest_preflight_263.py` ile **aynı gün** üretilen, en çok 10 dakika önce kontrol edilmiş resmî adayları okur, 10 ligin *kaynak olarak kontrol edildiğini* denetler. Eksik ligleri açıkça listeler. Henüz başlamamış ve KO'ya 2 dakikadan fazla kalmış maçların tam kanonik kimlik, başlangıç ve kaynak SHA'sını korur. Sonuç **yalnız inceleme listesi** ve hiçbir koşulda kendiliğinden pilot talebi değildir.
2. `prepare`: sadece **o gün kullanıcının açık analiz komutu verildikten sonra**, operatör `--user-command-authorized` ile ve tam kanonik takım+başlama ID'lerinden oluşan seçilmiş listeyle çalıştırabilir. Seçilmeyen maç zorlanmaz, aynı ID ikinci kez eklenmez, eski/yanlış maç bloke edilir. Çıktı ancak kullanıcının açıkça istediği `SABAH_TOPLU_V1` biçiminde olur.
3. `save_request`: dosyayı `experiments/263/sabah_requests/` içine yalnız **yeni dosya** olarak yazar, mevcut dosyayı üzerine yazamaz; `sabah_batch_263.named` ile gerçek istek biçimini ayrıca doğrular.
4. **ÖNEMLİ:** Bu script Git commit/push yapmaz. Eski GitHub `263-sabah-new100-on-request.yml` yalnız yeni isteğin kullanıcının açık komutuna bağlı ayrı bir Git push'ı sonrası tetiklenir. Orada lig ve maçın *canlı resmî kapıdan yeniden geçmesi*, dört model, maç öncesi SHA, ardından Pinnacle tek sorgu rezerve-kilit ve onaylı toplu+tekli PDF zinciri çalışır. Bir maç bu kapıdan geçmezse **PAS/engelli** olur; köprü tarafından mühürlü sayılmaz.
5. `new100` geçmiş kayıtları, main dalı, model ağırlıkları, 09.00 otomasyonu, Pinnacle API bakiyesi değişmedi.

## Operatör kullanım örneği (sadece kullanıcı aynı sabah gerçekten istediğinde)
- `python experiments/263/sabah_10league_manifest_preflight_263.py --day YYYY-MM-DD --out /tmp/today.json --mobile /tmp/tenleagues.md --candidate-manifest /tmp/not-approved.json`
- `python experiments/263/sabah_manual_preflight_bridge_263.py --mode review --preflight /tmp/today.json --output /tmp/review.json`
- İncelemeden maç ID seçim listesini, kullanıcının o günkü istediği kapsam doğrultusunda çıkart. Örnek belgenin `candidates` alanındaki *yalnız* `league,home_id,away_id,kickoff_utc` anahtarları.
- `python experiments/263/sabah_manual_preflight_bridge_263.py --mode prepare --preflight /tmp/today.json --selection /tmp/chosen.json --user-command-authorized --output experiments/263/sabah_requests/user_DAY_request.json`
- **Ayrı ve bilinçli GitHub commit/push** olmadan gerçek pilot başlamaz.

## Eksik kalan gerçek saha kabulü
- 10 ligde tam maç kapsaması garanti değil; ENG2 resmî sayfası JS ağırlıklı ve yedek TV seçimi bütün maçları sağlamıyor.
- Tek bir 8 Kasım sabahı **gerçek** kullanıcı komutu ile bu köprünün açılıp GitHub new100 işinin gerçek maçlarla 4 model + aynı sabah Pinnacle + SHA + iki PDF ürettiğini canlı doğrulamak gerekiyor.
- İşlem yapılmadıysa “mühürlendi” denmeyecek. Bu iş offline testlerin yeşil olmasıyla tamamlanmış sayılmaz.
