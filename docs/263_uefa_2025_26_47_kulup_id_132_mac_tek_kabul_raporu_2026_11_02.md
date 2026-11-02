# 2.6.3 — UEFA 2025/26 CL+EL resmî kulüp kimlik bağlantıları / tek sonuç raporu

**Tarih:** 2 Kasım 2026. **Durum:** Resmî kulüp bağlantıları web üzerinden incelendi; GitHub yapısal eşleştirme ve kapsam testleri başarılı. **Matematik modeline/üretime terfi YOK.**

## Döngü kontrolü — tekrar edilmeyen tamamlanmış işler

| Önceki işlem | Kanıt | Bu adımda ne yaptık? |
|---|---|---|
| 2025/26 CL+EL 288 karşılaşma → 132 isim/kapsam adayı | Run [41480542512](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41480542512) | **Yeniden çalıştırmadık**; mevcut artefaktı okuduk |
| 132 aday için geçmiş yerel gol/xG zaman-kesit kapsamı (126 dört maç, 89 sekiz maç, 0 xG) | Run [41485016193](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41485016193) | **Tekrar etmedik**; sonuç korunuyor |
| UEFA fikstür HTTP problemi ve T–60 kadro testleri | Daha önce kapanan kayıtlar | **Yeniden araştırmadık/test etmedik** |

## Yeni resmî kaynak kanıtı

2025/26 UEFA CL resmî 36 takım yazısı:
https://www.uefa.com/uefachampionsleague/news/029d-1ea2e7e3e5d8-c5227ee0ab3c-1000--meet-the-2025-26-champions-league-league-phase-teams/

2025/26 UEFA EL resmî 36 takım yazısı:
https://www.uefa.com/uefaeuropaleague/news/029c-1e982c79daa1-597a684fc805-1000--2025-26-europa-league-meet-the-league-phase-teams/

Bu **2025/26 sezonu** takım yazılarında bulunan kulüp bağlantıları
tarayıcı üzerinden incelendi. On ligdeki kulüpler için doğrudan
`uefa.com/<turnuva>/clubs/<sayısal ID>--<kulüp>/` profil adresi
ve mevcut 2025/26 yerel canonical karşılığı ilişkilendirildi.

Örnek resmî kulüp ID'leri:
- Galatasaray UEFA #50067: https://www.uefa.com/uefachampionsleague/clubs/50067--galatasaray/
- Barcelona UEFA #50080: https://www.uefa.com/uefachampionsleague/clubs/50080--barcelona/
- Fenerbahçe UEFA #52692: https://www.uefa.com/uefaeuropaleague/clubs/52692--fenerbahce/
- Braga/SC Braga UEFA #52336: https://www.uefa.com/uefaeuropaleague/clubs/52336--braga/

## Gerçek GitHub kabul sonucu

Yeni işlem: [Actions run 41486717971](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41486717971) — **SUCCESS, 9/9 yeni kontrol PASS**.

| Yeni kontrol alanı | Ölçülen |
|---|---:|
| 2025/26 Şampiyonlar Ligi'nde kaynaklı ve kapsam içi UEFA kulüp profil linki | 29 |
| 2025/26 Avrupa Ligi'nde kaynaklı ve kapsam içi UEFA kulüp profil linki | 18 |
| **Tekil UEFA sayısal kulüp profil ID'si** | **47** |
| 132 eski UEFA aday maçında **iki taraf için de** resmî UEFA kulüp profil linki bulunan | **132 / 132** |
| CL alt kümesi | 95 / 95 |
| EL alt kümesi | 37 / 37 |
| Farklı local kulübe bağlanan çakışan UEFA sayısal ID | 0 (fail-closed kontrol) |
| GitHub CI tarafından canlı UEFA HTML indirildi mi? | **Hayır** |
| 132 UEFA maçının **resmî maç sayfası ID'si** doğrulandı mı? | **Hayır** |
| Avrupa matematik motoru onaylandı mı? | **Hayır** |

Çıktı artefaktı: `263-uefa-2025-26-official-club-id-link-review`.
İnceleme kanıt dosyası:
`experiments/263/evidence/uefa_2025_26_article_club_links_web_review.json`.
Aday 132 karşılaşmanın üzerine **resmî profil ID referansı eklenmiş
inceleme-only kayıt** oluşturuldu; eski artefakt veya kaynak değiştirilmedi.

### Kaynak ve kanıt sınırı

Web araştırmasıyla **2025/26 UEFA yazılarından profil bağlantıları gözlendi**.
GitHub Actions'un UEFA sitelerine otomatik bağlanıp onları bağımsız
okuduğunu iddia etmiyoruz; test, sunulan kaynak bağlantılarının
alan adı, URL sayısal ID, local takım kimliği ve 2025/26 üyeliği ile
**çelişmemesini** kontrol ediyor.

**Resmî kulüp profil numarası = resmî maç numarası değildir.**
132 maçın her birinin UEFA maç-ID, tarih/saat/skor ve takım
taraflarının bağımsız kanıtı ayrıca gereklidir.
Ayrıca 2026'da derlenmiş bir sonuç CSV'sinin tarihsel 2025
UEFA başlangıç anından önce erişilebilir olduğunu söyleyemeyiz.
xG için de yeterli kaynaklı geçmiş çift bulunmadı.

## Mühendislik kararı / sıradaki tek aşama

**Bu kez çözülmüş olan:** Her iki takım 10 ligdeki kapsam
adaylarından olan 132 maçta 47 tekil resmî UEFA kulüp
numarasına dair, kaynağı ve sezonu belirtilmiş bağlantı
eşleşmesi var. İsim benzerliği artık tek başına referans değil.

**Sıradaki iş, tekrar olmadan:** 132 maçın UEFA resmî
**match-ID bağlantılarını** 2025/26 CL/EL resmî sonuç
arşivleriyle **tek toplu kanıt seti** olarak eşleştirmek;
kaynaklarda yalnız gün bilgisinin bulunduğu maçları as-of
tahmin testine sessizce dahil etmemek. Sonra yalnız gerekirse
geçmiş yerel verinin as-of yayın zamanı kaynak açığı raporlanacak.

**Değişmeyenler:** `main` (son denetimde
`11cdb67ba1935f183f454f1286b9350d2d8840d7`),
10 lig, yerel güncelleme hattı, B/C2/C3/M4, M0/M1/M2,
H2H iptali, 100 maçlık pilot, kullanıcı saati ve T–60
ilk 11 aşaması. **Hiçbir model veya oran/EV entegrasyonu yapılmadı.**
