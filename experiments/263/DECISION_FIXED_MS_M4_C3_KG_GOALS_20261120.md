# 20 Kasım 2026 — Dondurulmuş M4/C3 ailesel karar politikası

## Uygulanan mühendislik kararı
- **MS1/MSX/MS2:** tüm üç sonuçta **tek M4** uzmanı (M4 yoksa C3), as-of DEV kalibrasyonunun pozitif-skill MS sonuçları arasındaki **en muhafazakâr ortak ağırlığı** ve aynı tam MS geçmiş frekansı vektörü. Böylece toplam matematiksel olarak **%100**. Piyasa odds veya tek sonuç bazında model değiştirilmez.
- **KG Var/Yok:** **C3** uzmanı (C3 yoksa M4), ikili tamamlayıcılık zorunlu.
- **Gol 1.5/2.5/3.5 Alt/Üst:** **C3** uzmanı (C3 yoksa M4); tüm çizgilere aynı uzman ve ortak DEV ağırlığı; gol çizgisi sırası ve tamamlayıcılık doğrulanır.
- **Yetersiz gelişim Brier becerisi**, 3 model desteği, olasılık/lift, geçerli odds, EV ya da marjsız fiyat avantajı gibi eski kapıları **gevşetmeyiz**. O pazarda modelin ham yüzdesi tanı amaçlı görünür, fakat güçlü kanıt yoksa **PAS**.
- 96 eski mühür, 8 Kasım 40 SHA mühürü, C2/B/C3/M4 tahmin formülleri, eski json kararları, xG, lig sayısı ve `main` kolu değişmez. Bir karar değişikliği yalnız **yeni tahmin kararlarında** çalışır. Yeni tarihsel pilot başlatılmaz.

## Kararı yönlendiren karşılaştırma
- 293 Ekim maçında C3 MS 0.582332 vs M4 0.585542 Brier; C3 KG 0.246751 vs M4 0.248779; C3 2.5 0.247089 vs M4 0.249303.
- 8 Kasım **39 eski mühür** skorunda M4 MS 0.509959 vs C3 0.517322; C3 KG 0.246367 vs M4 0.248164; C3 2.5 0.247555 vs M4 0.262744.
- Dinamik geçmişe bakan meta seçici bu iki ölçümde de MS'nin sabit uzman seçimini geçmedi (Ekim sabit 0.585542/dinamik 0.586019, Kasım sabit 0.509959/dinamik 0.511454). Bu nedenle meta **aktif değil**, bkz. araştırma PR #18.
- Bu iki zaman aralığında MS üstünlüğü net değildir; M4 MS seçimi yalnız sabit bir **operasyonel araştırma tercihi**, kanıtlanmış kesin zafer değildir. Geçmiş skorların bazıları insan/web araştırmasıyla kayıtlı, tümü bağımsız ağ doğrulamalı değildir.

## Güvenlik ve sınırlar
- Tüm eski odds/EW/PAS/3 model/0.60/geliştirme becerisi eşikleri korundu.
- Kodu değiştirmeden önce ayrı araştırma kolunda yeni testler + eski 8 test çalıştırıldı; 40 gerçek SHA-kayıt **yalnız bellekte yeniden değerlendirildi**: 40/40 M4 MS %100, C3 KG/gol, gerçek piyasa fiyatı yokken 40/40 PAS, eski dosyalarda değişiklik yok.
- Kullanılan `conservative_dev_family_weight`, mevcut frozen Aug-Sep kilidindeki **pozitif-skill** pazarlardan hesaplanır; yeni model refit, yeni öğrenilmiş parametre veya gömülü bahis seçimi değildir.
- Tarihsel Brier farklarının küçük olması sebebiyle canlı başarı artışı veya kâr **iddia edilmez**.
- **Açık engel:** `forward_quad.py` içindeki 10 günlük son lig sonucu tazelik kapısı değişmedi. Milli maç arası diye veri olmadan kapıyı 20 güne çıkarmayacağız. Maç gününde uygun resmî ara/sonuç kanıtı olmadan sistem güvenli şekilde tahmini engeller; bu, diğer sıradaki bağımsız mühendislik işidir.

## CI / uygulama
- Sabit uzman korumaları: `experiments/263/test_fixed_specialists_263.py`.
- Önceki SHA'lar read-only: `experiments/263/verify_fixed_specialists_existing_40.py`.
- CI: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44620177779
