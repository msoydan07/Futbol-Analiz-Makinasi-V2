# 2.6.3 M1 10-lig ortak güç ağı ve M2 geçmiş UEFA görünürlüğü

**Yeni aşama, 2 Kasım 2026.** Bir önceki *9/9 başarıyla
dondurulmuş* M0/M1/M2 kronolojik deney ön kaydı (run 41494401386)
esas alınır. 132 UEFA resmî match-ID link sonucu (41488522760),
132 xG'siz geçmiş gol girdi tablosu (41493071435) ve ön kayıt
çıktısı GitHub artefaktlarından **aynen tekrar kullanılacak**.
Önceki 432, 288/132, 126/89/0, 47 kulüp, 132 maç,
12/12 xG yasağı veya 9/9 ön kayıt testlerini TEKRARLAMA.

## Tek gerekli yeni ölçüm

1. 2025 Eylül–Kasım arası **76 yapısal uygun eğitim**
   maçının ülke/liglerini bir grafik olarak say:
   Kulüpler 10 ligden, kenar farklı ligdeki UEFA rakibidir.
   10 lige tek bileşende ulaşılabiliyor mu, hangi ligin
   kaç karşılaşması/kaç farklı lig komşusu var?
   Grafik bağlı olsa bile 76 maç **güvenilir kalibrasyon**
   kanıtı değildir. Ülkeler arası güç katsayısı
   KESİNLİKLE HENÜZ EĞİTİLMEYECEK.
2. M2 için önceki UEFA puan/gol/rakip özellikleri
   gerekir. Önceki 132 maç, 2025/26 UEFA
   karşılaşmalarının yalnız **10 lig içi çiftleri**
   olduğundan her kulübün bütün diğer UEFA
   rakipleri bu kayıtta yoktur.
   Önceki maç haftası sayısı ile mevcut kapsama
   giren önceki UEFA maçları kıyaslanır.
   **Eksik geçmiş maç sıfır puan/gol olarak
   doldurulmaz.** Üçlü eşleştirilmiş testte
   M2'nin farklı küçük örneklemde sessizce
   çalıştırılması YASAK.
3. xG, xGA, xG vekili, H2H, kapsam dışı
   kulüplerin başka lig sonuçları, geçmiş
   görünmeyen yayın zamanı iddiası YOK.
   Aynı gün sonuçları geçmiş maçlara taşınmaz.
4. Bu aşama **yeni matematik testi değildir**;
   ülke grafiği/veri temeli için tek uygunluk
   ölçümüdür. M1'in ve M2'nin yapılabilirliği
   tek raporla kabul/bloğa karar verilir.

Tüm değişiklikler yalnız
`experiment/263-toplu-karsilastirma` dalındadır.
Üretim `main`, 10 lig B/C2/C3/M4,
100 maç pilot, A/B/C, T–60 11 ve
kullanıcının saati **dokunulmaz**.
