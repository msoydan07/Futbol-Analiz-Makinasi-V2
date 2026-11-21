# P1 — Footiqo resmî manuel dışa aktarım denetleyicisi

**21 Kasım 2026 — Bağımsız araştırma; ana 2.6.3 ve geçmiş SHA mühürleri değişmez.**

## Veri nereden gelir?

Kaynak: https://footiqo.com/database/ — resmî lig sayfası, **Odds** ve **Overview** veya **Scores** tablolarının standart **Export CSV** komutları.

Kullanıcı tabloyu web sitesinin kendi butonuyla **manuel** indirir; dosyaların satırlarını elle yazması gerekmez. Aynı lig/sezon için iki CSV gerekir:

- **Odds CSV:** `id, matchDate, Country, League, Season, homeTeam, awayTeam, H, D, A, O25, U25, BTTSY, BTTSN` sütunları (ek sütunlar olabilir).
- **Scores/Overview CSV:** aynı `id, matchDate, ...` kimlikleri ile `FTHG, FTAG, FTR` sütunları.

İndirilmiş dosyalar kişisel/beyan edilmiş ticari olmayan araştırmada işlenebilir. Site izinsiz otomatik indirmeyi ve veri setinin kamuya açık GitHub'a konmasını yasaklıyor: https://footiqo.com/dataset-licence/ . **Bu yazılımın ağ erişimi ve scraping işlevi yoktur.**

## Kullanım

GitHub'daki `experiments/p1_market_intelligence` klasöründe, örneğin:

```bash
python experiments/p1_market_intelligence/p1_footiqo_manual_export.py \
  --odds '/PRIVATE/Odds_Premier_League.csv' \
  --scores '/PRIVATE/Scores_Premier_League.csv' \
  --output '/PRIVATE/p1_footiqo_aggregate.json' \
  --attest-official-manual-export \
  --attest-private-noncommercial-research
```

İstenirse birden fazla lig dosyası `--odds` ve `--scores` parametrelerinden sonra boşlukla sıralanabilir. Python 3.11 yeterlidir; P1 `p1_market.py` dosyası aynı klasörde olmalıdır. `--attest-*` seçenekleri yalnız beyan edilen koşullar doğruysa kullanılmalıdır.

## Kontroller

- Odds ve sonuç dosyaları **sayısal aynı `id` + aynı tarih, lig, sezon ve takım isimleriyle** eşleştirilir.
- Yedi fiyatın hepsi zorunlu; 3 pazar ayrı ayrı marjdan arındırılır.
- Zorunlu alan/odds eksikse, fiyat geçersizse, olağandışı pazar toplamı varsa veya maç gelecekteyse **ret**.
- Son skorların ev/deplasman sonucu (`FTR`) ile çelişmesi ret; yinelenen skor kimliği toplu veri alımını durdurur.
- Tarihsel oranların gerçek *as-of* gözlem zamanı tablolarda olmadığı için **"yayıncı tarafından kapanış olarak etiketlenmiş, bağımsız zaman kanıtı yok"** statüsü korunur.
- Sonuç JSON'u **tek maçın ham fiyatlarını veya site CSV satırlarını içermez**. Kaynak dosyaların SHA256'ları, kabul/ret sayıları, lig/sezon dağılımı ve betimsel P0/P1 Brier, log-loss ve ana tercih isabeti yer alır.
- En az 200 maç ve 8 farklı tarih varsa kronolojik, **kalibrasyonsuz** eğitim/test raporu da üretilir. Bu çalışma yeni kalibrasyon katsayılarının doğrulandığı anlamına gelmez.
- Veri, maç sonucu girilmeden önceki bağımsız mühürlü arşivle doğrulanmadığı sürece P1 üretime terfi edilmez.

## Kapsamı ve durumu

**11 sentetik test yerelde geçti.** Gerçek Footiqo CSV dosyası henüz edinilmedi; **yeni gerçek tek şirketli maç testi yapılmadı**. `p1_market.py` ve bütün üretim dosyaları değiştirilmedi.