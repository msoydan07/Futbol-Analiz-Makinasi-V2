# 2.6.3 — 7 Kasım 2026 | Pinnacle T-60 oran karşılaştırma entegrasyon kararı

Deney dalı: experiment/263-toplu-karsilastirma. main değişmez.

## Önceden kanıtlanan oran temeli

The Odds API üzerinde bookmaker=pinnacle ve h2h (MS1/X/2). 6 Kasım 2026'daki gerçek sorgu GitHub Actions 42272882870, 1 kredi harcandı, 499 bakiye raporlandı. 7 Kasım Premier League dört fiyatı o günün erken piyasa arşividir; bugünkü T-60 fiyatı değildir.

## Yeni100 ana analize bağlanan sıralama

1. Açıkça istenmiş yeni maç, resmî maç/kanonik takım ID kontrolü, geçmiş araştırma veri SHA ve B/C2/C3/M4 model hesabını geçer. En az üç model AVAILABLE, C3/M4 zorunlu.
2. Ana yeni100 forecast, geçmiş baz oranları, dondurulmuş DEV kalibre/PAS kararı, telefon raporu ve SHA receipt GitHub'a append-only olarak push edilir. Pinnacle, bu eski kararı ve pilot sayacını değiştiremez.
3. Aynı GitHub job içinde fiyat araştırma planı mühürlü forecast SHA/receipt, bugün Türkiye günü, tahmin yaşı <=10 dakika, KO'ya 20–90 dakika ve daha önce rezervasyon bulunmamasını kontrol eder. 10 lig için maksimum 10 h2h sorgu, lig başına günde 1.
4. API secret yoksa rezervasyon/istek yok ve fiyat yok açıkça gösterilir. Mevcut rezervasyon varsa yeni istek yok. Uygunsa kredi rezervasyon dosyası önce commit+push edilir; uzak GitHub branch üzerinde doğrulanır. Ardından yeni zaman/KO prequery testi yapılır. Yalnız geçerse The Odds API'ye tek Pinnacle h2h çağrısı yapılır. Hata/boş yanıt yeniden sorgulanmaz; günlük slot tüketilmiş kalır.
5. Sağlayıcı JSON'un tamamında Pinnacle kimliği, resmî fikstür ev/deplasman ID, kickoff UTC, üç fiyat, overround, tahmine/yanıta 10 dakika tazelik, piyasa update <=10 dakika aranır. Bir başka bookmaker asla Pinnacle diye sunulmaz.
6. Önceki karşılaştırıcı B veya C2'nin eksikliğini impute etmeden C3/M4 + en az üç AVAILABLE modeli kabul eder. Ham model olasılıkları ayrı, marjsız yaklaşık Pinnacle pazar olasılıkları ayrı yazılır.
7. Yeni salt-okunur model-kalibrasyon kıyası, orijinal mühürlü RESEARCH_PAS kararındaki güvenilir C3/M4 destekli MS1/MSX/MS2 kalibre q olasılıklarıyla fair-market olasılığı yüzde puan farkı üzerinden karşılaştırır. Yetersiz destek -> veri yok. Ayrı senaryo EV bir bahis önerisi, değerli seçim, S1/S2 onayı veya model değişikliği değildir.
8. API sonucunun SHA dosyası, yeni bağımsız karşılaştırma JSON ve telefon Markdown'ı yalnız ADD şeklinde Git'e yazılır. Fiyat kaynaklı yeni100 pilot kaydı, karar revizyonu, gizli key sızıntısı ve geçmişe dönük piyasa doğrulaması yapılmaz.

## Sınırlar

Bugünkü 44 maçlık önceki araştırma koşusu 0 Pinnacle API çağrısıyla tamamlandı. O çalışmanın araştırma olasılıkları, 6 Kasım erken piyasa fiyatına geriye dönük bağlanmaz. Yeni100 asıl pilotunda en son 0/100 kayıt vardı; bu entegrasyon canlı T-60 eşleştirme kanıtı değildir. İlk gerçek yeni100 kullanıcı maçı T-60 penceresinde mühürlenene ve gerçek Pinnacle snapshot alınıp aynı anda karşılaştırılana kadar entegrasyonun canlı fiyat kolu KANIT BEKLİYOR olarak kalır.

Sabah yeni100 girişi yalnız TSİ 05:00–12:59 kabul eder. Maç saatine uzak sabah analizlerinde T-60 şartı sağlanmıyorsa 0 kredi harcanır; bu bilinçli güvenlik sınırıdır. Oran toplama otomasyonunun sonraki geliştirilmesi, gerçek T-60 anında aynı job içinde yeni analiz gerektirebilir. Var olan eski quad_forward ve Pinnacle araştırma workflow'larına API secret eklenmedi. 96 pilot, üç mühendislik kabul kaydı, ana 100 pilot ve main korunur.

## Kod kanıtı
- .github/workflows/263-sabah-new100-on-request.yml
- experiments/263/sabah_pinnacle_new100_bridge_263.py
- experiments/263/sabah_pinnacle_credit_guard_263.py
- experiments/263/sabah_pinnacle_capture_263.py
- experiments/263/pinnacle_market_benchmark_263.py
- experiments/263/test_sabah_pinnacle_new100_bridge_263.py
- .github/workflows/263-sabah-offline-components.yml
