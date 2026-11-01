# 2.6.3 — Kullanıcı tarafından belirtilen maç için doğrulama kuralı

**Öncelik:** kullanıcı maçı söyler → o anda resmî lig/federasyon kaynağı sorgulanır → maçın varlığı, ev/deplasman ve saat doğrulanır → kimlik eşleştirilir → tarihsel veri denetlenir → analiz hesaplanır. Önceden hazırlanmış resmî fikstür listesi, otomatik maç seçme veya Modül 0 **YOK**.

- Mevcut `analyze_named_match_gate.run` ve `verify_match_on_demand.verify_named_match` yeniden kullanılacak. Resmî sitenin yalnız URL'si değil, gerçekten getirilmiş ve okunmuş maç gözlemi gerekir.
- Maç doğrulanmazsa analiz başlamaz. Kaynakta tarih/saat henüz belirtilmemişse maçın varlığıyla saat doğrulaması ayrı raporlanmalı; mevcut doğrulayıcı saat yokken `VERIFIED` veremiyor (**açık sınırlama**).
- Takım kimlikleri 215 takımlık tarihsel kayıtla bağlanır, fakat geçmiş federasyon bayrağı canlı doğrulama yerine geçmez. Kulüp kısaltmalarının resmî kaynak adlarıyla eşleşme sorunu ana gateway'de halen ayrıca incelenecek.
- Resmî ilk 11 açıklanmamışsa `NOT_CHECKED` ya da gerçekten kontrol edilmişse `NOT_PUBLISHED_OFFICIAL_CHECK`: analiz durmaz.
- Sakatlık, ceza, taktik haberleri kaynak adresi, tarih ve takım kimliğine bağlanmadan doğrulanmış sayılamaz. Doğrulansalar bile matematiksel ağırlıkları ayrıca kanıtlanmadan C2/C3 lambda değerlerini değiştirmezler.
- Kaynak/güncellik kontrolleri **gerçek web doğrulaması değildir**; bu kod sadece mevcut resmî bakıcıdan gelen denetlenmiş kayıtları işler. Girilen kaynak JSON'unun doğruluğu dışarıda güvenilir adaptörün görevidir.
- 2.6.3 matematik/rapor modülleri hâlâ deneysel ve pazar önerileri kapalıdır. Bu katman sadece `READY_FOR_DATA_AUDIT` üretir; maç tahmini, pilot, oran, EV veya sonuç kaydı üretmez.

## Bu turda yapılanlar

1. Yeni `on_demand_context_263.py`: yalnız belirtilen maç için kapı ve optional kadro/ceza kanıtları; otomatik fikstür seçimi yok.
2. Yalnız yeni katmana yönelik sentetik yazılım testleri. Önceki gerçek maç performans deneyleri tekrarlanmadı.
3. Ana Model B, C2, C3 veya 2.6.3 şablon formülleri değiştirilmedi.

## Sonraki teknik mesele

`analyze_named_match_gate.run` içindeki resmî takım adlarının talep edilen takma adlardan farklı olmasını doğru kimlik üzerinden ele alma ve eski `2_6_2` next-step etiketini düzeltme. Bunu tek paket halinde test ederek ana motoru değiştirmeden yalnız deney dalında uygulamak gerekir.

## Tüketim ve güvenlik sınırları

- Deney dalındaki kodu proje kökünden, `PYTHONPATH=.:experiments/263` ile kullan. `prepare_named_match('TUR1', '...', '...')` sadece maç/bağlam **hazır bulunuşunu** döndürür; sonraki aşamadaki matematik analizi ayrı olarak bağlanacaktır.
- Resmî kaynak adaptörlerinin gerçekten fetch/parse yapması `analyze_named_match_gate` tarafından zorunlu tutulur. Bu deneyin `fixture_gate` parametresi **yalnızca deterministik birim testleri** için kullanılmıştır.
- Zaman ve tarih doğrulaması lig saat dilimiyle yapılır. Yerel maç tarihine UTC gününü doğrudan kopyalama.
- `VERIFIED_SOURCE_RECORD` ilk 11 için ancak iki ayrı 11 kişilik benzersiz oyuncu listesi mevcutsa verilir; bu, oyuncuların **maçtan önce resmî sayfada gerçekten görüldüğünü kendi başına kanıtlamaz**. Kaynağı gözlemleyen adaptör de ayrıca doğrulanmalı.
- Eksik kadro bilgisi analizi durdurmaz. Eksik/şüpheli sakatlık, ceza ve taktik verisi gol beklentisini değiştirmez.
- Kaynak URL'si lig resmî etki alanına ait olsa bile **site erişim testi yerine geçmez**.

## Tek grup test kaydı

- 14 yeni sentetik isimli-maç / kaynak / ilk 11 / saat bölgesi testi başarılı.
- Önceki matematik, veri bağlamı, kalite kapısı ve kimlik entegrasyonundan 61 regresyon testi başarılı.
- Toplam **75/75** test geçti. **Yeni gerçek maç tahmini veya tarihsel model performans karşılaştırması yapılmadı.**
- Açık işler: resmî adı farklı yazılmış takımın eşdeğer kimlikten doğrulanması; başlangıç saati açıklanmamış maçlarda `DATE_VERIFIED_TIME_PENDING` yolu; güncel kadro adaptörleri; matematik modelini güvenli analiz girişine bağlama. Bunlar bu turda tamamlanmış gibi gösterilemez.