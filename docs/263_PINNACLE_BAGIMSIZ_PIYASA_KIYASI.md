# 2.6.3 — Pinnacle bağımsız piyasa kıyası: yürütme sözleşmesi
6 Kasım 2026 · `experiment/263-toplu-karsilastirma`

## Sabit mühendislik kararı
1. **Pinnacle tekil birincil dış piyasa referansı**; farklı firmayı sessizce Pinnacle diye gösterme.
2. **MS 1/X/2 önce:** Aynı bookmaker'ın aynı maçta eksiksiz üç fiyatı; marj (overround) = fiyatların ters toplamı eksi 1; marjsız ihtimaller = ters oran / tüm ters oranların toplamı. Bu *yaklaşık piyasa tahminidir*, şirketin saklı matematik modeli ya da kesin gerçek olasılık değil.
3. Her bir B/C2/C3/M4 modelini kendi ayrı olasılıklarıyla kıyasla; model seçimi, eğitim, ortalama, resmî S1/S2, A/B/C veya bahis kararı değiştirme.
4. Yalnız **resmen doğrulanmış fikstür, imzalı takım kimliği, aynı ev/deplasman yönü ve UTC başlangıç** eşleşirse kaydı kabul et. İsim eşleşmesinde fuzzy yok; yalnız doğrulanmış takma adlar.
5. Maç öncesinde model kaydı ile oran gözlem süresi arasındaki fark en çok 10 dakika; Pinnacle'ın bookmaker zaman damgası da en çok 10 dakika eskimiş olmalı. En fazla 10 dakikayla T−60 *yaklaşımı*; kapanış oranları ayrı tutulur.
6. Pinnacle 1X2 yoksa/eskimişse karşılaştırma **YOK**, başka bookmaker ile dolgu yok. Sağlam sonuç ölçümü ancak gelecek maçlar bitip orijinal tahminler dokunulmadan skorlandığında yapılır.
7. 6 Kasım Gaziantep–Kasımpaşa ön kayıt SHA'sı ve eski PAS kararı değiştirilmedi. Testler o kaydı yalnız **sentetik fiyatla kopyalamadan** okuyup karşılaştırma fonksiyonunu sınar; yaşanmış piyasa verisi olarak sunulmaz.

## Ücretsiz API: doğru alan adı ve mevcut sınırlama
**Doğru sağlayıcı:** https://the-odds-api.com (TİRELİ). Site ücretsiz Starter paketinde 500 kredi/ay, bütün sporlar ve *çoğu* bookmaker diyor; Pinnacle EU listesinde olsa da ücretsiz planın Pinnacle hakkı **henüz gerçek anahtarla kanıtlanmadı**. Benzer yazımlı `theoddsapi.com` başka bir ticari servistir ve aynı ürün değildir.

Resmî doküman: https://the-odds-api.com/liveapi/guides/v4/ .
`bookmakers=pinnacle` ile `h2h,totals` tek bir ligdeki mevcut maçları topluca döndürebilir. 10 lig × 2 market × 1 bookmaker/region eşdeğeri = en fazla 20 kredi **tek tam tarama**. Kullanım hakkı API header'ından rapora kaydedilir, ancak bu testlerin canlı kota beyanı değildir. Hata 401/403/429 olduğunda sonraki 9 lige sorguyu tekrarlama ve gereksiz kredi harcama.

## Depodaki kod ve deneme
- `experiments/263/free_bulk_odds_263.py --pinnacle-only --out <path>`: gerçek anahtar varsa tüm 10 ligin **yalnız Pinnacle** fiyatlarını, kaynağını ve gözlem zamanlarını mühürler.
- `experiments/263/pinnacle_market_benchmark_263.py --forecast <locked.json> --bulk <research.json> --out <path>`: ön-kayıt ile aynı zamanlı exact match verisini karşılaştırır; okunur tekil JSON oluşturur. Önceki bahis/karar kaydını değiştirmez.
- `test_pinnacle_market_benchmark_263.py`: sentetik pozitif ve negatif koşulları tek toplu testte denetler. Gerçek fiyat testi değildir.
- `.github/workflows/263-pinnacle-free-once.yml`: **yalnız tek seferlik kullanıcının onayıyla**, en fazla 20 kredi kullanan gerçek veri erişim denemesi. `workflow_dispatch` default branch üzerinde olmadığı için GitHub Actions'ın Run workflow düğmesinde görünmeyebilir. Bunun yerine deney dalına `experiments/263/pinnacle_trial_requests/<benzersiz>.json` dosyasının **sadece yeni eklenmesi** ile bir defalık push tetiklemesi kullanılır; dosya `{"schema":"263_pinnacle_once_request_v1","day_turkey":"YYYY-MM-DD"}` içerir ve o gün Türkiye tarihine eşit olmalıdır. Hiçbir zamanlayıcı YOK. Anahtarın GitHub Actions Secret adı `THE_ODDS_API_KEY`; sohbete anahtar yazılmaz. Bir kaynağa erişim kodu yeşil olsa bile gerçek Pinnacle 1X2 bulunmazsa canlı kabul işi **hatalı** biter ve engel raporlanır.

## Kabul karar kademeleri
- **KOD_HAZIR:** offline testler geçer (Pinnacle erişimi henüz kanıtlanmadı).
- **ERİŞİM_VAR:** ücretsiz anahtar üzerinden Pinnacle'dan en az 1 geçerli, eksiksiz MS piyasası; 403 yok; en az bir ligde fiyat kaynağı/maç ve zaman damgası kontrol edilir.
- **T−60_UYGUN:** önceden SHA-kilitli yeni gerçek B/C2/C3/M4 tahminiyle, aynı maçta 10 dakikalık zaman farkı ve doğrulanmış takım eşleştirmesiyle karşılaştırma kabul edilir.
- **İSTATİSTİKSEL_İSPAT:** aynı maçlarda gerçekleşen sonuçlara karşı ileri dönem Brier/log-loss/kalibrasyon ölçülür; tek maç veya sentetik fiyat tahmin başarısını kanıtlamaz.

Erişim kanıtlanmadan hiçbir zamanlayıcı veya canlı S2 değişikliği devreye alınmaz.
