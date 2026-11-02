# UEFA 2.6.3 — yeni xG'siz M0 vs M1 retrospektif tek toplu karşılaştırma ÖN KAYDI

**2 Kasım 2026 — henüz gol olasılıkları çalıştırılmadı.**
Eski M0/M1/M2 üçlü protokolü, 2025/26 kaynağında
M2 için 93/124 eksik önceki UEFA maçı ve
10 ligden Championship'in bulunmaması nedeniyle
**veri önkoşulu aşamasında bloke edildi**. Bu yeni
doküman eski başarılı/başarısız deneyi silmez.
Yeni seçenek üçlü çalışmanın yerine **sessizce geçmez**.

## Dondurulmuş veri, kapsam ve bölünme

- 2025/26 resmî UEFA kimlikli 132 aday, salt-okunur
  124 eşit gol-verisi uygunluğu; yalnız
  dokuz temsili UEFA yerel ligine uygun maçlar.
- Eğitim Sep–Kas 2025 **76**; doğrulama Aralık 2025 **16**;
  ayrılmış son kontrol Ocak 2026 **32**.
- Aynı maç/kup/kronoloji seçimi M0 ve M1 için birebir.
- UEFA 10-lig kapsam kapısı **korunur**, ancak
  mevcut dokuz ülkelik model başka ligin takımına
  sıfır/kendi kendine uydurulan gücü atamaz.
- Yalnız maçın hedef takvim gününden **önce**
  gerçekleşen lig sonuçları girdi. Aynı gün
  ve sonrası sonuçlarından özellik, takım ratingi
  veya katsayı üretmek yasaktır.
- 2025/26 sonuçları sonradan toplu derlenmiştir;
  canlı kaynak yayımlanma/ilk görülme anı kanıtı
  henüz yok. Retrospektif sonuç, gerçek zamanlı
  maç öncesi performans kanıtı değildir.

## Baştan sabitlenecek iki ayrı hesap

**M0 – aynı ölçek varsayımı naif kontrol:**
- Her takım için hedef maç gününden önce kendi
  yerel ligindeki iç saha/deplasman gol for/against.
- Aynı ligin ev/deplasman gol ortalamasına göre
  boyutsuz hücum ve savunma göreli oranları.
- Gözlenen kulüp/konum maç sayısında `k=5`
  yumuşatma; tüm normalizasyonlar yalnız hedef
  tarihinden önceki lig sonuçlarıyla.
- İki UEFA gol oranını birleştirmek için yalnız
  **Eylül–Kasım eğitim** maçlarının ev/deplasman
  gol ortalamaları. Rakip lig eşitliği
  doğrulanmış kabul edilmez; M0 yalnız
  yetersiz bir karşılaştırma kontrolüdür.
- İki bağımsız Poisson λ (ev/deplasman)
  üretilecek; her λ başlangıçtan önce
  belirlenen sabit [0,15; 5,00] aralığında
  sınırlandırılacak. Katsayılar sonuçlara
  bakılarak sonradan ayarlanmayacak.

**M1 – M0 + UEFA eğitim maçlarından lig gücü:**
- Yalnız 76 eğitim maçındaki gerçek UEFA
  skorları, lig karşılaşma bağlantı ağını
  oluşturacak; her turnuvanın veri kapsamına
  giren başka liglerdeki maçları AYRICA araştırma YOK.
- Sabit `ridge=20` ile takımın 9 yerel
  ligine kısmi havuzlanmış fark puanı;
  ağırlıklı ortalama sıfır; ev/deplasman
  ortak temel UEFA gol ortalamaları M0 ile
  aynı ve eğitim dışı skorlar hiçbir zaman
  katsayıya katılmayacak.
- Poisson hızları:
  `λ_home(M1)=λ_home(M0)·exp(rating_home_league-rating_away_league)`
  `λ_away(M1)=λ_away(M0)·exp(rating_away_league-rating_home_league)`.
  Üstel katsayıya sonuçtan sonra yeni çarpan
  veya görev dışı motivasyon eklenmez.
- Kestirimde yıl sonu takım sıralaması, gerçek
  son skor, açıklanmamış ilk 11, xG/xGA,
  xG vekili, H2H, lig dışı başka kulübün
  ülke maçları YOK.
- ENG2/Championship için rating tahmin
  edilmeyecek. Böyle bir takım varsa skor
  tahmini verilmez; eşit güç varsayılmaz.
- UEFA'ya seçilmiş takımların ülke
  temsilcisi yanlılığı ve TUR1'in 5
  cross-league eğitim maçından doğan
  belirsizliği raporda açıklanacak.

## Tek çalıştırmada karşılaştırılacak ölçüler

- **Birincil:** aynı 16 doğrulama ve 32 Ocak
  karşılaşması üzerinde 1X2 ortalama log-loss.
- **İkincil:** 1X2 Brier, toplam gol
  Poisson log-loss, 2.5 Alt/Üst Brier,
  KG Brier, kalibrasyon, CL ve EL
  ayrımları, tarih blok örneklem belirsizliği.
- Kod iki modele de **aynı 124 maç ID** ve
  aynı tarihli yerel özellik kesitini kullanacak;
  eğitim için 76, doğrulama 16, holdout 32.
- M0/M1 katsayıları eğitimde bir kez dondurulacak;
  Aralık verisiyle ayar/penalty seçimi yok.
  Ocak sonuçları eğitim veya değişiklik için
  kullanılamaz. Bütün skorlar doğru
  hesaplanana kadar 1X2 ve 2.5 sonuçları
  gerçek gözlenen tahminmiş gibi sunulmaz.
- Bu 32 maç **ayrı gelecek sezon/bağımsız
  yeni gerçek maç** değildir. İstatistik
  iyileşme, üretime geçiş kanıtı değildir.
  Tekrarlayan backtest/p-hacking yasak.

**Kesin karar:** Deney tek kez, iki model
birlikte, aynı kilitli parçalarla,
tek mühendislik raporunda değerlendirilecek.
Başarısızsa model kapatılır. Başarılı
olsa bile gerçek maç öncesi kilitli
prospektif pilot ve ayrı güvenilir kaynak
kanıtı olmadan `main`, A/B/C, EV
ve gerçek yüzde tahmini yetkisi YOK.
