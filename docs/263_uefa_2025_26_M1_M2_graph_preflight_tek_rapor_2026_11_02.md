# Futbol Maç Analiz Makinası 2.6.3 — UEFA xG'siz M1/M2 yeni önkoşul sonucu

**Tarih:** 2 Kasım 2026.
**Tek yeni iş:** 76 uygun eğitim karşılaşmasının farklı ligleri bağlama grafiği ve 124 maçın önceki UEFA karşılaşma geçmişinin tamamlanmışlığı. **Model çalıştırılmadı.**

### Girdi ve test kanıtı

- Önceden tamamlanan 132 resmî UEFA maç numarası: run 41488522760.
- Önceden hazırlanmış xG'siz 132 gol girdisi: run 41493071435.
- 84/16/32, uygun 76/16/32 tarihli deney ön kaydı: run 41494401386.
- **Bu aşamanın yalnız yeni çalışması:** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41494951687
- **5/5 yeni odaklı kontrol başarılı**, önceki 432/288/132/124 maç deneyleri tekrar çalıştırılmadı.
- Çıktı: `263-uefa-xg-free-M1-graph-M2-prior-feasibility`, `graph_and_M2_readiness.json` ve `132_prior_UEFA_visibility_REVIEW_ONLY.json`.

### Ölçülen M1 ligler arası bağlantı ağı

- 76 yapısal uygun eğitim maçının **76'sı farklı ülke ligi** ekipleri arasında.
- 9 gerçek UEFA katılımcı ligi ağda temsil edildi:
  `BEL1, ENG1, ESP1, FRA1, GER1, ITA1, NED1, POR1, TUR1`.
- **32 farklı lig çifti** arasında maç; bu dokuz lig **tek bağlı bileşen**.
- `ENG2` / Championship 2025/26'daki bu 132 UEFA adayında görünmedi.
  Bu nedenle 10 ligin **tamamına** kalibre edilmiş bir güç skalası
  üretildiği iddiası YASAK. Mevcut 10-lig kapsam kapısı **aynen korunur**.
  Gelecekte Championship takımının UEFA maçında bu deney sonucu
  yalnız başına tahmin yetkisi VERMEZ.
- Eğitimde ligler arası maç sayıları: `ENG1=26, ESP1=23,
  GER1=21, FRA1=20, NED1=17, ITA1=15, POR1=13, BEL1=12, TUR1=5`.
  TUR1 ve bazı ülke çiftleri çok az tekrar edilmiş. Bağlı ağ,
  iyi kalibre şampiyonluk/gol gücü, örneklem yeterliliği veya
  seçim yanlılığı düzeltmesinin kanıtı DEĞİLDİR.

### M2 geçmiş UEFA maçları için gerçek kapsam

| Bölüm | xG'siz gol girdisi uygun | Her iki takımın tüm önceki UEFA maçları 132'de mevcut | Eksik geçmiş |
|---|---:|---:|---:|
| Eğitim | 76 | 28 | **48** |
| Doğrulama | 16 | 1 | **15** |
| Son değerlendirme | 32 | 2 | **30** |
| **Toplam** | **124** | **31** | **93** |

Kapsam dışı rakiplerin sonuçlarını kullanıcının açık
**sadece 10 lig kapsamı** kararını delerek toplamıyoruz.
Kapsam içinde olmayan UEFA geçmiş maçlar `0 puan`,
`0 gol`, zayıf rakip veya eksiksiz ilk tur olarak
uydurulmaz. M2'yi tüm 124 üzerinde eksiksiz 2025/26
önceki UEFA puan/gol/rakip özellikleriyle kurmak
bu veriyle **mümkün değil**.

### Mühendislik kararı (önceden gördüğümüz sonuçların ışığında ama model sonuçlarına bakılmadan)

1. Dondurulmuş **M0/M1/M2 üçlü** deney planı
   **veri önkoşulunda bloke edildi**; üçlü gerçek
   test yapılmadı, farklı maçlarda kıyaslanmadı.
   Dondurulmuş ön kayıt silinmez veya sonuçlarına
   göre yeniden adlandırılmaz.
2. **Yeni alternatif:** sadece tarihsel UEFA katılımcısı
   dokuz lig ve kapsama uygun aynı 124 maç için
   **M0/M1 ikili RETROSPEKTİF keşif kıyası**.
   Bu, üçlü deneye eşit başarı kanıtı değildir.
   Karşılaştırma sonuçlarını görmeden
   `docs/263_uefa_2025_26_M0_M1_sadece_9_temsil_lig_onkayit.md`
   dosyasında ön kayıt ayrı sabitlenir.
3. **M2 iptal/defer:** veri eksikliği gidermek adına
   dış lig araştırması başlatılmaz. Başarısız
   üçlü deney sonuçları uydurulmaz.
4. 2025/26 tek sezonun tarihsel yayın zamanı
   `first_seen` verisi yok; zaman sırasına göre
   sonuç kullanan geriye dönük analiz **canlı maç öncesi
   bağımsız doğrulama** yerine geçmez. 32 maçlık
   Ocak son bölümü dış sezon değildir.
5. M0/M1'den biri diğerini geçse bile
   **ana motor entegrasyonu, gerçek maç tahmini,
   A/B/C, EV ve 100 maçlık pilot onayı yok**.
   Bu alanlarda ancak yeni tarihli, kilitli,
   gerçekten maç öncesi kanıt gereklidir.

**Döngü sonucu:** 9-lig bağlı ağı ve 93 eksik
geçmişli M2 engeli bir defada ölçüldü. Önceki
kapsam ve xG testlerine geri dönüş YOK.
