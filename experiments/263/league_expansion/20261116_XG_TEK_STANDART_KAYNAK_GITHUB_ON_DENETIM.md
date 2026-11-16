# 16 Kasım 2026 — Tek standartlı xG kaynağı: GitHub ön denetimi

## Kapsam ve değişmezler
- Bağlayıcı 15 Kasım 2026 kapsamı: 10 aktif analiz ligi (ENG1 ENG2 GER1 ESP1 ITA1 FRA1 NED1 TUR1 POR1 BEL1) + 12 yalnız araştırma/eğitim ligi (ENG3 ENG4 ENG5 GER2 ESP2 ITA2 FRA2 GRE1 AUT1 SCO1 CHE1 DNK1).
- Yalnız 2025/26 ve 2026/27 sezonları. Geçerli geçmiş maçların post-match xG değerleri yalnız sonraki maçlara ait pre-match öznitelikleri üretirken kullanılabilir.
- main, ana M4, B/C2/C3/M4, 96 mühürlü pilot, orijinal xG Excel'i ve elde girilmiş 151 kayıt değiştirilmeyecek.
- Bu doküman salt araştırmadır; otomatik veri çekme, içeri alma, model eğitimi, üretim değişikliği ya da yeni pilot yapılmadı.

## GitHub adaylarının doğrulanan sınırları
1. https://github.com/nlbair/openplay — CC-BY 4.0 veri; her şuta tek geliştirilmiş xG modeli uygulanıyor, 2025/26 var, **2026/27 yok**, kapsama büyük beş lig + UEFA ve bazı turnuvalar giriyor. 22 ligin tamamını çözmez.
2. https://github.com/v-eatpizzanot/soccer-dataset — yayınlanan 271 lig/673966 fikstür ifadesi xG kapsamı değildir. Yalnız 128746 fikstürde xG rapor edilmiş. Veri sözlüğü xG'nin şut alanlarına dayalı **kaba sağlayıcı tahmini** olduğunu, gerçek şut düzeyinde xG olmadığını açıkça belirtiyor. Eksik sıfırlar NULL'a çevrilmiş. Kalite raporu 2026-07-05 tarihli; 2026/27 oynanmış güncel xG'yi bu sayıdan çıkarsamayın. 22 lig × 2 sezon xG kesişimi doğrudan dosyalardan sayılmadı.
3. https://github.com/vncgrvs/football-data-mcp — ilk beş lig için Understat, diğerleri için SofaScore kullandığını bizzat yazıyor; **tek model standardı yok**, 2026/27 kapsamı gösterilmiyor.
4. https://github.com/Ryzellx/football-live-api — geniş FotMob tabanlı API kodu; sunulan genel lig listesi o liglerin iki sezonda da oynanmış maç başına xG'si bulunduğunu kanıtlamaz. Veri kullanım izni de sağlamaz.
5. https://github.com/oladeeayo/open-matchday — 2026/27 sezonunda 75 yarışma ve CSV sonuç/şut/kart verileri hedeflenmiş, ancak README açıkça **xG yok** diyor. Özellikle şut istatistiğinin yaklaşık %19 sonuç satırında olduğu yazıyor; tek standart gerçek xG kaynağı değildir.

## Veri hakkı uyarısı
- FotMob doğrudan soccerdata GitHub Issue #918'de (2026-01-22) izinsiz otomatik/sistematik erişime karşı çıkmış: https://github.com/probberechts/soccerdata/issues/918 .
- Açık kaynak istemci kodu, üçüncü tarafın tarihsel xG verisini topluca çekme hakkını otomatik vermez.

## Karar / gate
**Henüz GO değil:** İki sezon için tüm 22 ligde tek tanımlı gerçek şut bazlı xG, ücretsiz sürdürülebilir erişim, kaynak hakkı ve maç bazlı doğrulanmış tam kapsamı olan depo teyit edilemedi.

El girişlerini durdur; elde girilmiş 151 kayıt ve orijinal 1855 giriş çalışma kitabı korunur.

Bir sonraki araştırma:
A. 22 lig × 2 sezon için (oynanan/gerçek xG bulunan/eksik/sunumun hakkı/aynı xG modeli) satır bazlı kapsam matrisi ve kanıt URL'leri oluştur.
B. Tek gerçek xG kaynağı çıkmazsa, lisanslı ve yaygın erişimli şut olay verisi bulunup bulunmadığını test et. Bulunursa aynı algoritmayı bütün lig/maç şutlarına uygulayan araştırma xG üret; aksi halde sadece toplam şuttan üretilen proxy'ye 'gerçek xG' deme.
C. Gerçek xG ve tek standart mümkün değilse tüm 22 ligde xG'siz ortak as-of özelliklerle çalışmayı sürdür; xG'yi zorla doldurma. Mevcut Understat ve 151 el girdisini sakla; model eğitimine otomatik alma.
D. Gerekirse yalnız eski 96 SHA-mühürlü pilot + uygun tarihsel doğrulanmış kohort üzerinden tek önceden tanımlanmış eşit karşılaştırma; yeni pilot veya üretime sessiz geçiş yok.

## Doğrudan kaynaklar
- https://github.com/nlbair/openplay
- https://github.com/v-eatpizzanot/soccer-dataset
- https://github.com/v-eatpizzanot/soccer-dataset/blob/main/docs/data_dictionary.md
- https://github.com/vncgrvs/football-data-mcp
- https://github.com/Ryzellx/football-live-api
- https://github.com/oladeeayo/open-matchday
- https://github.com/probberechts/soccerdata/issues/918

**Çözümlenmemiş:** 22 lig × 2 sezon sayısal maç/xG tablosu yayınlanmış parquet kayıtlarından doğrudan doğrulanmadı. Toplam lig sayısını xG bulunan lig sayısı yerine kullanma.
