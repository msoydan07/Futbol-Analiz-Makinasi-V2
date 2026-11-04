> **4 Kasım 2026 / 6–8 KASIM GERÇEK VERİ ÖN KONTROLÜ — YEŞİL**
>
> - Kabul edilmiş **4.518 maçlık SHA'lı dosya**, 10 lig için gerçek kaynak dosyası olarak okundu; 6, 7 ve 8 Kasım'ın her biri için tarihsel örneklem eşiği ve **10 günlük azami veri yaşı** uygun. [GitHub veri ön kontrolü #41905205159](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41905205159): **5/5 test başarılı**, (10/10) lig ve (30/30) lig-gün penceresi mekanik veri yönünden hazır. [JSON denetim artifact'ı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41905205159#artifacts).
> - Eski Hollanda tatil edilmiş maç skor kaynağında korunuyor ama **1 satır 90 dakika model eğitiminde hariç**; böylece NED1 405 kaynak / 404 eğitim satırı. ENG2 717 kaynak / 717 sonuç satırı; 3 Kasım tarihli 9 kaydın `source_row`, korner ve başka bazı ek alanları boş, uydurulmadı. Hiçbir ligde sonuç URL alanı boş değil.
> - **Sınırlama:** Bu denetim gelecekteki **resmî fikstürü, kadroyu, maç günü alınacak fiyatı veya 4.518 skorun tamamını bağımsız yeniden doğrulamaz**. 5 Kasım ve daha sonra tamamlanan maç sonuçları varsa gerçek T−60 anında yeni kaynak kontrolü şarttır. Bu yalnız veri ön hazırlığıdır; resmî 96/100 ileri pilot kayıt sayısı hâlâ **0**.
> - **Canlı oran araştırması:** [iddaa program sayfası](https://www.iddaa.com/program/canli) taranabiliyor ama otomatik güvenilir tam karşı fiyatların alındığı kanıtlanmadı. [The Odds API](https://the-odds-api.com/liveapi/guides/v4/) etkin bir anahtar isteyen bağımsız piyasa veri servisidir; [bookmaker listesi](https://the-odds-api.com/sports-odds-data/bookmaker-apis.html) aynı iddaa/Nesine oranlarını garanti etmez. **Bu nedenle ücretli/yeni sağlayıcı otomatik eklenmedi**, mevcut yerli kaynak önceliği korundu. Maçta kaynaktan gerçekten kontrol edilen tam fiyatlar yoksa EV yok ve ana değer kararı **PAS**.
> - GitHub ileri tahmin workflow'u, eş zamanlı değişiklik olursa `git pull --rebase` sonrası **yeniden KO-öncesi SHA ve zaman denetimi** yapacak. Bunun gerçek yarışta başarıyla sınandığı henüz iddia edilmez. Fenerbahçe–Liverpool ve diğer UEFA kilitli iki-model dosyaları değiştirilmedi; eski 880 maç yeniden hesaplanmadı.
>
---

> **4 Kasım 2026 — SON GELİŞTİRME DURUMU / 1.5, 2.5, 3.5 MAÇ SONU ÖLÇÜMÜ**
>
> - **Olasılık ve değer karar katmanı:** B/C2/C3/M4 + 1.5/2.5/3.5 oran çiftleri + ana/alternatif/PAS için daha önce 23/23 kabul testi yeşildi ([41864815416](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41864815416)).
> - **T−60 bağlama:** Dört-model gerçek KO-öncesi tahmin + SHA mühürlü geçmiş lig bazı + ilk oransız PAS; insan tarafından gerçekten kaynak kontrolü yapılan oran gelirse ayrıca yeni fiyatlı karar. Bağlantı 7/7 yeşil ([41876512990](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41876512990)). Henüz gerçek B/C2/C3/M4 maçı işlenmedi.
> - **Maç sonucu kapsamı iki farklı yolda tamam:** Piyasa referansı sonuç eşleştirmesi artık 1.5/2.5/3.5 hepsini ölçüyor, 18/18 yeşil ([41896865857](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41896865857)). Ana `evaluate_quad.py` ileri pilot değerlendiricisi de BTTS ve üç gol çizgisini ayrı Brier, logloss ve kalibrasyonla ölçüyor, **7/7 hedefli test** yeşil ([41897370653](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41897370653)).
> - **M4 dondurulmuş eski testleri tekrarlanmadı:** `.github/workflows/263-m4-quad-batch.yml` için yapılan ilk düzenlemede YAML biçim hatası oluştu (iş gerçekleşmedi, [41897367660](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41897367660)). Aynı dosya düzeltildi; son çalışma **başarılı**, kaynak/model değişmeyince ağır 4.413 maç refit adımını **atladı** ([41897531443](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41897531443)).
> - **Kaynak veriler / kayıtlar değişmez:** İnsan tarafından sınırlı araştırma kullanımı onaylanan 4.518 maçlık SHA snapshot, UEFA 3–4 Kasım M0/M0+Elo kilitli tahminleri ve orijinal B/C2/C3/M4 matematik kodu korunuyor. 100-match resmî pilot ilerlemesi hâlâ **0**.
> - **Açık tek ana entegrasyon kısıtı:** T−60 anında bahis oranları GitHub tarafından otomatik bağımsız doğrulanmıyor; güvenilir kaynaktan gerçek karşı oranlar manuel gözlemle alınabilir, yoksa EV hesaplanmaz, karar PAS. **Bir gerçek lig maçı** üzerinden tam uçtan uca kaynak+oran+KO-öncesi GitHub commit doğrulaması yapılmadan canlı üretim hazır iddiası yok.
>
---

> **4 Kasım 2026 / DÖRT MODEL ANA–ALTERNATİF–PAS UYGULAMA KAYDI**
>
> - Kullanıcı isteği üzerine aynı gün önceki sohbet kararı yeniden incelendi. Dört modelin ayrı olasılıkları, kendi lig tabanına göre güvenilir DEV kalibrasyonu, en az 3 modelin desteklediği pazar, güncel tam karşı oranlar, EV >=%5 / no-vig avantaj >=3 puan, ana / farklı aile alternatifi / PAS, 1.5 Üst keyfî cezalandırmama esas alındı.
> - **Deneysel karar politikası kodlandı:** experiments/263/four_model_value_policy_263.py; oran girişi GOALS_1.5 ve GOALS_3.5 ile genişletildi. Geliştirme Brier-skill negatif olan 1.5 Üst, yüksek ihtimal uyarısında görünebilir; henüz güvenilir değer adayı ilan edilmez. Gelecek gerçek başarı bunu değiştirebilir; M4 otomatik terfi etmedi.
> - Toplu kabul: [.github/workflows/263-four-model-value-one-batch.yml](../.github/workflows/263-four-model-value-one-batch.yml); **sonuç kesinleşmeden tam başarılı deme**. GitHub CI sırasındaki test/konfigürasyon adımlarını gereksiz tekrarlama.
> - **Açık kalan gerçek bağlantılar:** kullanıcının adlandırdığı T−60 gerçek resmî maçta SHA mühürlü forecast + aynı maçın as-of lig baseline kaydı; canlı bahis sitesinin gerçek fiyatları veya doğrudan insan gözlemi (bu kod otomatik fiyat toplamaz); dört-model araştırma kararının aynı KO öncesi güvenli kayıtla bağlanması ve maç sonrası sonuç ölçümü. Kötü veya doğrulanamayan oran = EV yok / PAS. Onaylı 4.518 veri ve 4.413 arşiv **değişmedi**.
>
---

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
