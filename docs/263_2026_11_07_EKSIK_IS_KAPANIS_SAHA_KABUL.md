# 2.6.3 — EKSİK İŞLER KAPANIŞ / SAHA KABUL DEFTERİ (7 Kasım 2026)

## Son doğrulanan kod durumu
- Geliştirme dalı: `experiment/263-toplu-karsilastirma`; **main'e taşındığı iddia edilmiyor**.
- Kullanıcı onaylı mobil **toplu** PDF ve **tekli** PDF: `sabah_mobile_approved_pdf_263.py`, kaynak olarak mühürlü new100 + aynı-zamanlı fiyat araştırması; oran rakamları gösterilmez, marjsız piyasa olasılığı yoksa çizgi ve S2 PAS/ONAYSIZ korunur.
- 10 ligin resmî sayfa taraması: `sabah_10league_manifest_preflight_263.py`.
- Sadece kullanıcının o günkü komutuyla isteğe dönüştürülen, ayrıca Git commit gerektiren güvenli köprü: `sabah_manual_preflight_bridge_263.py`. Tek başına pilot kaydı veya oran sorgusu yapmaz.
- Championship resmî üç kaynak sıralaması: EFL match centre, EFL TV selections, EFL Championship competition page. Sonuncuda yalnız **SportsEvent JSON-LD ile açık timezone-aware kickoff** kabul edilir; salt tarihli maç asla başlangıç saatiyle tamamlanmaz. TV seçimi yalnız yayınlanan maçlar için kısmi kaynak.
- Son bütünleşik sentetik test: **218/218 başarılı**, CI koşusu `42387134151`. Ayrı resmî sayfa salt-okuma testi: `42387134232`, başarılı. Testlerde ücretli Pinnacle API çağrısı yok.

## Bilerek açık kalan durumlar — tamamlandı diye gösterilmez
1. **Championship %100 fikstür kapsaması kanıtlanmadı.** Resmî EFL sezon fikstürü yayımlanmış olmakla birlikte, herkesçe indirilebilir her maç için saatli/kanonik resmî web API'si doğrulanamadı. JS-only gösterim ve TV seçimi listesi kısmi. Resmî EFL/klüp sayfası tek maç için farklı yoldan doğrulanırsa güvenli kapıdan geçirilebilir. Harici üçüncü taraf liste **resmî federasyon kanıtı yerine geçirilmez**.
2. **Yarınki gerçek yeni100 pilot:** TSİ 05:00–14:59, kullanıcı aynı gün açıkça ister; yeni Git isteği, resmî karşılaşma ve KO kapısı, B/C2/C3/M4, tahmin öncesi SHA, yalnız gerçekten alınmış aynı sabah The Odds API Pinnacle fiyatı, mobil PDF, uzaktan SHA kayıt teyidi birbirinden ayrılarak raporlanmalı. Bu 7 Kasım akşamı gerçek 8 Kasım mührü üretilemez.
3. **Canlı fiyatın erişilebilirliği:** `THE_ODDS_API_KEY` bağlantısı veya o ligde geçerli Pinnacle h2h bulunmazsa 'Piyasa —' ve 'Fark —'; kıyas yüzdesi üretmek için sahte oran kullanılmaz. Sentetik test gerçek fiyat garantisi değildir.
4. **İleriye dönük isabet/kalibrasyon:** Modelin tahmin kabiliyeti, günlük teknik testlerin yeşilliğiyle ispatlanmış olmaz. Gelecek maçlarda önceden mühürlenen sonuçlar bittikten sonra, `sabah_postmatch_new100_263.py` ile kayıt-saha karşılaştırması ayrı ölçülmelidir.
5. **Tamamen otomatik, telefondan bir kelimeyle GitHub işini başlatma:** Kullanıcı komutunun operatör aracılığıyla GitHub yeni istek dosyasına geçirilmesi ve push adımı gerekebilir; yalnız rapor kodu/rehber olması bu adımı kendiliğinden yapmaz.

## Değişiklik yapılmayan alanlar
- B/C2/C3/M4 ağırlıkları; orijinal kalibrasyon; ileri pilot kayıt ve sayaçları; 09.00 mevcut otomasyon; The Odds API harcama/rezervasyon geçmişi; mühürlü tahminler.
- Değişiklikler deneysel branch üzerinde; canlı maç tahmininin garantisi değildir.

## Tek sonraki adım
8 Kasım Pazar günü kullanıcının gerçek isteği geldiğinde **bir** uçtan uca kabul koşusu: resmi maç adları ve saatleri, yeni SHA, 4 model verisi, varsa Pinnacle/marjsız yüzde, toplu/tekli PDF, uzaktan Git kanıtı, sonra tek sonuç raporu. Değişiklik veya yeni tanı olmadan aynı başarısız koşu tekrarlanmaz.
