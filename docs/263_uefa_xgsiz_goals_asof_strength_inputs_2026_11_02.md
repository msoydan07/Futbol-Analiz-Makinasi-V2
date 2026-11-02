# UEFA 2.6.3 — xG'siz ligler arası güç motoru için yeni veri hazırlığı

**2 Kasım 2026, yalnız deney dalı.** Kullanıcının kararı:
Avrupa Şampiyonlar Ligi / Avrupa Ligi maçlarında iki taraf
için de xG/xGA hiç araştırılmayacak; xG vekili de kurulmayacak.

## Önceki çalışmalara dokunmayan yeni girdi
- SHA-256 ile kilitli, daha önce kabul edilmiş 4.413 yerel
  lig sonuç arşivi (run 41251343847)
- Resmî UEFA maç sayfası bağlantılarıyla eşleştirilmiş
  2025/26 CL 95 + EL 37, toplam 132 **inceleme adayı**
  (run 41488522760).
- Mevcut 2025/26 10 lig takım kimliği indeksi.

Önceki 432, 288/132, 126/89/0, 47 kulüp, 132 maç ID
ve 12/12 xG'siz araştırma kontrolü **tekrar edilmez**.

## Yeni ölçülecek
132 UEFA maçının günü için yalnız **tarih olarak daha önce
tamamlanmış** yerel 2025/26 lig maçları kullanılarak:
- Takımın toplam / iç saha / deplasman maç sayısı
- Gerçekleşmiş atılan ve yenilen goller
- O güne kadar kendi liginin ev/deplasman gol ortalaması
- İki takımda 4+, 8+ maç, ayrı iç/deplasman
  en az 2'şer maç ve 30+ lig maçı kaynak kapsamı
- CSV'deki tarihsel yayın/kaynak sürümü zaman
  damgasının **doğrulanabilir** olup olmadığı.

Bu girdiler yalnız **veri hazırlık/sayı kontrolüdür**.
Bir ligin gol ortalamasını başka ülkenin aynı
seviyedeki takımıyla doğrudan karşılaştırmayız.
Ülke güç köprüsü ve rakip seçilim yanlılığı
çözülmeden Poisson gol λ, MS1/X/2, 2.5 Üst,
KG, EV veya A/B/C **üretilmeyecek**.

### Çok kritik gerçek veri sınırı
2026'da derlenmiş güncel sonuç CSV'sinin
`match_date` sütunuyla geleceği filtrelemek,
2025'teki UEFA maçından önce **aynı veri
dosyasının erişilebilir olduğunu göstermez**.
Arşivde orijinal `first-seen` / sürüm /
kaynak yayımlama damgası kanıtlı değilse
`as_of_real_time_proven=false` kalır.
Kronolojik retrospektif test ile gerçekten
maçtan önce kilitlenmiş canlı pilot aynı şey
değildir. Geçmiş testler kanıt diye sunulmaz.

**Aşama kabulü:** Yeni tek CI gerçek veri kapsamı
sayısını ve eksik kaynak zaman kanıtını tek
raporda ortaya çıkarır. **Tahmin modeli hâlâ
uygunluk onayına tabi**, üretim `main`
ve 10 lig yerel hattı hiç değişmez.
