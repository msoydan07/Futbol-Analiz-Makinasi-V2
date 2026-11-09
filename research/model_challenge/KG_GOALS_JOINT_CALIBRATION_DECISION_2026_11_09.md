# M4 KG / ALT–ÜST KALİBRASYONU — TOPLU SONUÇ (9 Kasım 2026)

## Kaynak, ayar ve ayrım
- Kaynak: SHA kontrolünden geçen, sahibi tarafından **sınırlı araştırma amaçlı kabul edilmiş** 4.518 maçlık 2.6.3 geçmiş sonuç arşivi.
- 2026/27 Ağustos–Eylül **587** maçta geliştirme ve sabit ağırlık seçimi.
- 2026/27 Ekim–3 Kasım **397** ortak maçta değerlendirme; **1** kapsam dışı M4 tahmini.
- M4'ün orijinal kilitli matematik modeli değiştirilmedi.
- Her maç için önceden bilinen, hafta başından önce bitmiş sonuçlarla lig skor dağılımı oluşturuldu.
- Ortak skor dağılımı: **%80 M4 + %20 önceki lig skor dağılımı**. Her iki kaynak da geçerli tam skor dağılımı olduğundan KG, Alt/Üst ve MS pazarları bütünlüklerini korur.
- Ekim–Kasım dönemi önceki araştırmalarda **görülmüştür**. Bu test yeni bağımsız ileri deney değildir.

## İlk alternatif: Basit tam skor dağılımı birleşimi

| Pazar | M4 Brier | Aday Brier |
|---|---:|---:|
| KG Var/Yok | .249457 | **.247631** |
| 1.5 Alt/Üst | .163571 | **.161784** |
| 2.5 Alt/Üst | .250775 | **.247593** |
| 3.5 Alt/Üst | .241618 | **.238525** |
| MS 1X2 çok sınıflı | **.575728** | .578627 |

Gol pazarlarının dördü de iyileşti; **MS kötüleşti**. Bu nedenle tek başına mevcut 2.6.3'e terfi edemez.

## İkinci matematiksel prototip: MS 1X2 sabit tutulan skor dağılımı

İlk gözlemden **sonra** tasarlanan bu alternatifte, %80–%20 birleşimi yapılır,
ardından toplam skor matrisi içindeki **ev galibiyeti, beraberlik ve deplasman
galibiyeti kümeleri**, her birinin toplam olasılığı orijinal M4 ile
**birebir aynı** kalacak şekilde yeniden ölçeklenir.

Bu yöntem KG ve Üst dağılımını ayarlarken orijinal M4'ün MS olasılıklarını
değiştirmeyi matematiksel olarak engeller.

| Pazar | M4 Brier | MS-korumalı aday Brier |
|---|---:|---:|
| KG Var/Yok | .249457 | **.247904** |
| 1.5 Alt/Üst | .163571 | **.161639** |
| 2.5 Alt/Üst | .250775 | **.247707** |
| 3.5 Alt/Üst | .241618 | **.238542** |
| MS 1X2 çok sınıflı | .575728 | **.575728 (AYNEN)** |

Bu ikinci yöntem **daha sonra, test sonuçları zaten bilinirken**
formüle edildi; bu yüzden aynı 397 maçtaki kazanımı ne kadar iyi
olursa olsun yeni, kör bağımsız test sonucu sayılamaz. Matematik
birlikte hesaplandığında p(Üst1.5) >= p(Üst2.5) >= p(Üst3.5),
p(MS1)+p(MSX)+p(MS2)=1 garantileri korunmaktadır.

## Gerçek hafta sonu kayıtlarının durumu
GitHub'ın mevcut araştırma ve deney dallarında:
- **44** SHA-tutarlı maç önü tahmini: 6 Kasım **4** ve 8 Kasım **40**.
- Resmî postmatch attestation dizininde **0** sonuç dosyası.
- Yeni 2026/27 üçüncü taraf skor CSV'siyle takım kimliği+lig+tarih
  eşleştirme denemesinde **0/44** kayıt tam eşleşti. Bu, skor yok
  anlamına gelmez; otomatik skor bağlamak için yeterli kimlik
  kanıtı bulunamadığı anlamına gelir.
- 7 Kasım için ayrıca kullanıcının ChatGPT Library dosyalarında
  **44 maçlık araştırma JSON'u** ve **43 tamamlanan maçlık sonuç
  denetimi** bulunuyor; 1 maç ertelenmiş. Bunlar resmî yeni100
  pilot mühürleri değildir.
- 7 Kasım'daki **43** maça aynı %20 basit kalibrasyon uygulandı:
  KG Brier .233973 → .234002 (**neredeyse aynı, hafif kötü**);
  Üst1.5 .230620 → .226547; Üst2.5 .241176 → .239342;
  Üst3.5 .177833 → .174892. Sonuç raporu daha önce
  skorlar incelenerek hazırlanmış, bağımsız ağ kaynağıyla yeniden
  teyit edilmemiştir. Bu ölçümler keşifsel kanıttır.
- Kullanıcının tarif ettiği 95 maçlık toplam *96 sabit aday eksi
  ertelenen bir maç* bağlamıyla tutarlıdır; ancak **95 ayrı,
  değiştirilemez maç öncesi tahmin + 95 resmî tam zaman
  skor kaydının varlığı kanıtlanmamıştır**. Aday, hesaplanmış
  araştırma tahmini ve resmî mühür ayrı kategorilerdir.

## Mühendislik kararı
**Yeni adayları araştırma dalında sakla, mevcut üretim M4'e DOKUNMA.**
MS-korumalı ortak skor kalibrasyonu gelecek gerçek pre-match
mühürlü karşılaştırma için en mantıklı araştırma adayıdır.

Gelecekte yeni veriyle bağımsız sonuç alınmadan yöntemi
2.6.3'ün KG ve Alt/Üst yüzdelerine kalıcı olarak entegre etme.
Var olan MS 1X2 ve piyasa karar motoruna otomatik terfi YOK.

## Teknik kanıt
- İlk ve MS-korumalı adayın toplu CI:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42576956120
- Matematiksel invariants ve normalizasyon:
  `research/model_challenge/test_joint_score_calibration_263.py`
- Weekend seal + sonuç varlığı denetimi:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42575672034
- Harici skor eşleşmesi neden engelli:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42576638887
- Toplu kaynak: `data/quad_accepted_263/extended_history.csv`,
  4.518 maç kabul edili araştırma SHA'sı.
- Üretim, mühürlü tahminler, fiyat kayıtları ve asıl geçmiş skorlar: değişmedi.
