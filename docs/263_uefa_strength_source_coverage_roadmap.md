# UEFA CL+EL ligler arası güç köprüsü — 1. Aşama gerçek veri/kimlik denetimi

Amaç: 10 yerel lige veya B/C2/C3/M4 modeline dokunmadan UEFA takımlarını
mevcut canonical registry ile güvenilir biçimde bağlayabilmek.

Mevcut 432 maçlık açık tarihsel kaynak:
- 2024/25 Şampiyonlar Ligi lig aşaması: 144 maç 470 gol
- 2024/25 Avrupa Ligi lig aşaması: 144 maç 408 gol
- 2025/26 Şampiyonlar Ligi lig aşaması: 144 maç 487 gol
- openfootball/champions-league, sabit commit abfaeddc2ee3d14f99ecc163c9ddb46cb4d67cef

Yeni kod `experiments/263/europe/uefa_strength_source_audit_263.py`:
- Girdide yalnız bu üç sabit kaynak dosyasını kabul eder;
  her maçın kaynak satırındaki UEFA kulüp adını ve (ENG/TUR...) ülke
  işaretini ayrı korur.
- Kaynak satırlarının 36 takım x 8 maç, 18 maç x 8 hafta, gol toplamı
  ve benzersiz maç anahtarı güvenlik kontrollerini önceki parserdan kullanır.
- Canonical 10 lig kimlik cache'indeki **yalnız birebir normalize isim
  eşleşmelerini** `EXACT_NAME_CANDIDATE_NOT_VERIFIED` olarak verir;
  fuzzy isim eşleştirme, ülkeye bakıp takım kimliği tahmin etme,
  maç öncesi güç puanı üretme ve otomatik takım terfisi YOK.
- 2024/25 sonuçlarıyla 2025/26 ve 2026/27 takım üyeliklerini
  aynı tarihsel sezon gibi sunmaz. Şimdiki registry geçmiş 2024/25
  kulüp-üyelik kanıtı değildir.
- Çıktı: `data/europe_staged_263/strength_bridge_audit/` klasöründe
  denetim JSON'u ve manuel doğrulanacak UEFA isimleri CSV'si.
- GitHub Actions artefaktı: `263-uefa-strength-bridge-source-identity-review`.
- Yanıt: Gerçek kulüp eşleştirme kapsamı ve **hangi kaynakların eksik**
  olduğunu sayısal olarak göstermek; bu henüz çalışan güç modeli değil.

**Önceden kabul edilen sonraki aşamalar:** Eksik 2025/26 Europa League
bağımsız sezon ve güncel UEFA CL/EL sonuçları; UEFA kulüp ID
crosswalk'ının resmî kaynaklardan kanıtlanması; 2024/25 yerel
lig tarihsel verilerinin veya o yılın güvenilir ratinglerinin temini;
sonra aynı örneklemde ham lig kıyası / kalibre ortak güç / ortak güç +
rakibe göre performans karşılaştırmalı deneyi. 'Motivasyon' diye
yeni, keyfî bir puan veya gereksiz H2H testi olmayacak.
