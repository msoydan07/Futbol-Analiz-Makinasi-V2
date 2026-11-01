# Futbol Maç Analiz Makinası 2.6.3 — Resmî maç kaynaklarının dinamik okunması

**Durum (1 Kasım 2026):** İzole deney; ana Model B değiştirilmedi. Yeni gerçek maç tahmini, bahis/oran, Modül 0 veya pilot yapılmadı.

## Döngü denetimi

Var olan 215 takımlık kimlik dizini, 11 kaynaklı Maçkolik takma adı, tarihsel veri, Matematik C2/C3, pazar kalite kapısı ve eski tarihsel denemeler değişmedi/yeniden çalıştırılmadı.

## Yeni kod

- `experiments/263/official_page_lookup_263.py`: Resmî lig veya federasyon sayfasını **kullanıcının istediği maç için** gerektiğinde indirir, alan adını denetler, yapılandırılmış resmî maç olaylarını çıkarır, yedi günlük koşulunu uygular. Her zaman yalnız istenen ev/deplasman ikilisini kontrol eder. Güncel resmî siteye erişemediğinde maç var/yok diye kesin hüküm vermez.
- `experiments/263/named_match_coverage_263.py`: Önceki `mackolik_identity_gate_263.py` ve sabit 215 takım kimlik listesini kullanır. Maçkolik yazımı ile resmî sayfanın farklı adları **aynı takım ID'sine** karşılık gelmelidir. Yalnızca resmî sayfadan çıkarılmış veriyi gözlem olarak kabul eder. Sentetik HTML ve taklit ağ yanıtları testte asla canlı başarı olarak etiketlenmez.
- İki yeni bağımsız test dosyası. **26 test başarılı**, önceki model testleri tekrar edilmedi.

## Lig kapsamının dürüst durum tablosu

| Lig | Kaynak sayfası | Yeni sayfa ayrıştırıcısı | Operasyonel durum |
|---|---|---|---|
| ENG1 | Premier League resmî 2026/27 duyurusu | Tarih, ev/deplasman ve varsa ilan edilen saat | **Yazılım testi geçti**; duyurudaki saat geçici sayılır; güncel ikinci kontrol gerekli |
| GER1 | Bundesliga/DFL `products.bundesliga.com/fixtures` | Resmî tablo: tarih, UTC saat, ev/deplasman | **Yazılım testi geçti**; canlı sayfa bağlantısı ayrıca sınanacak |
| NED1 | KNVB resmî Eredivisie programı | Gün, ev sahibi, saat, deplasman | **Yazılım testi geçti**; canlı sayfa bağlantısı ayrıca sınanacak |
| ENG2 | EFL resmî maç sayfası | JSON-LD SportsEvent bulunursa | **Kapsam doğrulanmadı**; eski haftalık adaptör ayrıca duruyor |
| ESP1 | LaLiga resmî sonuç/maç sayfası | JSON-LD SportsEvent bulunursa | **Kapsam doğrulanmadı**; önceki hafta bazlı adaptör var |
| ITA1 | Lega Serie A resmî maçlar | JSON-LD SportsEvent bulunursa | **Kapsam doğrulanmadı**; önceki hafta bazlı adaptör var |
| FRA1 | Ligue 1 resmî maçlar | JSON-LD SportsEvent bulunursa | **Kapsam doğrulanmadı**; önceki kulüp duyurusu adaptörü var |
| TUR1 | TFF resmî site | JSON-LD SportsEvent bulunursa | **Kapsam doğrulanmadı**; ayrı TFF adaptörü var |
| POR1 | Liga Portugal resmî takvim | JSON-LD SportsEvent bulunursa | **Kapsam doğrulanmadı**; önceki duyuru adaptörü var |
| BEL1 | Pro League resmî site | JSON-LD SportsEvent bulunursa | **Kapsam doğrulanmadı**; önceki tek maçla sınırlı kulüp adaptörü var |

Kaynak adresi, tüm maçların erişilebilir olduğu anlamına **GELMEZ**. Sayfa değiştiğinde `NOT_VERIFIED` döner; başka bir siteden rastgele maç/saati uydurmaz. Yeni kod tüm 10 lig için tek bir **güvenli giriş arayüzü**, tüm 10 lig için kanıtlanmış **tam kapsama** değildir.

## Karar/kısıtlar

1. **Sadece kullanıcı maç adı verirse** arama yapılır. Maçkolik adı kaynaktır, fikstür kanıtı değildir. Yeni maç seçimi/Modül 0 yok.
2. Resmî site gerçekten indirildi/ayrıştırıldı ise ve eşleşen iki takımın ID'si doğruysa tarih/başlama saati sınıflandırılır. Zamanı bilinmeyen veya Premier League'in genel sezon duyurusunda sonradan değişebilecek saatler ayrı tutulur. Başlama günü tekrar saat doğrulaması gerekir.
3. İptal/ertelenmiş kaydı, farklı adrese yönlendirme, kimlik belirsizliği, çelişkili eşleşme ve eksik sayfa verisi başarılı maç olarak işlenmez.
4. İlk 11 açıklanmaması analizi durdurmaz. Kadro, oran/EV, gerçek maç kayıtları veya matematik katsayıları bu deneyde değiştirilmedi.
5. **Teknik açık iş**: 7 ligde JSON-LD dışındaki resmî HTML/JSON/kalıcı dinamik fikstür kaynaklarının lig bazlı doğrulanması; var olan haftalık adaptörlerin bu yeni arayüze sınırlı geri dönüş olarak bağlanması ve GitHub Actions'ta ayrı uçtan uca doğrulama. Bu işlemler henüz yapılmadı. Ana motora terfi yok.

## Kaynak kontrolü

- Premier League 2026/27 duyurusu: https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-season-2026-27
- Bundesliga/DFL resmî fikstür tablosu: https://products.bundesliga.com/fixtures
- KNVB Eredivisie programı: https://www.knvb.nl/competities/eredivisie/programma
- EFL maçlar: https://www.efl.com/matches/
- Lega Serie A program: https://en.legaseriea.it/serie-a/fixtures-results
- Liga Portugal: https://www.ligaportugal.pt/calendar

## Sonraki tek iş

Bu denetim tekrar edilmeyecek. Artık 7 ligin (ENG2, ESP1, ITA1, FRA1, TUR1, POR1, BEL1) **gerçek resmî veri biçimlerine özgü** dinamik ayrıştırıcılarını kontrollü, aynı kurallara bağlı bir pakette tamamlamak. Bir sonraki toplu kabulde her lig için *en az bir farklı haftadan* resmî sayfayla doğrulanmış eşleşme gerekir; aksi hâlde lig `NOT_VERIFIED` kalır. Model/pilot/EV tarafına geçilmez.