# 2.6.3 — 2025/26 UEFA Avrupa Ligi eksik sezon tamamlayıcı kaynak kabulu
## Tek paket ölçüm raporu — 2 Kasım 2026

**Çalışmanın amacı:** Önceden eksik olan 2025/26 UEFA EL 144 lig aşaması
maçını tarih/saha/skor bakımından kabul etmek; yalnız 10 yerel lig
kapsamımızdaki iki kulübün karşılaştığı geçmiş maçları ayırmak.
**Tahmin modeli veya ligler arası güç puanı üretilmedi.**

## Veri ve kaynaklar

- Eksik EL sezonu daha önce kullanılan
  `openfootball/champions-league` kaynak dondurmasında **bulunmuyor**.
- Tam sezonu veren, kamuya açık üçüncü taraf:
  https://fixturedownload.com/feed/json/europa-league-2025
- Resmî UEFA 29 Ocak 2026 lig aşaması sonuçları:
  https://www.uefa.com/uefaeuropaleague/news/029c-1e9b4e18c28e-3bb76afa22ac-1000--europa-league-league-phase-results-by-team/
- UEFA'nın 2025/26 turnuvaya katılan 36 kulüp listesi:
  https://www.uefa.com/uefaeuropaleague/news/0296-1d21e9c10031-f10e483164b3-1000--2025-26-europa-league-format-dates-draws-final/
- Braga adının resmî kulüp aynı kimlik eşleşmesi:
  UEFA 52336 https://www.uefa.com/uefaeuropaleague/history/clubs/52336--braga/
  ve resmî Portekiz Ligi 2025/26 https://www.ligaportugal.pt/team/285/sc-braga/20252026

## Gerçek GitHub kanıtı

- İlk kaynak/kimlik testi:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41478506406
- **Son kabul ve Braga düzeltmesi:**
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41478903767
- **10/10 yeni birim kontrolü PASS; veri indirme ve kapsam ayrıştırma başarılı.**
- SHA256 public feed `288f7410e0ef5bb5236408e2239d5351e8bcbfb21dc7f805e4f22dea267d3ae5`.
- GitHub Actions artefaktı:
  `263-el-2025-26-ten-leagues-scope-review`;
  `el_2025_26_source_acceptance.json` ve
  `el_2025_26_review_only_ten_leagues.json` içerir.
  Çıktılar **deney/inceleme amaçlıdır**, değişmez model eğitim girdisi
  olarak henüz kabul edilmedi.

## Ölçülen sayılar

| Kontrol | Sonuç |
| --- | ---: |
| 2025/26 UEFA EL lig aşaması tamamlanan maç | 144 |
| Toplam gol | 386 |
| Takım sayısı | 36 |
| Maç haftası | 8 x 18 |
| Resmî UEFA sonuç arşiviyle karşılaştırılan maç | 6 |
| 10 lig ve birebir isim adayı (ilk geçiş) | 32 |
| Resmî isim eşlemesiyle Braga kapsamına eklenen maç | 5 |
| **İki takım da 2025/26 10 ligde olan isim adayı** | **37** |
| **Kapsama girmediği veya isim tanınmadığı için elenen** | **107** |
| Bağımsız UEFA kulüp-ID'si tüm maçlar için doğrulanmış | Hayır |
| Üretim modeline onaylanan bu sezon karşılaşması | **0** |

**Not:** 107 dışarıda kalan maçı kullanıcı adına yeni ülke liglerine
ayrıntılı araştırarak dahil etmiyoruz. Eşleşmeyen kaynak adlarının
büyük kısmı zaten 10 lig dışında. Bunlar dış lig için yeni görev değil.

## Mühendislik kararı

Eksik 2025/26 EL veri kaynak açığı için **tarihli kaynak ve kapsama
göre seçilmiş 37 adaylı okuma hattı kuruldu**.

Fakat:
1. Bu **144 maçı resmî UEFA'ya karşı tek tek** henüz
   doğrulamadık; 6 sabit resmî çapa ve toplam turnuva/hafta
   sayıları uyuşuyor. Kaynak riski raporlandı.
2. 37 isim adayı, otomatik model eğitimi veya gerçek
   başarı kaydı değildir. Genel UEFA canonical-ID
   doğrulaması hâlâ eksik.
3. 2025/26 Champions League'deki mevcut 144 maçla bu 37
   adayın ortak 10 lig/tarih aralığında bağlanabilir
   olması ayrı bir aşama; verileri birleştirip sayı
   icat etmedik.
4. 2024/25 yerel lig tarihi/kimliği ayrı veri kapsama riski;
   2025/26 kayıtlarıyla 2024/25 maçına geriye dönük
   üyelik/yetki vermeyiz.
5. Böyle küçük örneklemde global güç katsayısı
   kalibre edildiği veya rakip motivasyon etkisi
   ispatlandığı iddia edilemez.

**Sıradaki tek teknik paket:** 2025/26 CL ve EL için
aynı sezonluk 10-lig gerçek veri/kimlik
kapsamını birlikte raporla; maç öncesi kronolojik
güç farkı girdileri yoksa eksik alanları tek raporda
kesinleştir. Yalnız veri kabulü tamamlandığında
önceden kararlaştırılan **M0/M1/M2 tek toplu dış-test**
kurulacak. B/C2/C3/M4 değiştirilmez.

**Değişmeyenler:** main, 10 lig haftalık güncellemesi,
mevcut dört matematik motoru, H2H çıkarma kararı,
kullanıcının saatine göre analiz, T–60 ilk 11,
A/B/C, pilot ve 100 maçlık süreç.
