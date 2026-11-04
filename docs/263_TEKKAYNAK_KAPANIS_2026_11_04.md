> **4 Kasım 2026 — SAHİP ONAYI / NİHAİ KAYIT (önceki durum notlarının yerine geçer)**
>
> - Kullanıcının açık **“4518 ONAYLIYORUM”** mesajı, **2026-11-04T15:43:42+00:00** onay zamanı ve `msoydan07` inceleyici kimliğiyle `data/staged_263/owner_approval_4518.json` dosyasına kaydedildi.
> - **Tek koşuluk kabul başarıyla tamamlandı:** [GitHub Actions #41860849189](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41860849189). `data/quad_accepted_263/extended_history.csv` ve `data/quad_accepted_263/source_acceptance.json` GitHub üzerinde mevcut. Kabul edilen dosya SHA-256: `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`; 4.518 satır, 42 kaynak bağlantısı. Eski 4.413 satır değişmedi.
> - Onay kapsamı: **sahibin kanıt raporunu ve açıklanmış sınırlamaları kabul ettiği deneysel araştırma kullanımı**. 4.518 sonucun tamamının bağımsız doğrulandığı iddia edilmez; `source_acceptance.json` bu sınırı **false** olarak açıkça işaretler. Otomatik insan onayı veya kaynak kontrolü icat edilmedi.
> - **Henüz pilot tahmin yok**: `forward_quad_263/` oluşturulmadı. Sonraki adım yalnız kullanıcı tarafından isimlendirilen maç için gerçek resmî fikstür ve KO-öncesi doğrulama, mühürlü dört-model kayıt; gelecekte geçmişe dönük kayıt üretmek yasaktır. İlk 11 eksik diye ön analiz durdurulmaz.
> - Mühendislik karşılaştırmaları, M4 ayar kilidi ve resmî 100 maç pilotu **değişmedi**. Aynı başarılı kabul testini tekrar çalıştırma.
>
---

> **04.11.2026 — GÜNCEL DURUM KONTROLÜ / DÖNGÜ KİLİDİ**
>
> - Yeni araştırma veri paketi: **4.518 maç**, 4.509'luk sabit SHA snapshot'a 3 Kasım Championship sonuçlarından **9 maç eklendi**. Çalışma [#41854694583](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41854694583) başarılı; çıkarılan ZIP içinde `extended_history.csv` ve `stage_report.json` mevcut. SHA-256 **`1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`**. Önceki 4.509 satır **bire bir değişmeden korunmuş** ve toplam kimlik sayısı tekil. Kaynaklar: [Football Web Pages](https://www.footballwebpages.co.uk/championship/fixtures-results/november), [Soccerway](https://www.soccerway.com/england/championship/results/), [Cornerflick](https://cornerflick.com/football/leagues/championship/results), [EFL](https://www.efl.com/news/2026/november/04/Sky-Bet-Championship--Birmingham-rise-to-second-as-Pompey-shock-Swansea/).
> - 9 yeni satır **STAGED_CROSSCHECKED_NOT_HUMAN_ACCEPTED**. Olası olmayan kaynak verisi yazılmadı; futbol-data sağlayıcısının bilinmeyen `source_row` numarası, ilk yarı / şut / korner istatistikleri boş. Bu paket **`data/quad_accepted_263` değildir**, ücretli/bahis/resmî pilot onayı yoktur.
> - İlk gerçek ve değişmez erken karşılaşma gölge kaydı: `forward_quad_shadow_263/2026-11-06/1d6b6f16fef8bac971c184c4.json` (Gaziantep FK–Kasımpaşa, resmî fikstür kapısı doğrulanmış, dört model mevcut, 4 Kasım KO öncesi). **EARLY_SHADOW_UNVERIFIED** statüsü değişmez; resmî pilot kaydı yapılmaz.
> - **Eksik ve kullanıcı yerine uydurulamayacak durum:** açık ve gerçek `HUMAN_VERIFIED_SOURCE_ACCEPTANCE` belgesi yok; yeni veri için dürüst kaynak incelemesi/onayı ve maçın T−60 resmî kayıt koşulları sağlanana dek `forward_quad_263/` boş kalır. 4 Kasım akşamında oynanacak maç sonuçları henüz mevcut değildir; gelecekten veri eklenmez.
> - Yalnız bu veri açığı giderildi; B/C2/C3/M4, 880 geçmiş maç, DEV kalibrasyonu ve üretim kodları **yeniden test edilmedi / değiştirilmedi**. Önceki 16-test kabulü ve as-of güvenliği yeşildir. **Başka yeni model/modül ekleme yok.**
>
---

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
