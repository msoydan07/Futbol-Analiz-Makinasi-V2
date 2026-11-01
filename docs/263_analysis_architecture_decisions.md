# Futbol Analiz Makinası — 2.6.3 Matematik Mimari Kararı

**Durum:** Kod hazır, yalnızca deney katmanı / model başarısı değerlendirmesi BEKLİYOR. **Tarih:** 2026-11-01.

## Kabul edilen matematik ayrımı

1. **C2 — 2.6.3 §6.2 standart ana formül adayı**: Cari sezonun, aynı ligin ve maç gününden **önceki** verilerinden lig ev/deplasman gol referansı; ev takımının iç saha atılan/yenen ve deplasman takımının dış saha atılan/yenen golleri. Önceki sezon yalnızca dört ayrı bağlam için `ρ` ön bilgisi ve sabit `k=5,w=0.5` olarak kullanılır. Önceki sezonda aynı takım/bağlam yoksa `ρ=1`. Her takımın ilgili iç/dış saha bağlamında **en az 4 bitmiş maçı** gerekir; şablonda olmayan 30 cari lig maç şartı eklenmez. Cari sezon referansı sıfırsa veya λ güvensizse tahmin **YOK**. Tam doğruluk/kalibrasyon kanıtlanmamıştır.
2. **C3 — rakip gücü öğrenen alternatif**: Değiştirilmemiş `exp_263_batch.fit_c3` ve `predict_c3`; lig, rakip, ev/deplasman saldırı/savunma etkileri ortak log-Poisson'da birer kez kullanılır. Tarihsel gözlem gerekiyorsa `>=30` maç ve her takımın ilgili bağlamda `>=4` maç. Önceki deneydeki 2026/27 performans kanıtı **retrospektif** ve bağımsız final değildir. Şablonun kanonik ana formülünün yerini **kendiliğinden almaz**. Koda müdahale edilmez.
3. **Gol olasılık hesaplayıcısı**: Aynı normalleştirilmiş Poisson skor matrisinden 1X2, 1X/X2/12, 0.5–4.5 gol, KG Var/Yok, takım gol çizgileri ve doğru skor. Kuyruk olasılığı ayrı korunur; varsayılan matematik üst sınırı `1e-9`. Üretilen `λ±%10` senaryoları yalnızca **sezgisel duyarlılık**; istatistiksel güven aralığı değildir. Dixon–Coles hesaplanmadan ismi modele eklenmez.
4. **İlk yarı golü**: İlk yarı atılan/yenen geçmiş gol sayılarıyla **tamamen ayrı** ridge-Poisson sayım modeli. `ilk yarı = maç sonu λ / 2` yapma. ≥40 kullanılabilir tarihsel ilk-yarı maçı, her takımın bağlamında ≥4 maç; eksikte `INSUFFICIENT_MARKET_DATA`. Geçmiş **ilk yarı takım modeli daha önce lig baz çizgisini geçemediğinden**, yeni adayı asla geçerli/kalibre diye sunma: `EXPERIMENTAL_NOT_VALIDATED`. Çizgiler 0.5,1.5,2.5, KG ve ilk yarı MS.
5. **Maç sonu korner**: Gollerle **aynı λ'yı kullanma**. Ev/deplasman korner sayılarına ayrı Ridge sayım eğrisi; aşırı saçılma için geçmiş korner artıklarından moment tabanlı NB/Poisson. Kornerlerin doğal sayım aralığı 5 gollük sınırla kırpılmaz; matematik toleransı ayrıca denetlenir. ≥40 korner gözlemi ve bağlamda ≥4; eski korner örnek modeli geçmişte kaybetti, bu **yalnızca yeni bağımsız adaydır**, `EXPERIMENTAL_NOT_VALIDATED`.
6. **Veri kalite kapısı**: 4.413 maçlık 10 lig, 2 sezon kabul snapshot'ı; `sha256=35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`. Sadece 1X2 için gereken zorunlu satırlar yanlışsa dur; yarı/korner eksik veya mantıksızsa ilgili pazarı karantinaya al ama geçerli maç sonu golünü kaybetme. Şut alanları modelde kullanılmaz (önceki C4 ilave katkı vermedi). xG yalnız önceki ayrı beş lig deneyinin durumunda; şu motorun içine sessizce eklenmez.
7. **Zaman sızıntısı**: `match_date < target_date`, aynı günün TAMAMI dışarıda; maçın kendi sonucu/şutu/korneri hiçbir şekilde girdi olamaz. UTC/TSİ kickoff ayrıntısı henüz bu **offline** katmanda yok. Haricî resmî fikstür / kadro kontrolü bu matematik katmanı tarafından yapılmış sayılmaz; çıktı `fixture_verified=false`, `is_real_match_forecast=false` olarak sabittir.

## Gözlemler ve kilitli mühendislik kararları

- 2.6.3 şablonundaki **4 bağlam maçı şartını** koruduk. Daha önceki karşılaştırma `C2` kodunda ayrıca bulunan `>=30 cari sezon lig maçı` şartı **şablonda yok**; yeni C2'ye aynen kopyalamadık. Bu yüzden eski C2 kapsama/başarı sayılarının yeni mimari C2'yi değerlendirdiğini iddia etmiyoruz.
- C3'ün matematik katsayılarının `Ridge=6` yapısını değiştirmedik. **Daha önce C3 için görülmüş +0.010587 1X2 log-loss retrospektif sinyalini** canlı model onayı kabul etmiyoruz.
- Kornerde sayısal beklentiler gol λ üst sınırına mahkûm edilemez; ayrı 30 korner üst sayım sınırı sadece **geçersiz sayısal uçları reddetme** amaçlı, eski deneyin eşiklerini değiştirmez.
- Yarım ve korner deneysel pazarlarının gerçekten C1/C0 baz çizgisini yenmesi henüz sınanmadı; kullanıcı isteğine uygun olarak burada geriye dönük performans testi **BAŞLATILMADI**.
- Bu çıktı bir maç önerisi değil, **izole yazılım/matematik geliştirme katmanı**. En olası bahis, oran, EV, pilot ve sonuç kaydı **YOK**.

## Doğrulanabilenler / bekleyenler

- **KANITLANDI (yazılım):** Bağımsız sayım dağılımı; gol pazarlarının tek ortak matrise bağlı tutarlılığı; ρ/k/w formülü; dört maçlık asgari bağlam; aynı gün sızıntısı koruması; bozuk 1H/korner karantinası; kalıntı kuyruk hesabı; eğitsel `λ±%10` duyarlılığı. 8 sentetik test geçti. 4.413 satırlık gerçek kabul snapshot'ı salt-okunur şekilde işlendi.
- **KANITLANMADI (tahmin):** C2'nin bu yeni uygulamasının kalibrasyonu, C3'e üstünlüğü, ilk yarı ve korner modellerinin lig baz çizgisini geçmesi; doğrulanmış canlı fikstüre veri bağlanması; şablonun tüm 17 bölümünün uçtan uca çalışması.

### Bir sonraki teknik iş — gerçek maç kayıtları değil

Matematik adaylarını aynı tarih/kesimle kıyaslayan **tek kapsamlı kabul testi** için aşağıdakileri topluca hazırla: C2/C3 maç sonu/HT/korner için aynı maç kapsama ve negatif kontroller; lig ve sezon kırılımı; seçilen yarışmacı için tahmin/kayıp kalibrasyonu; 2.6.3 zorunlu veri kalite kapısı. **Bütün adaylar/protokol önceden kilitlenmeden sonuçları tekrar tekrar deneyerek hiperparametre ayarlama yok.** Başarı gösterilmezse “kanıt yetersiz” ve entegrasyon yok.