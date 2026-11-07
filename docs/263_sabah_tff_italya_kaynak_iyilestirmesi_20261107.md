# 7 Kasım 2026 — resmî kaynak-bazlı canlı fikstür denetimi

**Girdi:** 96 sabit adaylık 6–8 Kasım kohortunun 7 Kasım için 44 maçlık bölümü. Son resmî kaynak taraması saatli 7, sadece gün 4, doğrulanamayan 33 statüsü verdi. Bu yalnızca sayfa taramasının görünürlüğüdür; dört model tahmini oluşturulduğu anlamına gelmez.

**Doğrulanmış yeni kaynak adresleri:**

- İtalya: https://www.legaseriea.it/serie-a/news/le-designazioni-arbitrali-della-11a (4 Kasım 2026 Serie A 11. hafta; Cumartesi dört maçın ayrı saatleri).
- Türkiye: https://www.tff.org/default.aspx?ftxtID=2966&pageID=600 (6 Kasım 2026 TFF 11. hafta; dört Cumartesi eşleşmesi). Türkçe karakterler için UTF-8 başarısızsa yalnız TFF'ye Windows-1254 çözümlemesi uygulanır.
- Almanya: https://products.bundesliga.com/fixtures dış kaynak araştırmasında saatli fikstür barındırıyor; fakat GitHub ham HTML okuyucusu sıfır maç çıkarıyor. Çalıştığı kanıtlanmadan onaylı kabul edilmez.
- Championship, Portekiz ve Belçika resmî sayfaları GitHub ham HTML ile doğru saatli eşleşme vermemiştir. Engel açıkça raporlanır.

**Uygulama:** official_page_lookup_263.py içinde İtalya ve TFF için yalnız 2026 Kasım 11. haftasının gerçek resmî kaynak satırlarına dayanan sınırlı ayıklama vardır. Ev/deplasman ve eşsiz lig sezonu kimliği ayrıca analyze_named_match_gate ile kontrol edilir. Bu yöntem sonraki sezonlar için genellenmiş değildir.

**Güvenlik:** Resmî açık saat yoksa KO uydurulmaz. KO geçmişse ileri tahmin oluşturulmaz. main, sabit 96 aday, önceki mühürler, B/C2/C3/M4, kalibrasyon kilitleri ve odds API kredileri değişmez. Mevcut GitHub CI yalnız çevrimdışı parser testleri ve ayrı canlı resmî sayfa okuma tanısı çalıştırır.

**Kabul:** Önceki taramaya karşı yeni taramada saatli eşleşme ve blok nedenleri karşılaştırılır. Sayfada eşleşme görülmesi uçtan uca model kayıt başarısı anlamına gelmez.
