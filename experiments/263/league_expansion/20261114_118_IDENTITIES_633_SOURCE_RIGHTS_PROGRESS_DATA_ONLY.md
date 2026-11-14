# 22 lig × 2 sezon — yalnız veri mühendisliği, 14 Kasım 2026 akşam
**Araştırma dalı:** `research/263-13-lig-22-havuz-20261113`  
**Maç kesim günü:** 13 Kasım 2026  
**Kapsam:** Kaynak hakları, kaynak sayım farkları, eski arşivle gerçek maç kimliği eşleşmeleri. **Matematik, yeni pilot, xG girişi veya model eğitimi YOK.**

## A. 118 şüpheli güncel lig maçı — sayım farkı artık tarih–takım–skor eşleşmesiyle araştırıldı

Geçmişteki dört kaynak farkı `2026_27_17_persisted_leagues_one_freshness_aggregates_only_20261114.json` içinde sadece toplam sayıydı. Bu turda yalnız dört ilgili ligi canlı kaynaktan **RAM içinde okuyup**, GitHub'daki mevcut maçların tarihini, lig içi takım eşadlarını ve final skorunu ayrı karşılaştırdık. Kaynak ham maç sonuçları, isimleri veya toplu JSON çıktısı GitHub'a yazılmadı.

| Lig | Mevcut kalıcı | Kaynakta skorlu benzersiz | Kaynakla **birebir tarih–takım–FT uzlaşan eski kayıt** | Kaynakta eskisine ek aday |
|---|---:|---:|---:|---:|
| SCO1 İskoçya | 42 | 75 | **42** | **33** |
| CHE1 İsviçre | 57 | 78 | **57** | **21** |
| GRE1 Yunanistan | 35 | 69 | **35** | **34** |
| AUT1 Avusturya | 42 | 72 | **42** | **30** |
| **Toplam** | **176** | **294** | **176** | **118** |

- Dört ligde de mevcut 176 skor için bu kaynakla doğrudan skor çelişkisi çıkmadı. Lig içi isim haritaları *önceden bilinen kulüp kimliklerine* sabitlendi; skor benzerliğiyle yeni takım ismi icat edilmedi.
- Bu yöntem **118'in mevcut 176 maçın yeni yazılmış mükerrer kopyaları olmadığını**, kapsam dahilindeki kaynakta 118 ilave maç kimliği bulunduğunu gösterir. **118 maçın tek tek resmî kaynakla doğrulandığı anlamına gelmez.** Bazı skorlu görünen kaynak olayları daha sonra ertelenmiş/hükmen olabilir.
- Araştırma kanıtı: [4 lig kaynak kimliği/sonuç **toplu** eşleşme raporu](./2026_27_FOUR_118_SCOPED_CROSS_SOURCE_FIXTURE_IDENTITY_METADATA_20261114.json) ve [tekrarlanabilir sınırlı QA kodu](./resolve_118_four_2026_27_identities_personal_metadata_only.py).
- Doğrulama: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43634513584 (önceki tam kulüp eşadı karşılaştırması https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43634404574).
- İkinci bağlam örnekleri: İskoçya lig organizatörü [SPFL resmî sonuçlar](https://spfl.co.uk/league/premiership/results); Avusturya güncel [2026/27 maç çizelgesi](https://www.liga1.at/spielplan-tabelle.html). Bunlar bu turda 118 maçın tek tek federasyonca doğrulandığı iddiası değildir.

**Karar:** 118 yeni maç **kalıcı skor veri kümesine / M4'e / model eğitimine alınmadı**. Maç kimliği ve kaynak kullanım hakkı onayı ayrı tutulur. Artık aynı dört kaynağı yalnızca sayı için yeniden sorgulamak gerekmiyor.

## B. 633 güncel sezon alt lig maçı — mevcut kaynak var, kalıcı paylaşım hakkı yok

Önceki **Football Charts kişisel araştırma API** denetiminden:
- ENG5 (İngiltere National League) **190**
- ESP2 (İspanya Segunda) **141**
- ITA2 (İtalya Serie B) **110**
- FRA2 (Fransa Ligue 2) **108**
- DNK1 (Danimarka Superliga) **84**
- **Toplam: 633** kaynakta gözlenmiş sonuç kimliği; **9.460 kalıcı kaynak satırına eklenmiş değildir**.

Bağımsız üçüncü taraf `open-matchday` derlemesinde aynı beş lig için **632** kaynak satırı sayılmıştı (ENG5 **189**, diğerleri 141/110/108/84); eski ilk kaynağın aynısı kabul edilmedi. Özellikle ENG5 189/190 farkı bugüne dek aynı maç kimliğinden bağımsız teyit edilmedi. Üçüncü taraf derlemenin ESPN/Soccerway/fixturedownload **üst veri hakları açık olmadığı için ham veri taşıma engeli sürüyor**.

### Gerçekten bakılan serbest lisans seçenekleri
- `openfootball/football.json` **CC0** ve `openfootball/espana`, `openfootball/italy` açık sezonsal kaynakları kontrol edildi. **2026/27** `football.json` klasöründe `es.2`, `it.2`, `fr.2` ya da ENG5 / DNK1 dosyası yok. `espana/2026-27` yalnız LaLiga 1. seviye, `italy/2026-27` yalnız Serie A içeriyor. Bu, başka bir CC0 sağlayıcının hiçbir zaman bulunamayacağı anlamına gelmez.
- `OpenLigaDB` **ODbL** sağlayıcısında önceki 2026 sezon katalog denetimi, bu beş hedef ligi geçerli ve dolu kaynak olarak bulmamıştı; Alman 2. Bundesliga ve İsviçre eski sezon gibi diğer ligler var. Sırf lig adı benziyor diye maç ithal edilmedi.
- `Football Charts` [Terms of Sale / Using the API](https://www.football-charts.com/terms): Ücretsiz kişisel araştırma/özel proje ve türetilmiş istatistiklere izin verir; **ham API yanıtını veya önemli bölümünü veri seti olarak herkese açık yeniden yayımlamaya izin vermez**. GitHub'a yalnız 4 lig için toplu karşılaştırma istatistikleri yazıldı.
- `Cornerflick` [veri lisansı ve kökeni](https://cornerflick.com/data): CC BY 4.0 yayıncı derlemesi ve anotasyonu için; maç sonuçlarının **api-football** kaynaklı üst hakları ayrıca geçerli. Böyle bir kaynak tüm arşive yeni, hakları açık bir kopya hakkı oluşturmaz.
- `football-data.co.uk` ilgili sezon CSV'lerini ücretsiz ve kişisel araştırmaya elverişli yayımlıyor; açık **ham veri yeniden dağıtma ve model eğitimi** izni otomatik varsayılmadı.

**Karar:** Kaynakları ücretsiz görebiliyoruz ancak **633'ü izinsiz yayımlayarak "arşiv tamamlandı" demeyeceğiz**. Hakları temiz bir yayın veya veri sağlayıcıdan yazılı yetki gelmeden bu beş sezonda yeni ham maç yayımlamıyoruz.

## C. Kalıcı güvenlik kilitleri
- Eski ana skor arşivi **4.617**, genişleme işaretçisi **4.843**, kaynak satırlarının toplamı **9.460** aynı kaldı.
- Önceden filtrelenen 625 kaynak satırının kararı, 200 doğrulanmış eski skor/tarih düzeltme bağlantısı ve 1.855 xG kullanıcı dosyası değişmedi.
- Ana 10 lig M4, B/C2/C3, 96 eski pilot, 40 NEW100 mühür, sonuç skorlama ve otomasyonlar değiştirilmedi.
- **Yeni kaynaklardan model eğitimine kabul: 0.** Kullanıcının yeni talimatı gereği matematik/test/parametre işlerine başlanmadı.

**Kesin durum:** **118 kaynakta ilave maç adayı var** (tarih/takım/skor kıyaslı), fakat bağımsız hak/olgu kabulü açık; **633 maç kişisel araştırma kaynağında erişilebilir** fakat kalıcı izin açık değil. Sonraki veri işi bu spesifik iki engelin kanıtını bulmak; eski başarılı karşılaştırmaları döngüye sokmamak.
