# Eksik veri kaynak araştırması — 2026-10-31

## Mevcut durum
- 10 lig / iki sezon: 4.413 doğrulanmış bitmiş maç.
- Understat 5 ligde 2.100 kesin eşleşmiş xG; 61 Understat kaydı eşleşmemiş.
- Diğer 5 lig (ENG2, NED1, TUR1, POR1, BEL1) için maç bazlı xG henüz doğrulanmadı.
- İlk yarı kornerleri kullanıcı kararıyla 2.6.2 kapsamından çıkarıldı; eksik veri hedefi değildir.
- ITA1 2026-27 satır 91: hatalı deplasman şut ikilisi karantinada; maç silinmez.

## Kaynak adayları (bulunabilirlik, veri doğruluğu ve lisans henüz ayrı ayrı doğrulanmalı)

1. **open-matchday** https://github.com/oladeeayo/open-matchday
   - Önceki araştırma ilk yarı korner içindi; artık kapsam dışı olduğu için bu kaynak için geliştirme yapılmayacak.
   - Bu kaynak mevcut veri planında aktif aday değildir.
   - Geçmiş araştırma notu olarak saklanır.
2. **OpenFoot API** https://openfootapi.com/docs
   - Dokümantasyonda Eredivisie, Primeira Liga, Süper Lig, Belçika Pro League ve maç xG/shot-map özellikleri tanıtılıyor.
   - Bu liglerde *gerçek maç bazlı tarihsel xG endpoint kapsamı* ve kullanım koşulları ayrıca doğrulanmadan güvenilir kaynak sayılmaz.
3. **StrikerAPI** https://sportsdatastack.com/leagues/eredivisie/match-results/
   - Üçüncü taraf dizin Eredivisie ve Primeira Liga için şut konumu bazlı xG ile ücretsiz kota iddia ediyor.
   - Birincil belge, ücretsiz kota ve 2025-26/2026-27 veri kapsaması henüz doğrulanmadı.
4. **Footiqo** https://football-data.co.uk/footiqo.php
   - Ücretli geçmiş xG paketleri sunuyor. Kullanıcı onayı olmadan ücretli kaynağa geçilmez.

## Kesin kabul kapısı
- Kaynakların veri kullanım koşulları ve zaman damgası kayıt altına alınır.
- Yalnızca kesin takım kimliği + tarih + final skor eşleşen maçlar; hiçbir veri sessizce mevcut maçlara yazılmaz.
- İlk yarı korner verisi toplanmaz, doğrulanmaz ve zorunlu veri kabul kapısına dahil edilmez.
- xG negatif olamaz, finite olmalı; rakip/ev-deplasman yönü doğrulanır.
- Eksik kayıtlar tahmin motorunda tahmin edilerek 'gerçek veri' diye gösterilmez.
- Önce *salt okunur pilot* ile 10 lig / 2 sezon kapsama ve çakışma raporu; sonra matematiksel fayda testi. Elle veri girişi son çare.

## Çalışma kararı
Bu araştırma veri varlığını değil **aday kaynakları** tespit etmiştir. Kaynakların fiili veri doluluğu, doğruluğu ve lisansları doğrulanmadan 'eksik veri tamamlandı' denmez.
