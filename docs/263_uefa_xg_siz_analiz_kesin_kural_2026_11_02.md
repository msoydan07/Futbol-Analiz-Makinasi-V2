# Futbol Maç Analiz Makinası 2.6.3 — UEFA CL/EL için xG kullanmama kararı

**Kullanıcı kararı: 2 Kasım 2026. DURUM: AVRUPA ANALİZİ İÇİN KESİN VERİ POLİTİKASI.**

## Kapsam

UEFA Şampiyonlar Ligi ve Avrupa Ligi'ndeki, **iki tarafı da mevcut
10 yerel ligde oynayan** kullanıcı tarafından seçilmiş maçlar için
**xG/xGA KULLANILMAYACAK**. xG bulunan lig ve kulüp için de xG araması
yapılmayacak. Bir tarafın xG verisi varken diğerinde yoksa tek taraflı
matematiksel ayrıcalık doğmayacak. Suni tahmini xG üretmeyeceğiz:
şut bazlı vekil xG, oran kaynaklı vekil xG veya sezonsal ortalamadan
türetilmiş xG bu yeni karar kapsamında yasak.

Kapsam dışı takımın başka ülke ligine ilişkin hiçbir araştırma açılmaz.
İsimleri Maçkolik biçiminde gelebilir. Kullanıcının verdiği maç
saati veri araştırmasını başlatır; T–60 ilk 11 ayrı kaynakla doğrulanır,
eksik ilk 11 tüm analizi durdurmaz.

## Kullanılabilecek ve geçmişte araştırılacak girdiler

- Gerçekleşmiş ev/deplasman gol ve yenilen gol istatistikleri.
- Takımın kendi lig ortalamasına göre normalize edilmiş hücum ve
  savunma sonuçları; rakip güç farklılıkları ve ligler arası ortak
  ölçek **ayrı, kronolojik karşılaştırmalı deneyle kanıtlanmadan
  kesin skor veya yüzdeye dönüştürülmez**.
- Son maç sonuçları ve örneklem/belirsizlik, mevcut ve geçmiş
  rakiplerin gücü; rakibe karşı UEFA puan durumu/bağlamı ancak
  kaynaklı ve maç öncesinde bilinebilir ise.
- Gerekiyorsa ve iki taraf için tutarlıysa gerçek şut/isabet,
  sakatlık, cezalı, ilk 11, dinlenme, saha avantajı ve
  kaynaklı oranlar. Her veri bağımsız doğrulama şartını korur.

`xG var mı?` sorusu UEFA araştırma hattında açılmaz ve analiz
raporunda `xG doğrulanamadı` bir veri kusuru gibi sunulmaz.
Arşivde daha önce ölçülmüş **0/132 xG uygunluğu** tarihsel
denetim sonucu olarak kalır; tekrar aranmaz veya test edilmez.

**Önemli matematik ayrımı:** Poisson modelinin tahmin ettiği
gol ortalaması **λ**, üçüncü tarafın geçmiş maçlara atadığı
**xG ölçümü değildir**. λ gelecekte sadece gerçekleşmiş
gol/yenilen gol, lig normalizasyonu, rakip güç
ve ev/deplasman gibi **xG'siz** verilerden öğrenilirse
kullanılabilir; yine de model uygunluğu otomatik
kanıtlanmış sayılmaz.

**M0/M1/M2 karşılaştırma yapısı** daha önce dondurulduğu gibi
aynı maçlarda, aynı tarih aralığında, maç öncesi
zaman kaçağı olmadan, 1X2 Brier/logloss ve gol piyasaları
üzerinden korunur; xG kullanan hiçbir deney kolu
karşılaştırmaya dahil edilmez. Tarihsel erişilebilirlik
ve dış test kanıtı eksikleri halen geçerlidir.
Hiçbir yeni tahmin modeli veya λ burada kurulmadı.

## Kod düzeyi politika

`experiments/263/europe/uefa_no_xg_contract_263.py`
kullanıcı maçı giriş kapısını çağıran **yeni Avrupa'ya
özgü standart araştırma sözleşmesidir**. Kolektöre
yalnız izinli kaynak alanlarını iletir ve dönen
yapıda xG, xGA, npxG, PSxG, expected_goals vb.
anahtarları fail-closed reddeder. Bu kod gerçek
web kaynaklarını fetch etmez: kolektörün içerik
sağlayıcısına doğru ve gerçek erişimi ayrı
denetlenmelidir. Başka kod yolunun bu sözleşmeyi
atlamadığını ileri sürmeyiz; canlı stat-fetch
adaptörüne entegrasyon gerektiğinde yine
ayrı test gerekecektir.

**10 yerel lig için var olan yerli xG stratejisi
ve deney motorları B/C2/C3/M4 bu Avrupa kararının
kapsamı dışında ve değiştirilmedi.** Kullanıcı
tüm yerel lig sisteminde xG'yi ayrıca kaldırmak
isterse ayrı kapsam kararı gerekir.

**Geçmişi koru:** 432 maçlık taktik deney,
288/132 UEFA kaynak kapsam testi, 126/89/0
veri uygunluk testi, 47 kulüp/132 maç kimlik testleri
**tekrarlanmadı**. main, pilot, A/B/C, bahis,
takım kimlikleri veya veri CSV dosyaları
değiştirilmedi.
