# 2.6.3 — 4.617 Maçlık Sonuç Arşivinin M4 Araştırma Motoruna Bağlanması
**Tarih:** 10 Kasım 2026  
**Dal:** `experiment/263-toplu-karsilastirma`

## Durum: 4.617 skor verisi gelecek yeni maç analizleri için aktif araştırma girdisi

- 4.518 özgün kabul edilmiş satır, `data/quad_accepted_263/extended_history.csv`, SHA256 `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`, **değişmedi**.
- 99 yeni, daha önce 99/99 tarih/takım/skor eşleşmesi yapılmış sonuç `data/quad_accepted_263/completed_99_results_only_20261110.json` içinde ayrıca korunur.
- 4.617 satırlık yalnız maç sonuçları veri dosyası `data/results_only_263/2026-11-10_completed_4617_scores_only.csv`, SHA256 `637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89`.
- 9 eski ENG2 kayıtlarının içerikleri aynen korundu; 99 yeni satırdan şut, korner, kart ve başka eksik/denetlenmemiş ayrıntılı istatistikler alınmadı.
- Yenilenen yeni100 sabah ve eski dört-modelli tek-maç iş akışları, **artık bu 4.617 satırlık dosyayı ve açık kaynak sınıfı manifestosunu** (`data/results_only_263/4617_research_input_provenance.json`) kullanır.
- M4 ile B/C2/C3 matematik fonksiyonları, 2025/26 DEV kilidi, eski 40 mühür, LITE ve basketbol değiştirilmedi.
- Motor **10 ligin tamamını her seferinde maç maç simüle etmez**: istenen ligin yalnız maç tarihinden önceki, normal tam süre oynanmış geçmiş satırlarını ilgili model fit'ine alır.
- Yeni100 arşivindeki daha önce mühürlenmiş 8 Kasım maçları yeniden hesaplanmaz veya geriye dönük güncellenmez.

## Bağımsız kaynak statüsü — kesin ayrım

Bu yükseltme **araştırma kullanımına** alınmıştır, bütün 99 maçın resmî federasyon tekil maç kimliği onaylandığı iddiası değildir. Yeni skorlar için gözlem sınıfları: 28 lig/federasyon+sağlayıcı araştırma uyuşması; 28 doğrudan lig/kulüp skor sayfası; 43 ikincil skor + kısmi resmî fikstür çapraz kontrolü. Bu durum mühür verisinde `APPEND_ONLY_4617_PUBLIC_RESULTS_ONLY_RESEARCH_NOT_OFFICIAL_ID_VERIFIED` olarak açıkça işaretlenir; insan kaynak onayı bayrağı **false**, resmî bahis onayı **false** kalır.

## Gerçek GitHub testi ve dal devri

- [7/7 CI regresyon, asıl 4.617 veriyle gerçek M4 fit farkı ve dört-model/sabah/telefon-mühür testleri](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42817490005) — SUCCESS.
- En son kaynak SHA'ları 4.413 temel, 4.518 eski, 4.617 yeni **üçü de doğrulandı**.
- Testte kullanılan sahte fikstür **yalnızca geçici test dizininde** oluşturuldu; gerçek yeni tahmin gibi kaydedilmedi.
- İş akışları `263-sabah-new100-on-request.yml` ve `263-quad-forward-on-request.yml` yeni dosya ve kaynağı okuyor.
- Dal devri 10 Kasım 2026'da `experiment/263-toplu-karsilastirma` üzerine ileri yönlü (fast-forward) yapıldı. O sıradaki dal SHA `b93c2f6825afcfed7c82b112a5ddc5159a6c53c9`. `main` değiştirilmedi.

## Son kalite kapanışı — 10 Kasım 2026, 10 lig

**Tamamlanan ve GitHub Actions ile doğrulanan işler:**

- [10 ligin tamamında 4.617 satırlık gerçek sonuç verisiyle M4/B/C2/C3 hesapları, tarih-kesit, MS/KG/1,5/2,5/3,5 olasılıkları ve araştırma PAS güvenlik testi: 9/9](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42819330391) — SUCCESS.
- [Sabah entegrasyonu ve mobil SHA mührü 223/223](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42818789654) — SUCCESS.
- [Normal süreden önce bitip hükmen tescil edilen maçın 90 dakika modellerinden çıkarılması 25/25](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42818789879) — SUCCESS.
- [Empirik baz oran ve önceki kaynak zinciri: bütün test grupları](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42818789763) — SUCCESS.
- Testten önceki iki kırmızı CI koşusu, eski 4.501 satırlık test varsayımı ve sentetik kayıtta eksik kaynak bayrağı nedeniyle oluşmuştu. Test girdileri gerçek 4.617 arşiv ve bugünkü kabul etiketleriyle uyumlu hâle getirildi; **üretim kabul kapıları gevşetilmedi**.
- En son kapsamlı CI, `m4_integrated.py`, `m4_lock.json`, eski 4.518 dosyası ve `forward_quad_263`, `forward_morning_263`, `forward_acceptance_263` ağaçlarını eski Git SHA ile birebir karşılaştırdı: **aynı**.
- Özgün 4.413 temel, 4.518 kabul edilmiş tarihçe, 4.617 sonuç dosyasının üç SHA'sı tekrar doğrulandı.

**Tamamlanan işin sınırı:** İş akışını 10 ligin tamamında gerçek sonuçlarla model hesaplayacak şekilde kanıtladık; testlerde kullanılan **fikstür geçidi sentetiktir**. Yeni bir gerçek maç için bağımsız resmî fikstür sayfası doğrulaması ve maç önü gerçek SHA mührü **henüz yapılmadı**; istenen gerçek maç gelmeden uydurulmamalı. 99 sonucun 43'ü ikincil kaynaklı araştırma kanıtına dayanır; tekil federasyon maç ID kanıtı yok. Bu iki açıklık modelin tahmin/başarı kanıtı gibi gösterilemez.

**Sonraki tek işlem:** Gelecek **gerçek, başlamamış** kapsam maçı için sabah model koşusu (4.617 araştırma kaynağı, resmî fixture gate, yeni SHA mührü) ve daha sonra maç sonrası karşılaştırma. **Eski 99 maçın yeniden aranması veya M4 parametrelerinin değiştirilmesi gerekmiyor.**

## Tek sonraki iş

Yeni gerçek bir maç geldiğinde **resmî canlı fikstürü önce doğrula**, 4.617 kaynakla gerçek maç öncesi sabah tahmini üret ve SHA mühürle; sonuçtan sonra aynı mührü gerçek sonuçla kıyasla. **Yeni 99 maç için aynı kaynak araştırmalarını yeniden başlatma.** Gelecekteki 99'luk veya başka sonuç gruplarını arşive eklerken ayrı kanıt sınıflarını koru; model formüllerini kör pilot performansı olmadan değiştirme.


## 10 Kasım 2026 gece kapanışı — 99 skor işi ve 10 lig canlı kaynak denetimi

- **99/99 sonuç** daha önce `data/quad_accepted_263/completed_99_results_only_20261110.json` ve 4.617 maçlık birleşik, yalnız skor içerikli `data/results_only_263/2026-11-10_completed_4617_scores_only.csv` içine kalıcı olarak arşivlendi. Çift kayıt üretilmedi; eski 4.518 satır ve 9 ENG2 istatistik farkı değişmedi.
- **43 eskiden ikincil kaynaklı skor için özel tamamlayıcı kanıt dosyaları:** `data/results_only_263/43_primary_public_score_review_20261110.json` ve `data/results_only_263/21_official_public_web_alternate_score_reviews_20261110.json`. İlk GitHub tarayıcı denetiminde **22/43** resmî sayfa gövdesinde takım + nihai skor aynı içerikte otomatik eşleşti. Geri kalan **21/43** (ENG1=5, ENG2=6, BEL1=10), Premier League/EFL/kulüp/Pro League'in resmi kamu sayfalarında **GitHub dışı alternatif web erişimiyle** ayrıca incelendi. **0 eski arşiv skor çelişkisi**. Bunlar yeni maç değildir; 99 zaten arşivdeydi.
- [99 özgün sonuç + 43 kaynak eşleşmesi + 21 ek incelemeyi sınayan **8/8 başarılı** GitHub testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42897904572). Özel kodlar `experiments/263/close_99_results_source_audit_263.py` ve testi.
- **Kanıt sınırı:** GitHub CI üzerinden `43/43` canlı kaynak gövdesi çekildi iddiası **YOK**. 22 CI tarayıcı eşleşmesi + 21 alternatif web resmî sayfa incelemesi ayrı tutulur. Sağlayıcı tekil resmî maç ID'si ve veri yeniden dağıtım lisansı bütün 99 için ayrıca onaylanmış değildir. Buna rağmen kullanıcının talebi olan **oynanmış maçın skorunu doğrulayıp ayrı güvenli arşive yazma işi tamamlandı**; bu lisans/ID bilgileri gelmedikçe doğrulanmış ileri performans veya bahsi onaylama iddiası yok.
- [10 ligde **10 Kasım'a ait gerçek canlı fikstür ön-denetimi**](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42897323995) başarılı. 10/10 lig kaynağı denendi; **o gün başlanmamış, resmî saatli ve kanonik kimlikli yeni pilot adayı 0**. Bu bilgi uluslararası arada lig fikstürünün tümü yok demek değildir. **Tahmin 0, Pinnacle/API 0, SHA mühür 0**.
- **Belçika fikstürü için önemli çözüm:** Pro League ana `/fr/jpl-calendar` sayfası GitHub tarayıcısında 403 üretirken resmî `https://www.proleague.be/jpl-kalender!` Next.js SSR kaynağı **HTTP 200**, **9 özgün maç ID + ev/deplasman + gerçek UTC kickoff** döndürdü. 9 maç **20–22 Kasım 2026** tarihlerinde, bugünden 7 gün içinde değildir. Kaynak HTML SHA `cf852ac069bed224cc0ad2419f5392e87cd99f90f754d04a7015a38ac7bf67f7`; maçlar `data/results_only_263/nov10_belgium_future_live_ssr_fixture_9_source_evidence.json` içinde zamanlı kayıtlı. Var olan `sabah_belgium_official_nextjs_263.py` ayrıştırıcısı bu sayfayı destekliyor; yeni model veya tahmin oluşturulmadı. **Resmî maç ayrıntısı sayfalarına GitHub 403 erişim problemi hâlâ teknik sınırlamadır**.
- **Karar:** 99 maçın skor ve güvenli arşiv işi yeniden açılmasın. İlk gerçekten başlamamış maç, saat penceresine girdiğinde o gün kaynağı yeniden kontrol edilerek **4.617 araştırma kaynağı** ile SHA-mühürlü tahmin oluşturulacak; geçmiş maçlara yeniden mühür atılmayacak. M4 `main` kilidi, mevcut modeller ve eski tahminler değişmedi.

