# 2.6.3 — 2025/26 UEFA Şampiyonlar + Avrupa Ligi ortak veri kapsamı / tek kabul raporu

**Tarih:** 2 Kasım 2026
**Karar:** KAPSAM ENVANTERİ TAMAMLANDI — GÜÇ MODELİ / KALİBRASYON ONAYLANMADI.

Bu rapor aynı sezondaki iki UEFA lig aşamasını yalnız bizim seçtiğimiz
10 yerel lig içinden gelen takımların *birbirleriyle* oynadığı
maçlar bakımından inceler; yeni ülke ligi araştırmaz.

## Kanıt ve kaynak sınırları

- **Başarılı toplu GitHub Actions:** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41480542512
- **10/10 yeni güvenlik testi PASS;** son çalışmada her iki tarihsel
  kaynak indirilip açıldı, kapsam ve kimlik kontrollerinden geçti.
- Artefakt: `263-uefa-2025-26-cl-el-ten-league-single-coverage`.
  İçerik: birleştirilmiş 2025/26 özet raporu JSON, tarihli aday
  maçlar JSON ve Markdown özet. **REVIEW_ONLY**, üretim girdisi değil.
- **CL kaynağı**: `openfootball/champions-league`, dondurulmuş
  `abfaeddc2ee3d14f99ecc163c9ddb46cb4d67cef`,
  `2025-26/cl.txt`. 144 maç / 487 gol; tüm 8 haftayı
  ve 36 kulübün 8'er maçını içerir.
- **EL kaynağı**: `https://fixturedownload.com/feed/json/europa-league-2025`,
  SHA256 `288f7410e0ef5bb5236408e2239d5351e8bcbfb21dc7f805e4f22dea267d3ae5`.
  144 maç / 386 gol, 8 hafta x 18 maç.
- **Resmî UEFA çapaları (toplam 12 ayrı maç):**
  - CL https://www.uefa.com/uefachampionsleague/news/029c-1e9a2f63fe2d-ebf9ad643892-1000--champions-league-2025-26-all-the-results/
  - EL https://www.uefa.com/uefaeuropaleague/news/029c-1e9b4e18c28e-3bb76afa22ac-1000--europa-league-league-phase-results-by-team/
  - Her turnuvadan 6 önceden tanımlı maçın tarih, skor ve
    takım yazımı kontrol edildi. **Bütün 288 maç tek tek
    resmî UEFA karşılaşma sayfasından doğrulanmadı.**
- **CL kaynak takım isimleri** ile UEFA'nın 2025/26 resmî
  kısa takım adları arasındaki 19 açık eşleme:
  https://www.uefa.com/uefachampionsleague/news/0296-1d21e9bdf7e4-808a7511165c-1000--2025-26-champions-league-format-dates-draws-final/
  Ekli JSON bunları yalnız kanıtlı *aday* kimlik olarak korur.
  UEFA'nın her takıma ait sayısal kulüp ID'si ayrıca teyit edilmedi.
- Önceki çalışma kapsamında kaynaklı `Braga` → `SC Braga`
  özel eşlemesi bu birleşimde korundu.

## Gerçek ölçülen 2025/26 kapsam

| Ölçüt | Şampiyonlar Ligi | Avrupa Ligi | Toplam |
|---|---:|---:|---:|
| Kaynaktaki tamamlanmış lig aşaması maçı | 144 | 144 | **288** |
| İki taraf da 2025/26 canonical 10 lig üyeliğinde — aday | **95** | **37** | **132** |
| Takım kapsamı veya çözülemeyen kaynak ismi nedeniyle dışarıda | 49 | 107 | **156** |
| Tam UEFA sayısal kulüp ID'si ve maç ID'si ile model eğitimi için onay | 0 | 0 | **0** |

**CL özel durum:** 36 UEFA takımından **29** takımın
2025/26 yerel 10 lig üyeliği canonical isim ve 19 açık kaynak ad
eşlemesiyle aday olarak belirlenebildi. Geri kalan yedi
takım için başka ülke ligi açılmadı. `AS Monaco FC (MCO)`,
Monaco'nun 2025/26 **FRA1** kaydı nedeniyle kapsamda; ülke kodu
tek başına üyelik ölçütü değil.

**EL özel durum:** Braga kaynak adı düzeltmesiyle 32 adaydan
**37 adaya** çıkıldı. Eleme nedenleri ve tanınmayan adlar
önceki kaynak-auditinde ayrıdır. Resmî maç başına kanıt düzeyi
değişmiş sayılmaz.

## Lig bağlantıları; neyi kanıtlar, neyi kanıtlamaz?

Bu 132 aday maçın yerel ligler arası bağlantı grafiği
**dokuz ligi** birbirine bağlıyor:

BEL1, ENG1, ESP1, FRA1, GER1, ITA1, NED1, POR1, TUR1.

**ENG2 Championship: 0 UEFA lig aşaması maçı.**
Championship gücü için bu Avrupa veri setinden doğrudan
uluslararası katsayı üretmek mümkün değildir.

Maçlardan ölçülen örnek bağlantılar:
- Premier League – La Liga: **11** maç.
- Premier League – Bundesliga: **8** maç.
- La Liga – Ligue 1: **7** maç.
- Premier League – Süper Lig: **3** maç.
- La Liga – Süper Lig: **1** maç.

Grafiğin dokuz ligi bağlaması **9 ligin maç gücü doğru
ölçüldü demek değildir**. UEFA'ya seçilen kulüpler kendi
liglerinin tipik temsilcileri değildir (seçim yanlılığı).
Birçok ikili lig kombinasyonunda yalnız 1-3 maç var.
İngiltere orta sıra kulübünün Türkiye şampiyonuna göre
gücünü bu örneklemden bir ana katsayı olarak **doğrudan
tahmin edip onaylayamayız**. Takım ve lig etkisi ortak
modelde ayrı sınanmak zorunda.

## Durdurma koşulları ve güvenlik

1. Bu maçlar **kaynak + tarih + canonical üyelik için inceleme
   adaylarıdır**, UEFA sayısal takım-ID'siyle uçtan uca
   eşleştirilmiş onaylı model verisi değildir.
2. Yerel lig verilerinde 2025/26 maç günü öncesi
   takım hücum/savunma, ev-deplasman ve xG/xGA veri alanlarının
   **geçerli tarihte mevcut olduğuna** dair gerekli veri
   zaman kesiti kontrolü yapılmadı.
3. 2024/25 UEFA sezonunun yerel lig üyelikleri,
   2025/26 kaydından türetilemez.
4. Sakatlık/kadro/ilk 11, maçın önem derecesi, motivasyon
   gibi şeyler için rastgele gol çarpanı yok; eski ikili
   karşılaşma (H2H) özelliği oluşturulmadı.
5. M0/M1/M2 ligler arası matematik testi ve dış dönem
   kalibrasyonu henüz yapılmadı. Bu rapordaki tek
   test **veri kabulü** testidir.
6. Mevcut B/C2/C3/M4 dört model, 10 lig,
   Salı güncellemesi, 17 bölümlük rapor, kullanıcıdan
   gelen saatle ön analiz, T–60 ilk 11, A/B/C, pilot
   ve üretim `main` **DEĞİŞMEDİ**.

## Tek sıradaki teknik paket

**2025/26 maç-günü öncesi yerel güç girdileri + tarihsel
UEFA takım kimliği kanıtı + aynı dönem kalibrasyon örneklemi
uygunluk denetimi**. Bu üç eksik topluca hazırlanıp tek
uyumluluk raporunda değerlendirilecek. Geçmeyen alanların
nedenleri açıklanacak. Ancak yeterli gerçek veri olduğunda
önceden kararlaştırılmış **M0/M1/M2 ortak kronolojik
dış testini** tek seferde çalıştırmak mantıklı olur.

**Mühendislik kararı:** 2025/26 CL+EL 10 lig kapsamı
ENVANTERİ KAPANDI; model entegrasyon izni **YOK**.
