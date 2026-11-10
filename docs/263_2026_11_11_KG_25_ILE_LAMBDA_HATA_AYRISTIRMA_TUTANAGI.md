# Futbol 2.6.3 — KG Var, 2.5 Üst ve beklenen gol hata kökeni

**Tarih:** 11 Kasım 2026 (Türkiye). **Aktif araştırma dalı:** experiment/263-toplu-karsilastirma.

## Sonuç: Denetim kuruldu, M4 değişmedi

99 tamamlanmış maçın arşivi 4.518 + 99 = 4.617 olarak kapanmıştı. Eski 6/7/8 Kasım önceden mühürlü üç kohort ve 984 maçlık DC/bivariate testi **yeniden çalıştırılmadı**. Rakip savunması/hücumu M4'te zaten hesaba giriyordu. Yeni rastgele rakip katsayısı veya KG/Üst yüzde düzeltmesi eklenmedi.

**Yeni gözlemci:** research/opponent_goals/prospective_goal_error_attribution_263.py

9 Kasım 2026'dan **itibaren**, yalnız gerçek yeni100 maç önü SHA-mühürlü tahminleri ve aynı maça daha sonra girilen insan teyitli resmî sonuç gözlemlerini işler.

- Gol beklentisi λ: Ev sahibi, deplasman ve toplam golde gerçekleşen eksi beklenen gol sapması.
- KG Var/2.5 Üst: Olayın gerçekten gerçekleşmesi ile maç önü olasılığı arasındaki fark, Brier ve sıfır gol/saçılım kontrolleri.
- Bağımlılık adayı: (ev gol−λ_ev) × (dep gol−λ_dep) çapraz artığı. Bunun sıfırdan farklı olması tek başına bağımsız Poisson'un yanlışlığını ispatlamaz; bağlam veya λ yanlılığı aynı sonucu üretebilir.
- B/C2/C3 ile M4 karşılaştırması **yalnız aynı yeni maçlarda** yapılıyor. Eksik model çıktısı doldurulmuyor.

Gün bazlı bootstrap aralığı için en az **10 farklı gerçek maç günü ve 80 tamamlanmış eşleştirme** gerekir. Daha erken gelen sonuçlar yine betimleyici olarak raporlanır; bu koşul **yeni pilot** veya oyun/bahis izni değildir. Model otomatik olarak değiştirilmez.

## Mevcut maç sonrası iş akışına bağlandı

Aktif deney dalında .github/workflows/263-sabah-new100-postmatch-readonly.yml içine aynı rapor işinin parçası olarak eklendi. Yeni sonuç dosyası GitHub iş akışını tetiklediğinde eski maç sonrası karnesine ek olarak **263-prospective-goal-error-attribution.json** çıktısı üretir. GitHub'ın bir Actions GITHUB_TOKEN push'unda başka workflow başlatmama kuralından ötürü her otomasyon yazmasının otomatik tetiklediği iddia edilmez.

**Başarılı test kanıtları:**
- 13/13 yeni güvenlik testi: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42903289291
- Aktif deneyde 17/17 mevcut + 13/13 yeni test ve salt okunur rapor SUCCESS: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42903695311
- Sabah offline entegrasyonu SUCCESS: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42903519852

**Gerçek veri durumu:** 10 Kasım 2026 21:18 UTC kontrolünde 8 Kasım sonrasına ait yeni önceden mühürlü gerçek maç **0**, bunların tamamlanmış sonucu **0**, farklı gün **0**. Yanıltıcı başarı yüzdesi veya model üstünlüğü üretilmedi. İlk gerçek yeni maçların sonuçlarıyla gözlemcinin raporu anlam kazanacak.

**Kesin koruma:** 4.518 eski dosya, 4.617 birleşik skor kaydı, SHA mühürlü eski pilotlar, M4 motoru ve ayar kilidi, üretim main, LITE ve basketbol değişmedi. Bu çalışma araştırma izleyicisidir; otomatik bahsi veya model terfisini onaylamaz. Bir sonraki iş, gerçekten yeni maç öncesi mühür ile sonrasındaki doğrulanmış sonucu aynı SHA'ya bağlayıp rapor okumaktır, eski 99 veya 984 maçı yeniden araştırmak değildir.


## 11 Kasım ek toplu deneme — λ ortalaması ile gol dağılımı birbirinden ayrıldı

- **Kaynak ve yöntem:** M4 ve orijinal 4.617 veri SHA değişmedi. 2025/26 geliştirme sezonunda, eski kilitte zaten sabitlenmiş 3 tarih dilimi × 10 lig üzerinde **701 aynı maç / 41 farklı gün**, tarih kesiti öncesi M4 fit. **2026/27 sezonunun 99 yeni sonucu dahil hiçbir sonucu aday geliştirmede kullanılmadı.** Eski 984 DC/bivariate testi veya 6/7/8 Kasım pilotları yeniden çalıştırılmadı.
- **Başlangıç tahmin–gerçekleşme:** KG Var **%49,72 tahmin / %55,06 gözlem**; 2,5 Üst **%50,28 / %54,21**. Bu farklar tek başına `+5%` otomatik düzeltme için sertifika değildir. M4 mevcut KG Brier **0,254245**, 2,5 Üst **0,257141**, MS **0,600433**.
- **Tek toplu rakip alternatif testi:** λ×0,95 KG/Üst'ü kötüleştirdi; bağımsız negatif binom marjinalleri α=0,10 ve α=0,25 KG'yi belirgin kötüleştirdi. **λ×1,05** adayında aday−M4 Brier: KG **−0,001768**, 2,5 Üst **−0,000959**, MS **+0,000467**. Üç farkın da 41 gün bloklu keşifsel 95% aralığı sıfırı içeriyor. **M4 üretim terfisi veya tahmin yüzdesi düzeltmesi YOK.**
- [701 gerçek geliştirme maçı ve 6/6 matematik testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42909826085). [Tek karar, tablo ve belirsizlik raporu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-goals-marginal-dispersion-20261111/research/opponent_goals/2026-11-11_KG_O25_M4_LAMBDA_VE_NB_TOPLU_KARAR.md).
- **Uygulanan tek ileri araştırma bağlantısı:** Önceden kilitli yeni100 maçlar sonuçlandığında, mevcut `research/opponent_goals/prospective_goal_error_attribution_263.py` kendiliğinden yalnız aynı mühürlü M4 λ'sının **×1,05** sabit adayına karşı KG/Üst/MS Brier farkını *ayrı rapor alanında* hesaplar. **Maç önü dosyasını, kullanıcı yüzdelerini, telefonu, oranları, MS/PAS kararı, mühür SHA'sını, M4 katsayılarını değiştirmez; yeni pilot açmaz.**
- [Aktif GitHub maç sonrası bağlantısı — 17 önceki + 15 yeni = **32/32 test PASS**](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42910428771). Mevcut aktif dalda henüz **0 yeni mühürlü maç/sonuç** var; bu nedenle adayın ileri maç başarısı **henüz ölçülmüş değil**.
- **Bir sonraki bilimsel karar:** Yeni günlerden aynı SHA ile kilitlenmiş gerçek maç ve sonucu geldiğinde λ×1,05'in KG/Üst'e katkısının MS'de anlamlı kayıp oluşturmadan tutarlı olup olmadığını görmek. Eski pilotları/kapatılmış 99 skor arşivini yeniden başlatmak yok.
