# 22 liglik veri işinde yeni kaynak denetimi — 14 Kasım 2026

**Kapsam:** 2025/26 ile 2026/27 (yalnız 13 Kasım'a dek oynanan sonuçlar). Kullanıcı xG girişini daha sonra yapacak. **Ana M4, on liglik üretim, eski tahmin mühürleri ve bütün matematik modelleri dokunulmaz.**

## Bir bakışta

| Sınıf | Maç | Kanıt | Bu turda kalıcı skora yeni kayıt |
|---|---:|---|---:|
| 5 güncel ligde yalnız kişisel araştırma kaynağında bulunan | **633** | Kimlik/sayı kaynak araştırması var; ham yeniden yayın izni yok | **0** |
| 4 güncel ligde kaynak sayımından saptanmış ilave aday | **118** | Mevcut 176 maçın 176'sı tarih/kanonik takım/FT'de eşleşti; kalanlar bağımsız resmî sonuç onayı bekliyor | **0** |
| **Yeni kaynak adayı toplamı** | **751** | **Yeni model eğitim izni yok** | **0** |

118'in dağılımı: İskoçya **33**, İsviçre **21**, Yunanistan **34**, Avusturya **30**. 633'ün dağılımı: National League **190**, Segunda **141**, Serie B **110**, Ligue 2 **108**, Danimarka **84**. **751, doğrulanmış yeni oynanmış maç sayısı veya eğitim için uygun maç sayısı değildir; kaynağa erişilebilen ve hukuki/kimlik kapısı açık aday toplamıdır.**

## Gerçekten kontrol edilen özgün açık kaynaklar

14 Kasım'da OpenFootball'ın birincil GitHub deposundan 2026/27 dosyaları açılıp **canlı blob SHA** ile önceki dosyanın SHA'sı karşılaştırıldı:

| Lig | Mevcut CC0 2026/27 kaynak | Eski kayıtta bulunan skorlu satır | Kaynakta yeni skor |
|---|---|---:|---:|
| İskoçya | [scotland/2026-27_sco1.txt](https://github.com/openfootball/europe/blob/master/scotland/2026-27_sco1.txt) | 42 | 0 |
| İsviçre | [switzerland/2026-27_ch1.txt](https://github.com/openfootball/europe/blob/master/switzerland/2026-27_ch1.txt) | 54 (+3 farklı araştırma kaynağında) | 0 |
| Yunanistan | [greece/2026-27_gr1.txt](https://github.com/openfootball/europe/blob/master/greece/2026-27_gr1.txt) | 35 | 0 |
| Avusturya | [2026-27/1-bundesliga.txt](https://github.com/openfootball/austria/blob/master/2026-27/1-bundesliga.txt) | 42 | 0 |

Bu dosyaların özgün depolarındaki [CC0 lisansı](https://github.com/openfootball/europe/blob/master/LICENSE.md) yeniden kullanıma izin verir. Ancak içerik SHA'ları önceki araştırma kayıtlarındaki sürümle **aynı** olduğu için dosyaları tekrar ithal etmek **yeni maç sağlamaz**. Önceki 4.218 araştırma skor-olgusu kabulünü ya da haklarını da genişletmez.

Diğer açık veri katalogları:
- [openfootball/football.json 2026/27](https://github.com/openfootball/football.json/tree/master/2026-27) yalnız bazı birinci seviye liglerde dosya içeriyor. ENG5 / ESP2 / ITA2 / FRA2 / DNK1 düzeyinde oynanmış sonuç dosyası yok.
- [openfootball/england/2026-27](https://github.com/openfootball/england/tree/master/2026-27): Premier League + Championship. National League yok.
- [openfootball/espana/2026-27](https://github.com/openfootball/espana/tree/master/2026-27): yalnız birinci lig. Segunda 2026/27 yok.
- [openfootball/italy/2026-27](https://github.com/openfootball/italy/tree/master/2026-27): yalnız Serie A. Serie B yok.
- [openfootball/europe/denmark](https://github.com/openfootball/europe/tree/master/denmark): mevcut klasörde 2026/27 yok; gösterilen son sezon dosyaları 2024/25.

Bu tarama **bütün internet üzerinde** açık lisanslı veri yok demek değildir; yalnızca kontrol edilen resmî depo yolları kapsamını gösterir.

## Ücretsiz CSV keşfindeki yeni hak engeli

[Football-Data.co.uk veri sayfası](https://www.football-data.co.uk/data), özel kişiler için ücretsiz CSV sunarken **otomatik bot/scraper/AI aracılığıyla veri eğitimi ürünleri için kullanımı dışladığını** açıkça belirtiyor. Bir ücretsiz CSV bağlantısını almak **otomatik AI veri toplama veya eğitim izni** vermez.

Bunun sonucu:
1. Bu kaynak üzerinden 633 ya da 118 maçı yeni otomatik indirmeyle çekmedik.
2. Daha önce aynı kaynaktan yalnız skor karşılaştırması yapılan araştırma denetimleri **yeniden yayın / yeni model eğitim izni** anlamına gelmez.
3. Kaynak sahibi ayrıca açık izin vermediği müddetçe **programatik veri kaynağı olarak etkinleştirilmeyecek**.

[Football Charts](https://www.football-charts.com/terms) canlı API'si kişisel araştırma amacıyla erişilebilir olsa da önemli miktarda ham yanıtın halka açık GitHub'a yayımlanmasına açık izin vermiyor. [open-matchday](https://github.com/oladeeayo/open-matchday) derlemesinin kendi erişilebilirliği ESPN/Soccerway/fixturedownload üst hak sorununu çözmüyor. [MatchDaySync](https://matchdaysync.com/developers) bazı sezonlar için halka açık CSV sunuyor ancak kendi açıklamasında mevcut siteyi 11 Ekim yedeğinden geri yüklediğini ve güncel veri akışının bağlı olmadığını belirtiyor; 13 Kasım kesiminin bütün güncel maçlarının ikinci teyidi sayılmaz.

## Veri kararı ve kalan gerçek iş

- **Önceki kalıcı satır toplamı 9.460**, 4.617 çekirdek, 4.218 araştırma-olgu kalite seçimi, 625 kaynak HOLD, 200 eski düzeltme bağlantısı: **hiçbiri değiştirilmedi**.
- Bu turda **0 ham satır yeniden yayınlandı, 0 yeni eğitim izni, 0 model matematik değişikliği**. 1.855 xG'lik kullanıcı çalışma kitabı da aynı kaldı.
- **Kaynak kalitesi**: 118 ek adayın her biri, bağımsız resmî sonuç (tarih, ev/deplasman, 90 dakika final, ertelenme/terk, aşama) doğrulamasına ihtiyaç duyuyor.
- **Kaynak hakkı**: 633 + 118 için kaynak sahiplerinden **ayrı bir yeniden kullanım hakkı** veya özgün CC0/ODbL karşılıkları gerekli. Ücretli veri satın alınması varsayılmadı.
- Sıradaki verimli çalışma, **yalnız değişmiş yeni kaynak/izin/maç kanıtı** olan öğeleri kontrol etmek. Aynı GitHub dosya SHA'sını veya aynı 176 doğrulanmış maçı tekrar tekrar taramayacağız.

### Denetlenebilir çıktı

[Makinece doğrulanan 751 aday kaynak-hak kilidi](./2026_27_751_SOURCE_RIGHTS_AND_STALE_CC0_FINAL_GATE_20261114.json) · [Kaynak hakları ve eski envanteri karşılaştıran salt okunur Python kontrolü](./verify_751_current_source_rights_hold_and_cc0_freshness_once.py) · [GitHub Actions başarılı test](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43635381027).

**Mühendislik sonucu:** Önce veri kalitesi ve kullanım hakkı; sonra xG bütünleme; en sonunda matematik. Açık sorunlar kapandı gibi gösterilmedi.
