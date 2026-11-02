# 2.6.3 — Avrupa Kupaları Güç Köprüsü / Aşama 1 Sonuç Raporu

**Tarih:** 2 Kasım 2026. **Durum:** Kaynak ve kimlik denetimi başarılı; güç modeli henüz kabul edilmedi.

## Kanıt

- GitHub Actions başarılı koşu: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41465698307
- Yeni güvenlik testleri: 7/7 PASS.
- Artefakt: `263-uefa-strength-bridge-source-identity-review`
  - `source_coverage_263.json`
  - `uefa_club_identity_REVIEW_ONLY.csv`
- Kaynak: openfootball/champions-league, commit
  `abfaeddc2ee3d14f99ecc163c9ddb46cb4d67cef`
  (önceki 432 maçlık çalışmayla aynı sabit tarihsel kaynak).
- Kullanılan read-only takım kimlik kaynağı:
  `experiments/263/evidence/identity_index_263.json`;
  mevcut 10 lig, 2025/26 ve 2026/27 kayıtları.

## Sayısal veriler

| Kalem | Denetim sonucu |
|---|---:|
| Şampiyonlar Ligi 2024/25 lig aşaması | 144 maç / 470 gol |
| Avrupa Ligi 2024/25 lig aşaması | 144 maç / 408 gol |
| Şampiyonlar Ligi 2025/26 lig aşaması | 144 maç / 487 gol |
| **Toplam** | **432 maç / 864 kulüp-maç tarafı** |
| Farklı UEFA kulüp + ülke kaynak etiketleri | **86** |
| Mevcut yerel takım isimleriyle birebir eşleşme *adayları* | **26** |
| Birebir isim eşleşmesi olmadığı için ayrıca incelenecek etiket | **60** |
| Mevcut takımlara iki taraflı birebir isim eşleşmesi adayı bulunan 2024/25 CL maçı | **6 / 144** |
| Mevcut takımlara iki taraflı birebir isim eşleşmesi adayı bulunan 2024/25 EL maçı | **20 / 144** |
| Mevcut takımlara iki taraflı birebir isim eşleşmesi adayı bulunan 2025/26 CL maçı | **9 / 144** |
| **Model için onaylanmış UEFA kulüp eşleştirmesi** | **0** |
| **Model için onaylanmış UEFA maçı** | **0** |

**Yorum:** 60 etiketin bir kısmı 10 yerel lig dışında kalan
kulüplerdir; başka kısmı ise UEFA adlarının canonical takım
adlarından farklı yazılmasıyla oluşmuştur. 'Birebir eşleşme'
onaylanmış kulüp kimliği değildir. 2024/25 UEFA verisini 2025/26
yerel lig üyeliğiymiş gibi kullanmak yasak.

Bu sonuç gerçek yeni tahmin başarısını veya küresel Elo'nun
kurulduğunu **göstermez**.

## Bulunan yapısal eksikler

1. Avrupa UEFA kulüp kimlikleriyle canonical yerel takım ID'leri
   arasında kaynak kanıtlı eşleme henüz yok.
2. Mevcut kimlik indeksinde 2024/25 yerel lig geçmiş üyeliği
   ve bu UEFA sezonundaki bütün kulüpler yok.
3. 2025/26 Europa League lig aşaması bu üçlü kaynak setinde
   bulunmuyor; bu turnuvaya özel dış sezon testi yapılamıyor.
4. 2026/27 güncel UEFA CL/EL geçmişi bu çalışmaya dahil
   edilmedi; Salı 10 lig güncellemesi UEFA güncellemesi değildir.
5. Resmî UEFA maç sayfası bazında 432 satır bağımsız doğrulanmış
   değildir. Kaynak toplamlarının resmî turnuva toplamlarıyla
   uyuşması tek tek maç kanıtı anlamına gelmez.
6. Rakiplerin ülkeler arası güçleri için güvenilir, maç öncesi
   tarihsel derecelendirme veya bağlantılı kulüp güç geçmişi
   henüz hesaplanmamıştır. Yerel lig sıraları doğrudan
   kıyaslanamaz.

## Bir sonraki tek çalışma paketi

**Kaynaklı UEFA club-ID eşlemesi + yerel sezon verisi
zaman kapsamı + 2025/26 EL veri boşluğu.**

- Önce 60 eşleşmeyen etiketi ve 26 aday etiketi, *öncelikli
  döneme ilişkin kaynak kanıtıyla*, lig kapsamı
  içinde/dışında diye gruplandır.
- 2024/25 ve 2025/26 için ligler arası güç modeli kurulacaksa,
  kulüp üyeliğinin ilgili yıldaki doğruluğunu doğrula.
- Karşılaşma verilerinde **iki takımdan biri yerel 10
  lig dışında** olsa dahi onu yanlış canonical ID'ye
  eşleme; gerekiyorsa ayrı UEFA-only kimlik.
- UEFA maç geçmişini ve mevcut takım isimlerini kaynak
  ve tarih bazında doğrula, sonra ancak geçmiş gücü eğit.
- Eksikler kapanmadan M0/M1/M2 kıyasına geçme;
  ilk 432 gol-hafta deneyini tekrar etme.
- Rakibe göre performans / motivasyon için keyfî katsayı
  veya geçmiş H2H özelliği üretme.

## Değişmez kurallar

Üretim `main`, 10 yerel lig, Salı 10:37 TSİ güncellemesi,
B/C2/C3/M4, A/B/C, canlı oranlar ve 100 maçlık pilot
değişmedi. GitHub işi yalnız
`experiment/263-toplu-karsilastirma` dalında yapıldı.

**Mühendislik kararı:** Aşama 1 veri/kimlik envanteri
tamam; model uygunluğu ONAYLANMADI.
