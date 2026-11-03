# Futbol Maç Analiz Makinası 2.6.3 — 3–5 Kasım UEFA / AŞAMA 6 TEK TOPLU MATEMATİK ÖN KABULÜ

**Tarih:** 3 Kasım 2026, Türkiye saati.  
**Durum:** **17/17 maçta iki ayrı matematik yolu bellek içinde kontrol edildi; olasılık/kazanan/λ dosyası üretilmedi.** Yalnız yazılım ve hesap güvenliği kabul edildi, tahmin kalitesi veya canlı maçta bahis onayı verilmedi.

## Kanıt ve tek koşu
- GitHub Actions **41592763161**: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41592763161 — **SUCCESS**.
- Aynı çalışma içinde **14/14 odaklı güvenlik/matematik testi PASS**.
- GitHub Actions artifact **13211220955**, adı \`263-uefa-17-stage6-math-preflight-NO-PREDICTIONS\`.
- Artifact sadece \`math_preflight_audit_NO_PREDICTIONS.json\` içeriyor; SHA-256 **dea2fa1cb24d415e8e23dba37dff7c54132258af1150845e4fa5d498541dedf3**. Dosya açılıp incelendi: **maç bazlı lambda, maç bazlı yüzde, maç tercihleri, gol/skor tahmini YOK**.
- Yeni kod \`experiments/263/europe/uefa_nov3_5_stage6_shadow_math_preflight_263.py\`, 14 odaklı test \`test_uefa_nov3_5_stage6_shadow_math_preflight_263.py\`. **Orijinal \`uefa_elo_m0_paired_retrospective_263.py\` fonksiyonları aynen import edildi.**

## Donmuş üç kaynak, yeni ağ isteği veya veri toplama YOK
1. Aşama 4: gerçek 2026/27 dokuz lig gol profili ve gol kaynağı anı. GitHub run \`41590323827\`; birebir kaynak raporu SHA-256 \`56e3210d425aeaa6b2a7bfc9d3244a0ae644b7a55b6c133308406a4647cb4c97\`.
2. Aşama 5: Elo + RD + haber kaynak seviyeleri. GitHub run \`41591598226\`; SHA-256 \`6b4aa434357fdd9b75d0f6c0f3e730b48dec6e7dec1cf6266c7d328d1ce45c5c\`.
3. Önceden tek kez ölçülmüş **retrospektif** 124 maçlık model kıyası. GitHub run \`41586786116\`; SHA-256 \`03c1b1fea46bcf941ad1271a0fe6fb0d536df8dcff9d2182a30bca91b7cdff17\`.

Bunların GitHub artifacts dosyaları yalnızca **indirildi ve SHA ile doğrulandı**; dondurulmuş geçmiş maçlar yeniden eğitilmedi, Elo sağlayıcısı veya 9 lig dosyaları yeniden indirilmedi. Önceki 3. aşama UEFA 17'li maç kimliği dosyası da ev/deplasman, 17 resmî maç ID'si, tarih ve turnuva çapraz kıyasına dahil.

## İki gölge matematik yolu

**M0 (Elo'suz başlangıç):** takımın kendi ligi içindeki konum-özel ev/deplasman atılan/yenilen gol oranları ve **k=5 yumuşatma**; UEFA eski araştırma eğitim grubunun sabit tabanları \`135/76≈1,776316\` ev golü/maç ve \`101/76≈1,328947\` deplasman golü/maç. Sabit beklenen gol aralığı \`[0,15;5,00]\`. Farklı liglerin ham gol ortalamaları doğrudan mutlak takım gücü sayılmaz.

**M0+Elo (YALNIZ TEKNİK GÖLGE):** aynı M0 ve **tek sabit, henüz onaysız** Elo farkı \`d=clip((home_elo−away_elo)/400,-2,+2)\`; tarihsel denemenin tek başına eğittiği **β=0,5254760017675575** ile \`λH=clip(λH_M0×exp(βd))\` ve \`λA=clip(λA_M0×exp(-βd))\`. Ek lig/UEFA ülke katsayısı, sakatlık, kadro, rakip PPG, xG veya H2H **bu formüle katılmadı**.

Bunlar iki **gölge araştırma modeli**; hiçbiri onaylı yerel B/C2/C3/M4 motorunun yerine geçmez. Retrospektif katsayı eğitim kaynağının gerçek zamandaki ilk görülme kanıtı eksikti; bu sorunu tek seferlik matematik testi çözmez.

## 14 tek seferde başarılı güvenlik denetimi

1. 17/17 UEFA maçının 34 ayrı takım kimliği, tarih/turnuva/girdi yolu doğru; 6 Salı, 6 Çarşamba, 5 Perşembe.
2. Her maç için **iki** ayrı modelin iki beklenen gol oranı ve 1X2, 2,5 Üst, KG olasılıkları **yalnız bellek içinde** hesaplandı. 1X2 olasılıklarının toplamı 1; maksimum toplama hatası **2,22×10⁻¹⁶**.
3. Olasılıklar [0,1], matematik sonlu ve beklenen gol değerleri önceden belirlenmiş [0,15;5,00] sınırlarında. Girdi rol ve lig normalizasyonu, önceki tek deneyin formülüyle aynı.
4. Kaynak SHA bozulursa, sabit katsayı/değerler değiştirilirse, kanıtsız Elo ağırlığı "onaylandı" yapılırsa, kulüp ID'leri eşleşmezse, maç başlama sonrası veri veya aynı gün sonuçları girerse, hesap kapanıyor.
5. Sakatlık listesi değiştiğinde matematik çıktısının değişmediği ayrı test edildi: haberler onaysız λ katsayısı haline getirilmedi.
6. Aynı Elo puanına sahip iki takım için Elo farkı sıfırlanınca M0 ve M0+Elo beklenen gol hesapları eşit.

**Koşu zamanı:** 3 Kasım **06:53 UTC / 09:53 Türkiye**, ilk UEFA maçı 17:45 UTC / 20:45 Türkiye başlamadan önce. Matematik **tüm 17 maçın ilk başlama saatinden önce** denendi. Ayrıntılı tek maç çıktıları RAM'den sonra silindi; kalıcı tahmin kilidi/sonuç defteri oluşturulmadı.

## Kesin sınırlamalar ve mühendislik kararı

- **AŞAMA 6: YAZILIMSAL GÖLGE MATEMATİK HAZIRLIĞI TAMAMLANDI.** Bu, onaylı tahmin modeli değil; doğru kalibre edilmiş canlı 1X2 ihtimali veya istatistiksel başarı raporu DEĞİLDİR.
- **17 gerçek maç tahmin kaydı: sıfır.** Matematik ön kontrolü sadece özet istatistik ve kaynak kanıtını kaydetti. Önceden kaydedilmiş 2025/26 retrospektif çalışması, gerçek 2026/27 pilot örneği değildir.
- **main, mevcut on lig, B/C2/C3/M4, 17 bölüm, A/B/C, 100 maç pilot, oran/EV:** değişmedi.
- **Aşama 7:** tek toplu kalite ve arayüz denetimi. Özellikle tarih blokajı, 1X2/2,5/KG formülleri, örneklem, kaynaktan futbol bağlamı ve *tahmin kaydını açmama* durumu son kez kontrol edilecek. **Aşama 8** tahmin kilidi, yalnız kullanıcı talimatıyla ve maç başlamadan önce ayrı yetkilendirme ile açılacaktır.

**Kural:** Kaynak değişmedikçe bu 14 test ve eski 124 maç testi tekrar edilmeyecek. Gerekli yeni denetimler bir sonraki aşamada toplu ve önce tanımlanmış şekilde yapılacak.
