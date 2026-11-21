# P1 — tarihsel kaynak kararı ve ikinci araştırma aşaması

**Tarih:** 2026-11-21. **Dal:** `experiment/p1-market-intelligence-20261121`.
**Kapsam:** Yalnız bağımsız araştırma; 2.6.3, karar v4, mühürler, mevcut çalışma takvimleri değiştirilmez.

## Gerçek durum

Yedi oran için aynı maçta üç **ayrı** pazarın bütün karşılıkları gerekir: MS 1/X/2, 2.5 Alt/Üst, KG Var/Yok. Aynı kaynağın aynı fiyat aşaması (*opening* veya *closing*) esas alınır. Sonradan oluşan veya kimliği belirsiz rakam doldurulmaz. P1'in oranları tersine çevirmesi piyasadan bağımsız yeni bilgi üretmez.

| Kaynak | Kapsam | Hak ve fiyat doğruluğu | Karar |
| --- | --- | --- | --- |
| Kullanıcının orijinal iddaa PDF'leri | 36 farklı maç için yedi fiyatın tamamı daha önce çıkarıldı; canlı fikstür ve orijinal PDF dışındaki oranlarla karıştırılmaz | Kullanıcı belgeleri; özgün PDF baytları ana GitHub deposuna konmaz, SHA işaretleri bağımsız zaman mühürü değildir | Özel yerel P0/P1 betimsel replay devam; kör sezon testi sayılmaz |
| [`nm2890/football-data`](https://github.com/nm2890/football-data) | 1X2/2.5/BTTS açılış ve kapanış; yedi ana ligin eski sezonları | Açık bir LICENSE görünmedi; dosyalar bahis şirketleri ortalaması, iddaa değil. EPL dosyası Kasım 2024'te bitiyor, dolayısıyla 2024/25 **eksik**, 2025/26 bulunmuyor | **Lisans/izin açıklanana kadar toplu indirme, modele alma ve dağıtma yok.** Format araştırması olarak kalır |
| [`Sharp-API/SharpAPI-Sample-Data`](https://github.com/Sharp-API/SharpAPI-Sample-Data) | CC BY 4.0, gerçek Dünya Kupası 2026 fiyat anlık görüntüsü, 6132 fiyat satırı; 99 çeşit pazar | Lisans açık. Fakat 10 takip liginden biri değil; 6132 satır **6132 maç değildir**. Her aynı kitap/fixture için yedi fiyatı barındırdığı teyit edilmedi. Anlık görüntü sonuçlarını içermez | Kaynak/format kabul motoru için izinli teknik deneme adayı. 10-lig tarihsel eğitim havuzuna girmez |
| [`FootInsights/footinsights-data`](https://github.com/FootInsights/footinsights-data) | CC BY 4.0, maç öncesi 1X2 / O2.5 / BTTS **model olasılıkları** ve sonuçları | Bunlar bahis **oranı değil**. Olasılıklardan `1/p` ile sözde oran üretmek yasak | Bağımsız karşılaştırma/kalibrasyon referansı olabilir; P0/P1 fiyat havuzu **değil** |
| [`v-eatpizzanot/soccer-dataset`](https://github.com/v-eatpizzanot/soccer-dataset) | CC BY 4.0 olarak yayımlanmış; odds.csv 1X2 price fields | 2.5 ve BTTS fiyatları yok; altında üçüncü taraf API kaynağı | Yalnız kısmi pazar referansı; 7 olaylık P1 testine kabul yok |
| [`akareen/Football-Data-Analysis`](https://github.com/akareen/Football-Data-Analysis) | Çok geniş 1X2 CSV | MIT kod/depo lisansı üçüncü taraf bahis verisinin kullanım haklarını tek başına açıklamaz; BTTS/O-U yok | Tam P1 kapsamına uygun değil |

## Yeni kaynak kontrolü — Footiqo ücretsiz lig tabloları

**Daha uygun kaynak bulundu:** [Footiqo ücretsiz tarihsel lig veritabanı](https://footiqo.com/database/) ve [Premier League oran tablosu](https://footiqo.com/database/leagues/england-premier-league/). Kaynak; açılış/kapanış yerine yalnız **closing** fiyatları gösteren ücretsiz Odds sekmesinde **aynı sağlayıcı 1xBet** için MS 1/X/2, 2.5 Üst/Alt, KG Var/Yok **yedi gerçek marjlı fiyatı**, takım/lig/tarih ve maç kimliğini yayımlıyor. Skorlar aynı sayfanın Scores/Overview sekmesinde aynı ID ile mevcut.

Doğrudan sayfada incelenen **Arsenal–Coventry, 21 Ağustos 2026** örnek satırı: 1X2 (1.20,7.97,13.80); 2.5 Üst/Alt (1.54,2.53); KG Var/Yok (2.22,1.66). Aile bazlı ters fiyat toplamının 1'e göre farkı sırasıyla **+%3.13, +%4.46, +%5.29**; bu **marjdan arındırılmış konsensüs değil, ham fiyat** olduğunu destekler. Tek bir örnekten fiyatların gerçekten ilan edilen saatte piyasada bulunduğu ispatlanmış sayılmaz.

Site açıkça filtrelenmiş tabloların CSV/Excel olarak ücretsiz dışa aktarılabileceğini ve kişisel araştırmada kullanılabileceğini söylüyor: [veri açıklaması](https://footiqo.com/football-data/). Bununla beraber [kullanım şartları](https://footiqo.com/terms-of-use/) içeriğin yeniden dağıtımını sınırlıyor; ağır scraping veya toplu çekme için yazılı izin gerekli. Bu çalışmada **CSV otomatik indirilmedi, kaç geçmiş maçın eksiksiz olduğu teyit edilmedi**. Kullanıcı kaynaklı veya sahibin izin verdiği yerel CSV elde edilmeden GitHub'a ham veri konmayacak.

**Yeni mühendislik kararı:** Footiqo 1xBet = bağımsız *tek-bookmaker ham yedi fiyat* kohortu için **birinci aday**. OddsIntel 3.626 karşılaştırması ise tamamen ayrı, daha önce marjı silinmiş konsensüs verisi; iki grubun fiyatlarını aynı eğitim/test havuzunda kaynağı etiketlemeden birleştirme. Tek bookmaker kaynakta önce sezon ve lig genişliği, aynı maç/aynı fiyat anı, 7 fiyat eksiksizliği, sonuç tutarlılığı, kaynak lisansı ve geliş zamanı denetlenir. Kapanış fiyatlarının orijinal gözlem zaman damgaları yoksa yalnız yayıncı tanımlı kapanış kanıtı olarak sınıflandırılır; kör mühür iddiası yapılmaz.

## Aynı şirket koşulunu sağlamayan depoların örnek doğrulaması

- [samarpreetxd/Soccer-Betting-Model](https://github.com/samarpreetxd/Soccer-Betting-Model): 2025/26 Premier League ve Bundesliga gerçek CSV başlıklarında Bet365 MS/2.5 var ama **Bet365 KG Var/Yok sütunu yok**. Örnek kodda geçen `B365BTSY` ismi, yayımlanan gerçek CSV'lerde fiyatın varlığını kanıtlamıyor.
- [oxg43/hnlsupersport](https://github.com/oxg43/hnlsupersport): Hırvatistan 2024/25 CSV içinde 1X2, 2.5 ve KG sütunları bulunuyor, fakat **bookmaker kimliği dosyada yok** ve lisans açık değil; kullanıma alınmadı.
- [Bedbin17/oddsportal_scraper](https://github.com/Bedbin17/oddsportal_scraper): Tek bookmaker + 3 pazar için **kazıyıcı kodu**, yasal yeniden kullanım izni olan geçmiş veri arşivi değil; P1'de otomatik kazıma yapmayacağız.

## Tamamlanan mühendislik işi

- `p1_historical_intake.py`: Kullanım hakkı bildirimi, tarih, sonuç, aynı maç ve yedi oran kontrolü; kabul/ret gerekçeleri; araştırma çıktısı. **Lisans iznini otomatik olarak hukuken doğrulamaz.**
- `p1_research_aggregate.py`: Veri kabul raporundan, maç başına **tek** gözlemle eşleşik P0/P1 Brier ve log-loss farkları. Açılış ve kapanış, kitaplar ve ligler ayrı kohort. Örnek en az 30 ise yalnız betimsel paired bootstrap aralığı; 200 altına anlamlı üstünlük mesajı yok. Zaman ispatı olmadığı için 200 üstünde de otomatik üretime geçiş yok.
- `test_p1_research_aggregate.py`: tekrarlanan maç, kaynağın/evrenin karışması, sahte bağımsız zaman kanıtı, bozuk skor ve küçük örnek için koruma testleri.
- **Yeni dış veri alınmadı**, izin verilmemiş fiyatlar başka GitHub deposundan kopyalanmadı, lisanssız maçlar eklenmedi. Yeni tarihsel testte 0 yeni maç var. Kendi PDF örnekleri ile geçmiş açıklayıcı testler aynı kaldı.

## Çalıştırma (yalnız izinli yerel CSV sağlandığında)

```bash
python -m unittest discover -s experiments/p1_market_intelligence -p 'test_*.py' -v
python experiments/p1_market_intelligence/p1_historical_intake.py \
 --csv /tmp/licensed_cohort.csv --manifest /tmp/rights_manifest.json \
 --output /tmp/p1_audit.json
python experiments/p1_market_intelligence/p1_research_aggregate.py \
 --audit /tmp/p1_audit.json --output /tmp/p1_paired_report.json
```

Kaynağın lisans belgesini, kullanılan veri sürümünü/commit SHA'sını, maç öncesi fiyat aşamasını, sonuç kaynaklarını ayrı tut. Araştırma için onaylanmamış oranları otomatik çekme. M4/C3 ile aynı maçlarda geçmişte dondurulmuş tahminler olmadan P0/P1 üstünlük iddiası yapma. İddaa olmayan fiyatları ana bültendeki iddaa fiyatları yerine kullanma.

**Sonuç:** P1'in tarihsel veri kabul ve toplu karşılaştırma yazılımı çalışır; 10 ligin tüm sezonlarını kapsayan, açık izinli ve yedi oranlı tarihsel arşiv henüz doğrulanmamıştır.