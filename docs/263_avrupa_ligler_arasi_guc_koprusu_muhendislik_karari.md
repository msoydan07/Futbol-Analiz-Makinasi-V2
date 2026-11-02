# 2.6.3 — Avrupa Kupaları: Ligler Arası Güç Köprüsü (mühendislik kararı)

Karar tarihi: 2026-11-02. Durum: TASARIM / VERİ KANITI BEKLEYEN, UYGULANMAMIŞ.

## Problem — örnek

2026-10-14 Aston Villa 6-0 Fenerbahçe UEFA Şampiyonlar Ligi.
Resmî maç: https://www.uefa.com/uefachampionsleague/match/2049582--aston-villa-vs-fenerbahce/
TFF: https://www.tff.org/default.aspx?ftxtID=51646&pageID=267

Hedef **6-0 gibi uç skoru geri dönük uydurmak** değil, maç öncesinde iki kulübün ligleri farklıyken kazanma olasılıklarını doğru ölçeğe yerleştirmek.

Bir takımın kendi liginde üst sıralarda bulunması, farklı güçlü bir ülkenin orta sıra takımından daha kuvvetli olacağını göstermez. Ham lig sırası ve ev ligindeki gol ortalaması **farklı ligler arasında doğrudan kıyaslanmayacak**.

## Yapılması gereken iki ayrı düzeltme (sırası zorunlu)

**A: Ülkeler ve takımlar arasında ortak güç skalası (öncelik 1).**

- 10 yerel ligin geçmiş maçlarından **o ligin kendi ortalamasına göre** takımın hücum/savunma üstünlüğünü maç öncesi tahmin et.
- Resmî UEFA CL+EL maçları, gerektiği ölçüde UEFA Conference League (tahmin kapsamı değil, yalnız ligler arası köprü verisi) üzerinden ülkeleri/ligleri birbirine bağla.
- Sadece UEFA'ya katılan üst kulüplerin ortalaması bütün ülke ligine uygulanamaz: katılım/seçim yanlılığını ele al; ülke ligi + takım sapmasını kısmi havuzlama ile birlikte tahmin et, bilinmeyen takımlarda belirsizlik raporla.
- Dış ClubElo tarihsel maç öncesi dereceleri, varsa, ayrı referans model; UEFA beş yıllık kulüp/ülke katsayıları yalnız ek göstergedir, otomatik kazanma olasılığı değildir.
- Saha avantajı, ev/deplasman farkı ve tarihten bağımsız olmayan takım performansı ayrı tut; daha sonraki maç veya sezon sonu derecesi tahmine sızamaz.
- En önemli kabul testi: 'İngiltere orta sıra takımı — Türkiye lideri' gibi eşleşmeler için, tahmin **ülke ligi sırası nedeniyle yanlış üstünlük varsayıyor mu?** Sadece tek bir anekdotla karar yok.

**B: Karşılaşmaya özgü davranış / taktik farkı (öncelik 2).**

- A'dan çıkan doğrulanmış global güç farkından sonra rakibin savunma/hücum seviyesi, UEFA turnuvası, eleme/lig, 1.-2. maç, toplam skor, puan ihtiyacı gibi **maç öncesinde bilinen** özellikler.
- Takımın yüksek kaliteli rakibe karşı şut sayısı, xG, topa sahip olma ve gol yeme/gol atma karakteri geçmişte ne kadar değişmiş? Aynı sinyali iki kez sayma; xG eksikse 'DOĞRULANAMADI'.
- 'Avrupa maçı hep az gollü', 'İngiltere takımı hep kazanır', 'puan gerekliyse kesin hücum eder' gibi sabit dogmalar yasak.
- Değişik taktik olasılıklarını doğrudan gerçekleşmiş motivasyon gibi sunma; belirsizlik belirt.

### C: UEFA güncel puan durumu ve fikstür zorluğu (2 Kasım kesinleştirme)

**Karar: İkili geçmiş (H2H) ayrı istatistik/araştırma/deney özelliği olarak
kapsamdan çıkarıldı.** Birkaç eski karşılaşma, o dönemki teknik direktör,
kadro, oyun anlayışı ve formu yansıtabilir; bugün için güvenilir bağımsız
kanıt değildir. Geçmiş maçlar zaten genel rakip kalitesi / güç modelinin
tarihsel veri girdisidir; aynı maçlar 'H2H üstünlüğü' adıyla ikinci kez
ağırlıklandırılamaz. H2H için veri taraması, ilave modül,
özel test veya kullanıcıdan kayıt talebi açılmayacak.

**İstisna: Aynı eleme eşleşmesinin rövanşındaki ilk maçın skoru** mevcut
eşleşmenin toplam gol/eleme durumudur, 'geçmiş H2H gücü' değildir.
Mevcut `uefa_match_context_263.py` içerisinde sadece bu anlamıyla
korunur. Örnek: ilk ayak 2-0 ise rövanştaki toplam skor ihtiyacı
model için bağlamdır; önceki yıllarda birbirleriyle oynadıkları maçlar
başka bir H2H özelliği oluşturmaz.

Veri kararları:
- **Mevcut** `experiments/263/europe/uefa_match_context_263.py` lig
  aşamasında iki takımın maç öncesi `points, goal_difference, rank, played`
  alanlarını taslak seviyesinde alıyor. Henüz canlı UEFA kaynağıyla
  bağımsız doğrulama yok; bunlara otomatik `VERIFIED` denmeyecek.
- **Fikstür zorluğu:** Her takım farklı rakiplerle oynar; aynı puan
  farklı rakip gücü dağılımlarında toplanabilir. Ham puan/sıra
  doğrudan karşılaştırma yapılmaz. Oynanmış rakiplerin ortak
  ligler-arası skaladaki **o maçtan önce bilinen** güç derecesi,
  ev/deplasman koşulları ve örneklem sayısı ölçülür.
  Maç sonrası güncellenmiş rating ile geçmişi geriye dönük
  tahmin etmek (lookahead) yasaktır.
- **Zaman:** Maç gününden ve analiz anından sonraki rakip sonuçları,
  güncel puan ve sonradan gelişen eleme senaryoları maç öncesi
  özelliğe taşınamaz. İlk hafta hiç maç yoksa tahminle sıfır
  puan/rakip ratingi doldurulamaz; veri eksikliği açık yazılır.
- **Turnuva aşaması:** CL ve EL lig aşaması 36 takımlı;
  puan durumu, kalan hafta/maç sayısı, averaj ve rakip zorluğu
  birlikte raporlanır. Sezon ortasındaki sıra nihai sıralama
  gibi sunulmaz.
  Kaynak:
  https://documents.uefa.com/r/Regulations-of-the-UEFA-Champions-League-2026/27/Article-17-Match-system-league-phase-Online
  https://documents.uefa.com/r/Regulations-of-the-UEFA-Europa-League-2026/27/Article-17-Match-system-league-phase-Online

**Toplu kabul deneyi:** Mevcut önceden planlanan kronolojik
karşılaştırmada ana ligler-arası güç ölçeğine **yalnız kaynaklı,
rakip zorluğuna göre değerlendirilmiş UEFA puan durumunun**
ek katkısı araştırılır. H2H özelliği/ablation kolu yoktur.
432 maçtaki daha basit puan/hafta çalışması ileri sezonda
fayda sağlamadığı için bu yeni özelliğe otomatik artı puan
veya gol katsayısı tanımlanmaz. Yeni bir M5 kurulmaz.

## Ön-kayıt yapılacak tek toplu karşılaştırma

- Referans M0: Yerel lig seviyelerinin doğrudan karşılaştırılması / halihazırdaki
  naif ligler arası yöntem (varsa).
- M1: Aynı geçmiş veri + maçtan önce hesaplanan ülkeler arası ortak güç köprüsü.
- M2: M1 + rakibe özgü hücum-savunma/taktik göstergeleri.
- Dış doğrulama M3 değil: maç öncesi kaydedilmiş piyasa marjsız olasılıkları
  sadece bağımsız BENCHMARK; ayrı beşinci tahmin motoru yok.
- Karar ölçüleri: 1X2 Brier/logloss, gol sayısı ihtimal/logloss, 2.5 Alt/Üst
  Brier ve kalibrasyon, takımın maçı kazanma olasılığının makullüğü.
  Eşleşmiş aynı maçlar, tarih sıralı eğitim/validasyon/test,
  lig ve sezon bazında rapor, düşük örneklem için hata aralıkları.
- Önce toplu veri eksikleri ve deney tasarımı kapanacak; sonra **tek toplu test, tek rapor**.
  Kötüleşme varsa ekleme yapılmaz; M1 veya M2 sadece güçlü ve kararlı dış
  test kanıtıyla terfi adayı olabilir.
- Zamanında kadro/oran yoksa tahmin matematiği durmaz ama eksikler açık
  belirtilir; A/B/C onayı ve 100 maçlık kayıt süreçleri ayrı.

## Kaynaklar

UEFA maç kaydı:
https://www.uefa.com/uefachampionsleague/match/2049582--aston-villa-vs-fenerbahce/
UEFA kulüp katsayı yöntemi (seri başı/turnuva puanları, doğrudan galibiyet olasılığı değil):
https://www.uefa.com/nationalassociations/uefarankings/club/
Ligler arası performans köprüsü için tarihsel yöntem, FiveThirtyEight:
https://fivethirtyeight.com/methodology/how-our-club-soccer-predictions-work/

## Değişmez sınırlar

identity.LEAGUES içindeki 10 yerel lig, sezon verisi, Salı veri
güncellemesi, C2/B/C3/M4, üretim/main, A/B/C ve 100 maçlık tahmin
defterine bu kararla hiçbir değişiklik yapılmadı. Avrupa verileri ve
köprü testleri mevcut deney dalında tutulacak. Bir resmî maç sonucu
tek başına bir modelin o maç öncesi tahmininin doğruluğunu ispatlamaz.
