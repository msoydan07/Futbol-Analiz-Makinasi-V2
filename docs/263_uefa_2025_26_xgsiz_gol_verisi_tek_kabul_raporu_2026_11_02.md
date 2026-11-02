# 2.6.3 — UEFA 2025/26 xG'siz gerçek gol-girdisi ve kaynak zaman kanıtı: tek toplu kabul raporu

**Tarih:** 2 Kasım 2026. **Durum:** Veri hazırlığı ve tarih-kaçağı korumaları BAŞARILI. Modelin doğruluğu / ligler arası ortak güç ölçeği **ONAYLANMADI**.

## Çalışmanın gerçek kanıtı
- Yeni, bir defalık CI çalışması: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41493071435 — **başarılı, 5/5 yeni test PASS**.
- Önceden başarıyla kabul edilen **4.413** yerel maçın SHA-kilitli `historical_results.csv` arşivi: run `41251343847`, hash `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- Önceden resmî UEFA maç numaralarıyla eşleştirilmiş **132** maçın salt-okunur inceleme artefaktı: run `41488522760`.
- Yeni artefakt: `263-uefa-2025-26-goal-only-prematch-input-readiness`; dosyalar: `xg_free_temporal_goal_feature_coverage.json`, `132_goal_only_feature_inputs_REVIEW_ONLY.json`.
- Uygulama: `experiments/263/europe/uefa_goal_only_asof_feature_readiness_263.py`.
- Girdiler UEFA web sayfalarından yeniden çekilmedi; daha önce kabul edilmiş orijinal GitHub Actions artefaktları kullanıldı.

## Gerçek sayılar

| Yeni, sadece geçmiş GOLE DAYALI veri kontrolü | UEFA CL | UEFA EL | Birlikte |
|---|---:|---:|---:|
| Önceden kimliği eşleştirilen inceleme aday maçları | 95 | 37 | **132** |
| İki tarafın da en az dört eski yerel lig maçı | 89 | 37 | **126** |
| İki tarafın da en az sekiz eski yerel lig maçı | 64 | 25 | **89** |
| İki tarafın da en az iki eski iç saha VE en az iki deplasman maçı | 87 | 37 | **124** |
| Her iki takımın ülke liginde maç gününden önce ≥30 tamamlanmış maç | 92 | 37 | **129** |
| 4+ eski maç VE 30+ ülke ligi maçı | 89 | 37 | **126** |
| 4+ eski maç + 2'şer iç/deplasman maçı + 30+ ülke ligi maçı | 87 | 37 | **124** |

**Çıktıda saklananlar:** 2025/26 aynı ligindeki her kulübün hedef tarihten önce oynadığı toplam/iç/deplasman maçları; gerçekleşmiş atılan ve yenilen golleri; aynı hedef tarihten önce tamamlanan kendi ülke ligi maçlarının ev/deplasman gol ortalamaları ve son gerçekleşen yerel lig maç tarihi.

**Kritik sınırlama:** 132/132 için hesaplanabilir bir bağlam satırı üretilebilmesi 132/132 için güçlü, güvenilir tahmin üretilebileceği anlamına GELMEZ. Başta altı örnekte iki tarafta dörder eski maç yoktur. 124 örnekte iç/deplasman şartları vardır; bu sayılar yalnız kapsama kanıtıdır. Şu anda herhangi bir Avrupa maçına `lambda`, MS1/X/2, KG, 2.5 Üst/Alt olasılığı veya EV hesaplanmadı.

## xG'siz matematik ve kaynak dürüstlüğü
- Kullanıcının kesin kararı uygulandı: **Her iki kulüpte xG/xGA, xG vekili ve xG'ye özel kaynak taraması YOK.**
- İki taraf da gerçek gol / yenilen gol / ülke ligi ev-deplasman sonuçlarıyla aynı kurallar üzerinden işlendi.
- Hedef UEFA takvim gününe eşit veya daha geç yerel maç sonuçları dışarıda tutuldu; sızıntıyı yakalayan yeni sentetik testler PASS.
- **Dikkat:** Bir ülke liginde maç başına 1,6 gol ortalaması, başka ülkede 1,6 gol ortalamasıyla aynı *rakip kalitesini* göstermez. Ortak ligler arası güç ölçeği henüz hesaplanmadı ve geçmişte başarısı kanıtlanmadı.
- Orijinal 4.413 satırlı CSV sütunlarında özgün kaynak yayına çıkışını veya ilk fetch zamanını kanıtlayan `published_at_utc`, `source_first_seen_at_utc` gibi **aday metadata zaman sütunları bulunamadı**.
- 2026'da üretilmiş/derlenmiş CSV'de bir yerel lig maçının tarihinin UEFA maçından önce olması, o verinin o gün **tam ve güvenilir biçimde erişilebilir olduğunu** kanıtlamaz. Gerçek zamanlı önceden kilitlenmiş tahmin ile geçmiş veri üzerinde as-of kesitli retrospektif çalışma AYRIDIR.

## Döngü kontrolü

**Bu raporda yalnız yeni iş yapıldı.** 432 maç eski UEFA puan/hafta deneyi, 288/132 kapsam, 126/89/0 xG veri denetimi, 47 kulüp profil ID, 132 resmî match-ID kontrolleri ve xG'siz araştırma kuralı yeniden çalıştırılmadı.

Main, 10 lig verisi, B/C2/C3/M4, H2H iptal kararı, kullanıcının saati, maç günü T–60 ilk 11, A/B/C, oran/EV ve 100 pilot aynen korundu. Çıktılar yalnız `experiment/263-toplu-karsilastirma` dalının deneme/inceleme alanındadır.

## Sıradaki mantıklı teknik iş / mühendislik kararı

**Aynı veri eksikliğinin etrafında döngüye girme!** Gerekli tarihsel kaynak ilk yayın damgaları bu özgün arşivde yok. Eski kayıtlara güvenilmez damga uydurma veya ayrı ayrı tüm 132 maç için tekrar yayın tarihi arama yok.

Bir sonraki *tek toplu* mühendislik çalışma paketi:
1. XG'siz, sonuçlara dayalı **M0 naif / M1 ligler arası kısmi havuzlanmış güç / M2 rakibe göre davranış** karşılaştırmasının **ön-kayıtlı tek kronolojik retrospektif protokolünü** yaz; verisi olmayan konfigürasyonları otomatik dışarıda bırak. 132/124 örneklem, dış sınama yetersizliği, UEFA'ya seçilen kulüp yanlılığı ve aynı 2025/26 veri yılına aşırı uyum tehlikesini ayrıca bildir.
2. Bu veri kaynaklarının 2025/26'da canlı erişilebilirliği kanıtlanamadığı için çalışma başlığı daima `RETROSPEKTIF_WALK_FORWARD_NO_LIVE_PREGAME_PROOF` olacak; böyle bir sonuç 100 maç canlı pilotun yerine geçmeyecek.
3. Yeni gol modeli parametrelerini veya katsayılarını bu veri kapsam sayılarından otomatik seçme. Varsa testler **tek ön-kayıtlı karşılaştırmalı deney** ve tek rapor içinde; iyileşme sürdürülebilir değilse yeni motor YOK. Canlı entegrasyon için ayrıca gerçek maç öncesi kilitli pilot gerekir.

**Bu aşamanın kararı: GOALS_SOURCE_FEATURE_READINESS_SUCCESS / UEFA_MODEL_NOT_APPROVED.**
