# Futbol Maç Analiz Makinası 2.6.3 — 4 Kasım 2026 tek kaynak durum defteri

## Hedef (değişmedi)
10 ligde geçmiş maçlardan kurulan B/C2/C3/M4 sistemini **maç başlamadan kaydedilen, değiştirilemeyen tahminlere**, tek ana aday / farklı aileden alternatif / PAS kararına ve maç bittikten sonra gerçek performans ölçümüne bağlamak. Yalnız kullanıcının maç adıyla istediği maçlarda, canlı resmî fikstür kontrolüyle ilerle. Otomatik maç keşfi yok.

## Gerçekten tamamlananlar
- 10 lig kimlik eşleşmeleri ve mühürlenmiş 4.413 temel arşiv; 4.501 staged veri (+88) ve GitHub Actions [#41802358251](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41802358251) içindeki 4.509 veri artifact'ı (+8). **Artifact mevcut olması, resmî insan kaynak kabulü değildir**.
- 880 geçmiş dönem yeniden kurulmuş model tahmininin keşif amaçlı kıyası; 587 geliştirme dönemi kalibrasyon kilidi ve 293 Ekim araştırma değerlendirmesi. Gerçek değiştirilemez maç öncesi sonuç ölçümüyle karıştırma; eski maçları tekrar çalıştırma.
- B/C2/C3/M4 tahmin akışı; ana aday, farklı pazar ailesinden alternatif ya da PAS; 1.5 Üst'e sırf yüksek ham olasılıktan ötürü öncelik verilmez. Oran/EV/ROI **henüz doğrulanmamış**, bahis ve resmî S1/S2 yetkisi yok.
- 88 sonucun CSV/referans eşleşmesi; 72 kayıt için [dış kaynak denetim raporu](263_2026_11_04_72_external_score_audit.md), diğer 16 için referans denetimi; 2 Kasım'ın 8 sonucuna [çapraz kontrol raporu](263_4509_veri_8_mac_capraz_kontrol_2026_11_04.md). Dış skor kıyası tam 4.509 satırın insan kabulü anlamına gelmez.
- 31 Ekim SC Cambuur 4–0 Go Ahead Eagles: erken tatil ve resmî kesinleşmiş skor kaynakta korunur; 90 dakika eğitim ve lig bazlı pazar oranlarından SHA-256 mühürlü istisna filtresiyle çıkarılır. [16 hedefli test yeşil](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41851081895).
- **Son düzeltme (2ef98d4)**: lig bazının sonradan hesaplandığı zaman eskiden tahmin saati gibi kayda geçiyordu. Artık gerçek hesaplama zamanı yazılıyor; baz en fazla 10 dakika sonra ve kesinlikle KO öncesinde oluşturulabilir, eski zamana mühürlemek veya sonraki sonuçları kullanmak engellenir. Eski baz v1 yerine güvenli v2 kullanılır. [Lig baz testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41852718420), [kaynak/zaman kilidi testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41852718384) ve [tek toplu uçtan uca kabul](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41852718419) **başarılı**.

## Güncel kesin engeller
1. **İnsan kaynak kabulü yok:** `data/quad_accepted_263/` yaratılmadı, `HUMAN_VERIFIED_SOURCE_ACCEPTANCE` üretilmedi; 4.509 güncel paket artefact'ı insan tarafından dosya/kaynak seviyesinde incelenip dürüstçe onaylanmalı. İmza, reviewer, zaman damgası ve SHA uydurma. Doğrulama tamlanmazsa gerçek ileri kayıt **PAS/BLOCKED**.
2. **Gerçek ileri tahmin kaydı yok:** `forward_quad_263/` boş; resmî 100 maçlık pilot etkilenmedi. Kullanıcı maç ismini verince güncel resmî fikstür + T−60 koşulları + kabul edilmiş veri ile gerçek KO-öncesi kayıt gerekir. İlk 11 açıklanmadıysa ön analizi durdurma.
3. **Sonuç sonrası ileri performans kanıtı yok:** Yapay testlerin yeşil olması yüksek tahmin isabeti veya pozitif ROI garantisi değil.

## DÖNGÜ KİLİDİ
Yeni modül, ikinci şablon, tekrar 880 hesaplaması, gereksiz yeniden kalibrasyon, maç uydurma, otomatik kabul, sahte saat damgası **yok**. Bir sonraki iş **yalnızca 4.509 veri paketinin kaynak kabulü / eksik gerçek kaynak incelemesi**; bunun dışında aynı kodu yeniden test etme. Ardından kullanıcı tarafından adlandırılan ilk gerçek maçta tek KO-öncesi tahmin kaydı ve daha sonra sonuç ölçümü. Her adımda yalnızca yeni, ilgili ve tek kabul kanıtını sakla.

**Şimdiki hüküm:** Mühendislik prototipi hazır ve son bütünleşik kapılar yeşil. Gerçek maç öncesi ileri pilot **henüz aktive edilmedi**. Üretim dalı ve resmî 100 maçlık pilot değişmedi.
