# B/C2/C3/M4 dörtlü ileri pilot — yalnız kullanıcı adıyla seçilen maçlar

Durum: **altyapı / deneysel**. Henüz hiçbir gerçek maçın ileri pilot kaydı oluştuğu iddia edilmez.
Eski C3 kuyruğu experiments/263/requests/ ile tamamen ayrıdır. Modül 0 / otomatik maç seçimi yoktur.

## Önce güncel veri kabulü (zorunlu)
Dondurulmuş 4.413 maçlık kaynak bağımsız temel arşiv olarak korunur. Yeni sonuçlar,
var olan experiments/263/season_refresh_263.py ile toplu hazırlanır; 10 ligin maç
kimliği, tarih, kaynak ve önceki satır bütünlüğü doğrulanmadan kabul edilmez.
Dondurulmuş arşivin kendisi güncellenmez.

Bu deney dalında aşağıdaki yollar **yalnız gerçek doğrulama tamamlandıktan sonra** oluşturulur:
- data/quad_accepted_263/extended_history.csv — önceki 4.413 satırı değiştirmeyen güncel veri dosyası
- data/quad_accepted_263/source_acceptance.json — forward_quad.py içindeki verify_snapshot
  kuralına göre status=HUMAN_VERIFIED_SOURCE_ACCEPTANCE, gerçek reviewer, gerçek
  reviewed_at_utc, snapshot_sha256, baseline_sha256, kaynakların source_links listesi

Onay kodu bir kişinin gerçek futbol kaynağını kontrol ettiğini iddia etmek için
kendiliğinden doldurulamaz. Kaynak/onay yoksa yeni pilot **BLOCKED** kalır; ESKİ
veriye sessiz geri dönüş yok. 3 Kasım Salı güncellemesi henüz doğrulanmadı.

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
100 yeni maç; 25 maçta yalnız teknik kontrol; 100'de tek bağımsız ileri karşılaştırma.
Bahis, EV, resmî A/B/C sınıfı ve ana sisteme otomatik terfi YOK.
