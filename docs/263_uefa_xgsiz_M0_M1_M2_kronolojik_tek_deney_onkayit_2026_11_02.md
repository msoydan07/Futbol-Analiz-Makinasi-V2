# 2.6.3 xG'siz Avrupa ligler arası güç karşılaştırması — ön kayıt

**Tarih:** 2 Kasım 2026. **Nitelik:** Salt okunur, sabitlenmiş
deney protokolü. **Bu dosya model eğitimi veya tahmin sonucu değildir.**

## Döngü kontrolü / girdi

Önceden kabul edilmiş 132 UEFA maç numarası kimliği (41488522760)
ve 132 maçın xG'siz iç/deplasman yerel gol geçmişi (41493071435)
**yeniden hesaplanmaz**, GitHub artefaktlarından okunur.
4.413 maçlık veri arşivi, 288/132 taraması, 432 maç
taktik regresyonu veya xG yokluğu testi tekrarlanmaz.

## Sabit kronolojik tarih parçaları

- **Eğitim:** Eylül–Kasım 2025, **84** maç (CL 60 / EL 24).
- **Doğrulama:** Aralık 2025, **16** maç (CL 12 / EL 4).
- **Ayırılmış son bölüm:** Ocak 2026, **32** maç (CL 23 / EL 9).

Aynı takvim günündeki tüm maçlar aynı parçaya düşer.
**132** ham örnek, **124** ise 2 takımın kendi liginde
en az 4 önceki lig maçı; her biri için en az 2 iç ve 2
deplasman maçı ve her iki ligde en az 30 önceki sezon
maçı olan **girdi bakımından yapısal aday**.
124'ün parçalar arasındaki dağılımı bir defalık
ön-kayıt kontrolünde sayılacak. 124'lük filtre hem
M0, hem M1, hem M2 için *aynı maç-ID listesi* olacak.
M2 ek girdileri eksikse üçlü karşılaştırma
farklı örneklemde ve sessizce yapılmayacak.

### Modeller, tek plan ve bağlayıcı kısıtlar

**M0 (kontrol):** Aynı sezondaki önceki gerçek yerel
lig gol ve yenilen golleri, ülke ligi ev/deplasman
ortalamalarına göre ölçeklenmiş, gol sayısı için
daha önce kararlaştırılan `k=5` yumuşatma referansı
ve UEFA eğitim maçlarından tek ortak başlangıç
ortalamalı Poisson. Farklı liglerin eşit güce
sahip olduğu **doğrulanmış** sayılmaz; bu bilerek
naif karşılaştırma koludur.

**M1:** M0 + maç öncesinde gözlenmiş UEFA
sonuçlarından ülkeler arası kısmi havuzlanmış
güç farklılığı. Sabit `ridge=20` ve ligi
sıfır toplam merkezlemeyle, saha etkisini
ayrı öğrenme. Avrupa'ya seçilen takımların
ülke temsilcisi olma yanlılığı açıkça raporlanır;
kapalı/sadece tek maçtan bağlı güç grafiği
varsa katsayı tahmini yerine **BLOKE** kararı.

**M2:** M1 + daha önce oynanmış UEFA maçlarına
dayalı rakibe göre önceki puan/maç, gol yeme
ve önceden bilinen rakip güç farkı;
aynı gün, aynı hafta sonuçları, H2H veya
tahmini motivasyon katsayısı YASAK.
İlgili takım için önceki UEFA verisi
gerçekten yoksa sıfır güç/puan uydurulmaz.
Sabit ek `ridge=20`; doğrulama veya son
testten katsayı seçilmez.

**Üç kol için xG/xGA/xG vekili YOK.**
Poisson λ, yalnız gol geçmişine göre
geliştirilen bir matematik tahminidir, xG değildir.

## Ölçütler ve karar

**Birincil:** aynı maçlarda 1X2 log-loss.
**İkincil:** 1X2 Brier, toplam gol Poisson
log-loss, 2.5 Üst Brier, kalibrasyon ve
turnuva bazlı kırılım; KG yalnız destekleyici.
Tüm karşılaştırma maçları eşleşmiş; kullanıcı
tarafından kabul edilmeden risk/EV/kupon yok.
Tarih-blok bootstrap ve 32 maçlık tek-sezon
son bölümünün yetersizliği raporda gösterilecek.

**Çok kritik:** 2025/26 sonuçları bugün artık
biliniyor. Veri kaynaklarında özgün ilk
yayın anı damgası da yok. Bu nedenle
`RETROSPEKTIF_WALK_FORWARD_NO_LIVE_PREGAME_PROOF`
etiketi zorunlu. İster iyi ister kötü sonuç
çıksın, aynı sezonun 32 maçı **yeni sezon bağımsız
kanıtı** veya canlı 100 maçlık pilot değildir.
Otomatik model terfisi **daima yasak**.

**Bu aşamanın bitiş ölçütü:** Tek GitHub koşusu,
geçmiş iki artefaktın salt okunur tutarlılık
testi, sabit tarih sayıları ve yapısal veri
uygunluğu; **henüz gerçek M0/M1/M2 eğitimi
ve tahmin yüzdesi yok.** Kod, veri hattı ve
`main` üzerinde yaşayan motorlara dokunma.
