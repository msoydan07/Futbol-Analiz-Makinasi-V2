# 2.6.3 — Yeni 100 maçlık pilot: postmatch skor ve kalibrasyon kabul raporu

**Tarih:** 7 Kasım 2026  
**Dal:** experiment/263-toplu-karsilastirma  
**Çalışma prensibi:** tek kapsamlı test, eski mühürlü tahminleri değiştirmeden yeni kabiliyet

## Yapılan ve doğrulanan
- Genel 2.6.3 offline kabul: **120/120 PASS** — https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42360088847
- Maç sonu ayrı iş akışı: **15/15 sentetik test PASS; gerçek boş pilot raporu SUCCESS** — https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42360088887
- GitHub gerçek salt okunur rapor çıktısı: new100_registered=0, human_attested_results=0, independently_verified_results=0, pending=0. 0 veri için isabet veya Brier yüzdesi yok, kaynak başarısı iddiası yok.
- İş akışı: .github/workflows/263-sabah-new100-postmatch-readonly.yml
- Skorlayıcı: experiments/263/sabah_postmatch_new100_263.py
- Güvenlik testleri: experiments/263/test_sabah_postmatch_new100_263.py
- Gerçek insan kaynak inceleme kontratı: docs/263_2026_11_07_new100_postmatch_evaluation_contract.md
- İş akışı deney dalındaki kod veya yeni results JSON eklendiğinde çalışır; B/C2/C3/M4 yeniden eğitilmez.

## Çıktılar
- MS 1-X-2: top-1 isabet %, 3-sonuçlu Brier ve log-loss, her modelde ayrı N.
- KG Var ve 1,5 / 2,5 / 3,5 Üst: doğru yön %, ikili Brier, log-loss ve 5 kalibrasyon grubu, ayrı N.
- DEV-kalibre olasılıkları: sadece karar dosyasında pozitif kalibrasyon becerisi ve yeterli destek ile C3/M4 dayanağı olduğu pazarlarda ayrı değerlendir; B/C2/C3/M4 yüzdelerini keyfi birleştirme.
- M4 – diğerleri: sadece **aynı maç** üzerinde her iki modelin de hesaplama yaptığı eşleşmelerde Brier farkı. Dört modelin hepsinin çalıştığı ortak maç sayısı ayrıca izlenir.
- Korner: güvenilir/kalibre veri ve resmi sonuç kimliği yoksa **HESAPLANMADI**.
- Bir maçın kesin skoru resmî sayfadan **insan teyitli** atanmışsa veri sınıfı HUMAN_ATTESTED_OFFICIAL_PAGE_NOT_NETWORK_REVERIFIED; bir URL'nin varlığı skoru bağımsız ağ doğrulaması yapmaz. Gerçek bağımsız ağ doğrulama adımı bu sürümde henüz yok. Kullanıcıya veya bahis kararına 'verified' iddiası taşınmaz.
- Maçın resmi kaynağının zamanı, mühürlü SHA/ID/KO ve veri şekli uyuşmazsa veya aynı maç için çelişik iki sonuç gelirse skor üretme.

## Değişmezler
- Ana dal main ve B/C2/C3/M4 hesaplama fonksiyonları değişmedi.
- 96 eski aday ve old four-record forward_quad_263 ayrı; 3 acceptance3 mühendislik kaydı da ayrı. NEW100: **0/100**.
- Geriye dönük tahmin yaratmak, orijinal mühürleri yeniden yazmak, geçmiş modelleri eğitmek, kaynak kanıtı olmayan maç sonucu yazmak, sahte odds/EV/ROI göstermek yasak.
- Pinnacle / iddaa / başka API kredisi kullanılmadı. Bu akış yalnız kaynak-attestasyon ve puanlama içindir.

## Tek sonraki çalışma
Yeni100 pilot için kullanıcının açıkça adlandırdığı **ilk gerçek, hâlâ başlamamış** müsabaka ile resmi fikstür+ileri SHA kaydını oluştur. Bittikten sonra gerçek resmi skor kaynağıyla hem tam zaman skoru hem resmi maç kimliğini doğrula ve new100 karnesine ekle. Bağımsız ağ doğrulaması yapılmadıkça veriyi insan-attestasyon olarak etiketle. İlk kayıt olmadan başarı %, model üstünlüğü veya tamamlanmış 100 pilot raporu verme.
