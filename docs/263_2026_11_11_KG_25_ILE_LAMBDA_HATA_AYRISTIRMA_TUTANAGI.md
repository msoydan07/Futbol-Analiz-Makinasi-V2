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
