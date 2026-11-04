# B/C2/C3/M4 dörtlü ileri pilot — yalnız kullanıcı adıyla seçilen maçlar

Durum: **altyapı / deneysel**. Henüz hiçbir gerçek maçın ileri pilot kaydı oluştuğu iddia edilmez.
Eski C3 kuyruğu experiments/263/requests/ ile tamamen ayrıdır. Modül 0 / otomatik maç seçimi yoktur.

## Önce güncel veri kabulü (zorunlu)
Dondurulmuş 4.413 maçlık kaynak bağımsız temel arşiv olarak korunur. Yeni sonuçlar,
var olan experiments/263/season_refresh_263.py ile toplu hazırlanır; 10 ligin maç
kimliği, tarih, kaynak ve önceki satır bütünlüğü doğrulanmadan kabul edilmez.
Dondurulmuş arşivin kendisi güncellenmez.

Bu deney dalında ilgili kaynaklar **4 Kasım 2026 tarihinde gerçekten oluşturulmuş ve testle kabul edilmiştir**:
- data/quad_accepted_263/extended_history.csv — 4.518 maçlık sabit SHA
  1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9;
  eski 4.413 satır yerinde korunmuştur.
- data/quad_accepted_263/source_acceptance.json — gerçek kullanıcının açık sınırlı
  araştırma onayını, 4 Kasım UTC zamanını ve 42 kaynak bağlantısını içerir.
  Bu **bütün 4.518 maçın resmî kaynaklarda bağımsız doğrulandığı anlamına gelmez**.
- 3 Kasım tarihli 9 ENG2 maçı sonuç kaynaklarıyla karşılaştırıldı; ilk yarı,
  şut/korner alanları bulunmayan 9 kaydın boş alanları uydurulmadı.
- İlk 6–8 Kasım için ligin veri güncelliği ayrı `weekend_source_readiness_263.py`
  kontrolündedir. Bu denetim maç günü kaynak yenilemesini, resmî fikstürü,
  ilk 11'i, güncel bookmaker oranını veya pilot tahminini **otomatik onaylamaz**.

Kaynak onayı 7 günden eskiyse veya SHA değişirse ileri kayıt reddedilir.
Bu durumda eski veriye sessiz dönüş veya sahte insan onayı YOK.

## Gerçek kullanıcı maç isteği
Kullanıcı maç adını söyledikten ve kabul edilmiş veri hazırlandıktan sonra yalnızca
**YENİ** experiments/263/quad_requests/YYYYMMDD_istek01.json oluşturulur:

{
  "schema": "quad_named_match_batch_request_v1",
  "matches": [
    {"league":"TUR1","home":"Besiktas","away":"Genclerbirligi"}
  ]
}

Bu sadece **istek biçimi örneğidir**; dosya oluşturulmadı ve pilot başlamadı.
Maç tarihi/saati/kimliği/resmî onay kullanıcı JSON'unda bulunmaz.
Gerçek CI, bağımsız canlı resmî maç kapısını çalıştırır. Başarılı kayıt,
forward_quad_263/YYYY-MM-DD/*.json altına tek ortak maç + dört model çıktısı olarak
eklenir; dosyanın üzerine yazılmaz ve SHA ile değişiklik tespit edilir.
GitHub Actions botun commit atabilmesi için dal izni gereklidir.
Başarısız deneme quad_batch_reports altına engel nedeni yazıp CI'yi başarısız gösterir.
Bir koşu başarısız oldu diye aynı isteği tekrar tetikleme; önce kaynak hatasını düzelt.

## Kapsam
6–8 Kasım'da 96 sabit aday maç; 25 geçerli kayıtta teknik kontrol; 9 Kasım Pazartesi gerçek pre-KO kayıtlar üzerinden tanımlayıcı sonuç raporu. 3 ayrı maç günü bağımsız istatistiksel üstünlük kanıtı değildir.
Bahis, EV, resmî A/B/C sınıfı ve ana sisteme otomatik terfi YOK.
