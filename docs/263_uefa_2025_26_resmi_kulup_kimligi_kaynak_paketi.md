# 2.6.3 2025/26 UEFA resmî kulüp ID bağlantıları — kanıt paketi

**2 Kasım 2026 — tek yeni kaynak/kimlik denetimi.** Daha önce başarıyla
tamamlanan 288/132 aday kapsam (run 41480542512) ve 132 maç öncesi
yerel veri denetimi (run 41485016193) **yeniden çalıştırılmaz**.

## Kullanılan resmî sezon bağlantıları
- UEFA Champions League 2025/26 **36 takım** tanıtımı:
  https://www.uefa.com/uefachampionsleague/news/029d-1ea2e7e3e5d8-c5227ee0ab3c-1000--meet-the-2025-26-champions-league-league-phase-teams/
- UEFA Europa League 2025/26 **36 takım** tanıtımı:
  https://www.uefa.com/uefaeuropaleague/news/029c-1e982c79daa1-597a684fc805-1000--2025-26-europa-league-meet-the-league-phase-teams/

Bu iki resmî sezon tanıtım sayfasının **bizzat kulübe tıklanan bağlantıları**
2025/26 katılımcı takım isimleriyle **kalıcı sayısal kulüp profili ID**
sunuyor. ChatGPT web araştırmasında 10 lig kapsamındaki
29 CL + 18 EL takımının bu URL bağlantıları incelendi.
Örnekler:
- Galatasaray: https://www.uefa.com/uefachampionsleague/clubs/50067--galatasaray/
- Barcelona: https://www.uefa.com/uefachampionsleague/clubs/50080--barcelona/
- Fenerbahçe: https://www.uefa.com/uefaeuropaleague/clubs/52692--fenerbahce/
- Braga/SC Braga: https://www.uefa.com/uefaeuropaleague/clubs/52336--braga/

`experiments/263/evidence/uefa_2025_26_article_club_links_web_review.json`
**kaynağı burada web üzerinden incelenmiş** 47 takımın resmî
profil bağlantılarını ve mevcut canonical 2025/26 yerel
takım karşılıklarını bulundurur; 10 lig dışındaki hiçbir
takımın rakip ligi araştırılmaz.

**Kaynak disiplini:** GitHub Actions UEFA sayfalarını ağdan
indirmiyor (önceki GitHub runner erişim zaman aşımı);
ayrı kanıt dosyasının 47 URL'sinde sayısal ID, uygun
UEFA domain/turnuva, 2025/26 sezon yazısı, mevcut canonical
2025/26 takım ID'si, ID benzersizliği kontrol ediliyor.
Bu adım **Web üzerinden incelenmiş kulüp bağlantılarının
yapısal kabulü**dür; CI'nin bizzat UEFA HTML'i bağımsız
indirdiğini söylemeyiz.

Ayrıca 132 maçtaki iki tarafın **mevcut kabul edilmiş
aday kaydı** ve ilgili 47 resmî UEFA kulüp numarası
arasında çelişki olmadığını kontrol eder.
Ama **132 resmî maç ID'sinin doğrulaması** yapılmış
sayılmaz. Tarihsel maç skorlarının resmî kaynak
tek tek onayı ve 2025/26 yerel istatistiklerin o maçtan
önce erişilebilirliğinin yayın zamanları eksiktir.

**Terfi yok:** B/C2/C3/M4, M0/M1/M2, form, xG,
Poisson katsayıları, oranlar, pilot/main değişmez.
Tam verifikasyon olmadan canlı yüzde açıklanmaz.
