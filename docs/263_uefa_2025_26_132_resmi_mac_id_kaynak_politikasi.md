# UEFA 2025/26 CL+EL: 132 maçın resmî maç numarası kaynak bağlantısı — deney incelemesi

**2 Kasım 2026.** Daha önceki **288/132** on-lig kapsam taraması
(run 41480542512), **126/89/0** maç öncesi veri kapsamı (41485016193)
ve **47 UEFA sayısal kulüp profil bağlantısı** (41486717971)
tekrar çalıştırılmıyor; olduğu gibi korunuyor.

Resmî UEFA 2025/26 sonuç yazılarında görünen tek tek maç
bağlantılarının tıklanmasıyla 95 CL ve 37 EL, **132 tarihsel
karşılaşma URL'si ve URL'deki UEFA match-ID** toplandı:
- https://www.uefa.com/uefachampionsleague/news/029c-1e9a2f63fe2d-ebf9ad643892-1000--champions-league-2025-26-all-the-results/
- https://www.uefa.com/uefaeuropaleague/news/029c-1e9b4e18c28e-3bb76afa22ac-1000--europa-league-league-phase-results-by-team/

Örnek doğrulanmış doğrudan bağlantılar:
- Galatasaray 1-0 Liverpool (30.09.2025):
  https://www.uefa.com/uefachampionsleague/match/2045927--galatasaray-vs-liverpool/
- Fenerbahçe 0-1 Aston Villa (22.01.2026):
  https://www.uefa.com/uefaeuropaleague/match/2046268--fenerbahce-vs-aston-villa/
- Braga 1-0 Feyenoord (24.09.2025):
  https://www.uefa.com/uefaeuropaleague/match/2046157--braga-vs-feyenoord/

Web'de görülen resmi arşiv maç listelerindeki **tarih ve
skorlar** da dosyaya kaydedildi. GitHub bu kaynak handoff'unu
üç mevcut kayıtla karşılaştırır: UEFA kulüp profil ID'leri,
2025/26 canonical 10 lig takım kimliği ve 132 tarihsel maç.
Tarih, gol, ev/deplasman yönü, UEFA URL'si,
match-ID, benzersizlik ve kaynak alan adı kontrol edilir.
Tüm 132 eşleşmezse test FAIL-CLOSED.

**Kaynak dürüstlüğü:** UEFA bağlantıları ChatGPT web'de
incelendi; GitHub runner'ı bu resmî HTML'i bağımsız
indirmedi. 132 resmî match-ID URL'sinin web üzerinden
gözlenmesi, tarihsel istatistiğin karşılaşmadan önce
yayınlandığı/erişilebilir olduğu anlamına GELMEZ.
Her URL'nin bütün sayfa verileri de bağımsız runner
tarafından çekilip imzalanmadı.

**Bu bir model eğitimi değil:** Mevcut xG açığı,
tarihsel as-of veri yayın zamanı ve kalibre ligler
arası güç köprüsü hâlâ kanıt bekliyor.
Yeni ligler, H2H, katsayı, yüzde, EV, bahis, pilot,
main/B/C2/C3/M4 değiştirilmedi.

**GitHub artefaktları:** `132_official_match_id_links_report.json`,
`132_UEFA_MATCH_IDS_REVIEW_ONLY.json`.
