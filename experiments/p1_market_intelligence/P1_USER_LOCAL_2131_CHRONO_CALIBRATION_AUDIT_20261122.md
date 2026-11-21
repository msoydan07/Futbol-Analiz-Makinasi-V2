# P1 — 2.131 maçlık kullanıcının yerel iki-sezonlu kalibrasyon raporu

**Tarih:** 22 Kasım 2026. **Dal:** `experiment/p1-market-intelligence-20261121`. **Sadece P1 araştırması**; 2.6.3/M4/C3, maç önü mühürler ve ana dal değişmedi.

## Çalışma kanıtı ve kapsam

Kullanıcının paylaştığı sadece özet `P1_KALIBRASYON_TOPLU_RAPOR.txt` dosyasının SHA-256 değeri: `653c50c53ed861e2d838aa3c5180fdccb6b7e494833e6403876550b1d1dd4859`. **Eğitim 2024/25: 1.065 maç; test 2025/26: 1.066 maç; toplam 2.131.** Eğitim en geç **25 Mayıs 2025**, test en erken **15 Ağustos 2025**. Kaynağın 1xBet olarak tanımladığı maç öncesi kapanış fiyatları için gerçek yakalama zaman damgası bağımsız doğrulanmadı; gerçek ham Excel dosyaları kamu GitHub'a aktarılmadı. Bu veri **kullanıcının yerel programından gelen özet** olduğundan, tek tek 2.131 satır bağımsız incelenmedi.

## Eğitim döneminden öğrenilen pazar bazlı güç/sıcaklık katsayıları

| Model | MS | 2.5 Alt/Üst | KG |
|---|---:|---:|---:|
| P0 | 1.04 | 1.04 | 1.02 |
| P1 | 1.00 | 1.04 | 1.04 |

Üç pazar ayrı ayrı normalize edilir. Hiçbir katsayı test sezonundan öğrenilmedi.

## 2025/26 dokunulmaz test grubunda performans

| Varyant | Ana tercih isabet | Makro Brier ↓ | Makro log-loss ↓ |
|---|---:|---:|---:|
| P0 | 671/1066 (%62.95) | 0.513458 | 0.773906 |
| P1 | 672/1066 (%63.04) | 0.514496 | 0.775335 |
| P0 + eğitim kalibrasyonu | 674/1066 (%63.23) | **0.513380** | **0.773737** |
| P1 + eğitim kalibrasyonu | **675/1066 (%63.32)** | 0.514476 | 0.775304 |

Kalibrasyonun etkileri: P0 ana isabet **+3**, Brier −0.000078, log-loss −0.000169; P1 ana isabet **+3**, Brier −0.000020, log-loss −0.000031. Kalibre P1 yalnız **bir** maç daha fazla ana tercih tuttu, ancak **kalibre P0 daha iyi olasılık proper-score** sağladı. Bunlar küçük farklardır; model üstünlüğü veya kazanç iddiası değildir.

## Kaynak kodu teknik denetimi

Yerel `P1_2_SEZON_KALIBRASYON.py` içinde sezona göre **2024/25 eğitim / 2025/26 test** bölümü, grup başına eğitimde log-loss minimizasyonuyla `p ** t` sıcaklık kalibrasyonu ve ayrı holdout değerlendirmesi mevcut. Ayrıca maç haftası blok bootstrap, lig bazlı proper scoring ve tahmin vs gözlenen oran (reliability) binleri **JSON raporuna** yazılıyor, sadece TXT'ye **yazılmıyor**. 22 Kasım yerel sentetik birim testleri tekrar çalıştırıldı: **4/4 başarılı**.

## Karar ve açık iş

**Üretime aktarım YOK.** Bir sonraki aşama **yeni Excel indirmek değil**, zaten kullanıcının bilgisayarında oluşan `P1_KALIBRASYON_TOPLU_RAPOR.json` dosyasını paylaşması. Bu JSON ham oran veya tek tek maç kaydı içermiyor; lig ayrımını, 2024/25'teki 1.065 kabulün sebebini açıklayabilecek dosya/kabul adetlerini, pazar bazlı olasılık kalibrasyon aralıklarını ve eşleşik hafta-blok güven aralıklarını içeriyor. TXT'den güven aralığı/istatistiksel fark hesaplanamaz. Ancak JSON incelendikten sonra model kullanım kararı verilebilir.

**Gerçek fiyat zaman damgası kaynağın beyanıyla sınırlıdır; iddaa canlı fiyatına birebir genellenemez.**
