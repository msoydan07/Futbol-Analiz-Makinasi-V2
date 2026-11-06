# 2.6.3 — Pinnacle aynı çalışmada T−60 bağımsız piyasa karşılaştırması

6 Kasım 2026 · Kullanıcı tarafından onaylanan iş akışı. **İddaa oranın yerini otomatik olarak almaz.**

## Sabit mühendislik kararı

- Kullanıcı yeni bir maç/dörtlü tahmin istediğinde, B/C2/C3/M4'ün SHA ile kilitlenmiş ileri tahmin kaydı oluşturulur; **mevcut tahmin ve S1/S2 kararları değişmez**.
- Bir bağımsız araştırma adımı, yalnız maç başlangıcına **20–90 dakika kalmış** ve en fazla **10 dakika önce** kaydedilmiş tahminler için The Odds API'nin **Pinnacle** MS 1/X/2 fiyatını sorgular.
- **Bir ligde birden çok maç varsa aynı çalışma/gün için yalnız bir h2h lig sorgusu** yapılır; başka bookmaker asla Pinnacle diye sunulmaz.
- Her lig sorgusu için üst sınır yaklaşık **1 API kredisi**; tek kullanıcı isteğinde 10 ligin tümü varsa en fazla 10 kredi sorgulanır. Hata varsa otomatik tekrar yapılmaz.
- Tam karşı fiyatlar, doğrulanmış ev/deplasman kimliği, doğru UTC başlangıç, fiyatın tahmine en çok 10 dakika uzaklıkta olması ve sağlayıcıdaki market güncellemesinin en fazla 10 dakika eski olması zorunludur.
- Marj (overround) = üç ters fiyatın toplamı − 1. Piyasanın yaklaşık marjsız MS olasılığı = her bir ters fiyatın bu toplama bölünmesi. Bu, Pinnacle'ın iç matematik modelinin kesin çıktısı olarak gösterilmez.
- Dört modelin ayrı MS olasılıklarıyla kıyas hesaplanır; modellerin ağırlıkları, kalibrasyonu veya bahis kararı değiştirilmez.
- Oran bulunamazsa «Pinnacle kıyası yok» nedeni kaydedilir. **Model tahmini, açıklayıcı pazar yüzdeleri ve bahis için PAS kararı korunur.**

## GitHub dosyaları

- experiments/263/free_bulk_odds_263.py: özgün toplu kaynağın **seçili lig + seçili h2h pazarı** destekleyen, ücretsiz kotaya duyarlı hali.
- experiments/263/pinnacle_forward_join_263.py: yalnız **aynı çalışmada yeni ve mühürlü** tahminleri Pinnacle'ın taze verisiyle eşleştiren salt-okunur bağlayıcı.
- experiments/263/pinnacle_samejob_runs/<istek_SHA>.json: maç başına durum ve varsa engel nedeni.
- experiments/263/pinnacle_samejob_bulk/<istek_SHA>_<tarih>.json: sağlayıcı kaydı ve SHA.
- experiments/263/pinnacle_samejob_comparisons/<tarih>/<maç_id>.json: dört model ile Pinnacle marjsız olasılık kıyası; bahis onayı değil.
- .github/workflows/263-quad-forward-on-request.yml: ayrı yeni maç talepleri için aynı koşuda fiyat ve model bağlayıcı. Yalnız talep dosyası eklendiğinde tetiklenir; **yeni otomatik tarama takvimi kurulmaz**.

## Geçmiş gerçek fiyat kanıtı

6 Kasım 2026 tarihli ilk API bağlantısı başarılıdır: GitHub Actions 42272882870, bir Premier League lig sorgusu, 7 Kasım için dört maçta tam Pinnacle 1/X/2, 1 kredi, kalan 499. O ilk snapshot ön maç günü akşamından gelmiştir; **T−60 değildir** ve sonradan 6 Kasım'daki Willem II–PEC Zwolle veya Gaziantep–Kasımpaşa tahminlerine bağlanamaz.

Orijinal artifact:
https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42272882870/artifacts/13530770750

İlk gerçek provider snapshot SHA-256: 9d108a5f91441071f6c4c3e102725c3d88ac4bfb6b681ba3e3dca478c6b2fe2b.

## Kabul kapısı

1. Bir **tek toplu sentetik test** ile modelin değişmemesi, kaynağın tek lig sorgulanması, 10-dakikalık tazelik, PAS'ın korunması ve eksik veri/anahtar durumları kontrol edilir.
2. İlk **gerçek yeni T−60 dört model + Pinnacle** aynı-zaman başarılı kaydı görülmeden bu entegrasyon canlı sahada doğrulandı sayılmaz.
3. Gerçek maç sonuçları sonradan aynı maç kümesinde Brier/log-loss/kalibrasyonla ölçülür. Tek maç veya tek pazar yüzdesi üstünlük kanıtı değildir.
4. Oran sağlayıcısı verisi Pinnacle'ın doğrudan sitesinden bağımsız tekrar doğrulanmış değildir; sağlayıcı gecikmesi yaşanabilir.

Kaynak dokümanı: https://the-odds-api.com/liveapi/guides/v4/ ve https://the-odds-api.com/sports-odds-data/bookmaker-apis.html .
