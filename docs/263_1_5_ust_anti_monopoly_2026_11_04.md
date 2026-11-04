# 2.6.3 — 1,5 Üst tekelleşme denetimi (4 Kasım 2026)

**Kural:** 1,5 Üst yasak değil; yalnızca yüksek ham yüzdeyle otomatik birinci olamaz. 2,5 Üst de sırf daha yüksek baz farkı var diye seçilemez. Mevcut C2, B, C3, M4, S1/S2 matematik motorları değişmeden kalır.

Matematik: P(1,5 Üst) = P(2,5 Üst) + P(tam 2 gol). Bu yüzden ham yüzde karşılaştırması mekanik olarak 1,5 Üst lehinedir. 4.509 maçlık aşama verisinde 10 lig toplamında yaklaşık 1,5 Üst %77,8, 2,5 Üst %54,8 gerçekleşti. Bunlar model doğruluğu değil taban sıklıklarıdır.

**İzole karşılaştırma:** Her pazar için maçtan ÖNCE oynanan aynı lig karşılaşmalarındaki baz sıklık bulunur. Bir araştırma adayı olarak tahmin ile kendine ait baz arasındaki fark kıyaslanır. 2,5 Üst daha düşük yüzdeye rağmen kendi bazına göre daha güçlü olabilir. 1,5 Üst de kendi bazına göre öne çıkabilir. Keyfi eksi 10 puan ceza ya da maç kotası yok.

Gerçek araştırma: 6 Kasım Gaziantep FK–Kasımpaşa maçının 4 Kasım'da mühürlü erken kayıt ve TUR1 396 önceki maçında 1,5 Üst baz %76,8; 2,5 Üst baz %54,5. Dört model iki Üst çizgisi için de bu tabanın altında. Bu yalnız pozitif Üst baz farkı yok demektir: **otomatik Alt, PAS veya canlı bahis kararı değildir**.

**Nihai sistem şartı:** Tarih sıralı geçmiş maçlarda her pazara özgü kalibrasyon, Brier/log-loss, PAS-kapsama ve güvenilirlik; varsa aynı anlı doğrulanmış bahis oranıyla no-vig/EV. Fiyatlı S2 kararı, basit lig baz farkı negatif olsa bile ayrı değerlendirilir. Başarı kanıtlanmadan S1/S2 kararı üretilmeyecek. 1,5 Üst ve 2,5 Üst aynı maçta birbirinden bağımsız ana ve alternatif gibi gösterilmeyecek.

Korumalar: eski model kodu, 96 maçlık resmî pilot, ana dal ve kaynak kabul kuralları değişmedi. Yeni modül yalnızca salt-okunur araştırma, ana/alternatif boş. Brier için farklı olay sıklıklarını çıplak karşılaştırma uyarısı: https://pmc.ncbi.nlm.nih.gov/articles/PMC12818272/ .