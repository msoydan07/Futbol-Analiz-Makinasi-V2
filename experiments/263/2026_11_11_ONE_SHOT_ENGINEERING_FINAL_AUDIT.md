# Futbol Analiz Makinası 2.6.3 — 11 Kasım 2026 tek toplu mühendislik denetimi

**Çalışma dalı:** `experiment/263-toplu-karsilastirma`. M4 donmuş modeli, eski 96 maçlık pilot tahminleri, LITE ve basketbol kodları değiştirilmedi. Kullanıcının onayı: yapılan testleri tekrar etmeme, yeni pilot açmama, matematik/fiyat/PDF doğruluğunu denetleme, en sonda tek rapor.

## 1. Kanıta dayalı mevcut durum

**Son bütünleşik test:** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43061659668 — **53/53 çevrimdışı regresyon testi başarılı**. Bu test grubu önceki 48 testin geriye uyumluluğunu, 4 bağımsız Poisson analiz testini ve yeni özel/veri yolu-bütünlük testini içerir. Adayların tahmin isabet oranı değildir.

**İlk defa bu denetimde yapılan 4.617 gerçek skor veri as-of matematik testi:** Aynı başarılı CI koşusunda, kabul edilmiş **SHA `637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89`** skor-only veri arşivi **4.617/4.617** okunarak doğrulandı. Eski bilinen maç bitmeden tescillenen **bir NED1 81. dakikada terk edilmiş ve 4-0 hükmen skorlanmış maç**, tam 90 dakikalık matematik eğitiminden çıkarıldı (**4.616 uygun maç**). Kaydın resmî skor sonucu değiştirilmedi.

Her ligde **donmuş M4 ayarlarıyla tek as-of fit** yapıldı, ayrıca aynı örnek takım çifti için **B/C2/C3** hesaplanabilirliği sınandı. Bu bir **sonuç görüp yeniden optimize etme** veya ileri tahmin isabet deneyi DEĞİLDİR.

| Lig | Tam maç geçmişi | B | C2 | C3 | M4 |
|---|---:|:---:|:---:|:---:|:---:|
| ENG1 | 480 | ✓ | ✓ | ✓ | ✓ |
| ENG2 | 732 | ✓ | ✓ | ✓ | ✓ |
| GER1 | 387 | ✓ | ✓ | ✓ | ✓ |
| ESP1 | 499 | ✓ | ✓ | ✓ | ✓ |
| ITA1 | 490 | ✓ | ✓ | ✓ | ✓ |
| FRA1 | 396 | ✓ | ✓ | ✓ | ✓ |
| NED1 | 413 | ✓ | ✓ | ✓ | ✓ |
| TUR1 | 405 | ✓ | ✓ | ✓ | ✓ |
| POR1 | 404 | ✓ | ✓ | ✓ | ✓ |
| BEL1 | 410 | ✓ | ✓ | ✓ | ✓ |
| **Toplam** | **4.616** | | | | |

**Bağımsız matematik doğrulaması:** Dondurulmuş M4 ve kanonik C2 Poisson matrisleri **81 ayrı `λ_ev × λ_dep`** senaryosunda kapalı form bağımsız hesaplarla karşılaştırıldı: `KG Var = (1-e^-λev)(1-e^-λdep)`, `2.5 Alt = e^-(λev+λdep)·(1+λev+λdep+(λev+λdep)^2/2)`. MS 1/X/2 olasılık toplamı, ev–deplasman simetrisi, 2.5 Alt+Üst=1 ve KG Var+Yok=1, üst/alt sıralama monotoniği, domain dışı input kapıları test edildi. Eski B/C3 0–10 gol kuyruğu büyükse tahmin uydurulmadığı doğrulandı. **Bu testler modelin maç sonucunu öngörme becerisini değil, hesaplanan olasılıkların matematiksel tutarlılığını doğrular.**

## 2. Denetimde gerçekten düzeltilen sorunlar

1. **Önemli uçtan uca veri yolu hatası:** İddaa kullanıcı PDF dosyası `/tmp` veya `/mnt/data` gibi repo dışındaki bir klasöre işlendiğinde, kalibrasyonun SHA'lı dört-model kayıtlarını okuması reddediliyordu. **Düzeltildi:** `iddaa_pdf_value_bridge_263.py` yalnız ilgili özel oturumun `forecasts/` ve `empirical_baselines/` altındaki JSON'larını okuyor; `../` ve symlink kaçışı reddediliyor. `iddaa_pdf_one_step_263.py` bu sınırlı oturum bağını geçiriyor. **Gerçek rapor üreten sentetik uçtan uca test geçti.**
2. **Tek PDF'yi yanlışlıkla ikinci kez işletme:** Önceki sistem aynı PDF SHA'sında doğrudan `FileExistsError` veriyordu. **Düzeltildi:** Başarıyla tamamlanmış oturumdan `completed_receipt.json` imzalı özet ve çıktı PDF byte-SHA kontrolüyle **aynı raporu geri verir**; maç resmî kaynağını tekrar çağırmaz, yeniden oran aramaz, tahminleri veya eski pilotu tekrar yazmaz. Önceki oturum yarım kalmışsa sessizce o kaydı başarı saymaz; fail-closed ve ayrı inceleme gerekir.
3. **Kullanıcının yüklediği bültenin kazara GitHub'a yüklenmesi:** Varsayılan yerel kullanıcı PDF klasörleri `.gitignore` kapsamına alındı; PDF baytları işleme klasöründe kalır.
4. **Matematiğin ayrı kaynağa göre karşılaştırması:** 81 × 2 bağımsız analitik gol/KG hesap ve 10 lig gerçek veri fixed-fit denetimi eklendi; ana M4 motoru, 4 model katsayı ve parametrelerini yeniden eğitmek için geriye dönük optimize edilmedi.

## 3. Önceden yapılmış olup tekrarlanmayan işler

Mevcut ilk 48 PDF/ad/market/ev-deplasman/GitHub testlerini yalnız geriye uyumluluk korumak için aynı CI'da çalıştırdık. Önceki M4 parametre 12 aday araması, eski 96 maç pilotu, 99 maçın arşiv kararı, B/C2/C3 model ayarı, 25 maçlık operasyonel test, Pinnacle kredi tüketimi, bahis oranı API'sinden yeniden fiyat arama **tekrarlanmadı**.

Resmî/araştırma veri sınıfı ayrımı korunur: 4.617 sonuç-only skor havuzundaki son 99 maçın **28'i resmî sayfa/ikincil uyum**, **28'i doğrudan lig/kulüp skor sayfası**, **43'ü ikincil skor ve kısmen resmî fikstür destekli**. Bunlar 4.617 maçın tamamının bağımsız resmî maç ID'siyle onaylandığı anlamına gelmez.

## 4. Şimdi tespit edilen gerçek canlı operasyon riskleri (kapalı değil!)

**A — Resmî fikstür adapterlerinin zaman kapsamı:** Gerçek çağrıda kullanılacak bazı adapterler **eski sabit haber/hafta sayfalarına** bakıyor: `championship_fixture_lookup.py` (EFL 30 Ekim–4 Kasım hakem duyurusu), `laliga_fixture_lookup.py` (jornada 11), `serie_a_fixture_lookup.py` (11. hafta hakem ataması), EPL Ekim-Kasım değişiklik haberi, `ligue1_fixture_lookup.py` sabit TV haberi, `portugal_fixture_lookup.py` 12. haftaya kadarki TV programı ve `belgium_fixture_lookup.py` tek kulüp takvimi. Genel güncel kaynak seçimi ve gerçek bir kapsam ligi PDF'siyle bağlantı **henüz doğrulanmadı**. İddaa bülteni birinci kaynak olduğundan canlıda ikinci resmî kontrol yapılamazsa **yalnız ilgili maçın resmî onayı bloke edilir**; ikinci bahis operatörüne gidilmez. Bu durum testlerin yeşil olmasına rağmen ilk maç günü için operasyonel risktir.

**B — Milli maç arası ve geçmiş veri tazeliği:** `forward_c3.py` ve `forward_quad.py` geçmiş veri için **10 gün** sınırı kullanır. 9–17 Kasım uluslararası arada maç olmayınca, 21 Kasım gibi ilk lig gününde **son oynanan maçın üzerinden 10+ gün geçmiş olabilir** ve matematik doğru olsa bile geçerli as-of veri onayı alınmadan tahmin kapısı doğru biçimde PAS verebilir. Tarih kuralını körlemesine 20–30 güne yükseltmedik; bunun için resmî takvimden *gerçekten oynanmamış* aralığın teyidi ve ilk hafta sonu güncel skor arşivinin yenilenmesi gerekir. Kaynak eksikken hayalî tarih damgası verilmesi yasak.

**C — Tahmin doğruluğu/kâr için ispat sınırı:** 81 durumlu matematik tutarlılığı ve 10 lig as-of fixed fit, **out-of-sample MS/KG/2.5 tahmin üstünlüğünü veya bahis EV'sini kanıtlamaz**. Bunun kararı geçmiş mühürlü tahminlerden, aynı maç eşlemesinde gerçek sonuç ve doğru fiyatla ölçülür. 96 pilotu veya oyuncu/macar tahminleri tekrar üretmek yok. Model değişikliği için gerçek eşleşmiş kör sonuç kanıtı gereklidir.

**D — Gerçek İddaa 10 lig PDF kabulü:** Önceki 11 Kasım 3-sayfalık belge kapsamdışı maçlar içerdi; 30 satırda 28 tam fiyat hizası, 2 satır şüpheliydi. *10 liglik iddaa takımları, resmi saat ve tek PDF→analiz→PDF* canlı birleşik kabul henüz yapılmadı.

## 5. Net mühendislik kararı

**YEŞİL:** Frozen B/C2/C3/M4 mevcut as-of skor havuzunda 10/10 lig için birer temsilî maç hesabı üretiyor; MS/KG/2.5 matematik olasılıkları bağımsız Poisson testleriyle tutarlı; 53/53 denetim ve orijinal PDF-first fiyat karar/kopya rapor testi geçti. Özel oturum yolu ve gizlilik/tekrarlı çalıştırma sorunları düzeltildi.

**TURUNCU — canlı kabulü henüz yok:** Güncel resmî fikstür/hafta adapterleri ile ara sonrası veri tazelik kapısı. Bu engeller çözülmeden **“her maçta üretimde sorunsuz yüzde yüz çalışır” ya da “şu model en doğru, bahis avantajı garanti”** denmez. Tek gerçek kapsam ligi İddaa PDF'si geldiğinde, esas canlı kabul yalnız o günün seçili maçlarında bir defa yapılmalı, resmî kaynaklar anlık güncel haftaya yönlenmeli; baştan yeni 96 pilot başlatılmamalı.

## Kaynaklar

- [53/53 + 4.617 gerçek skor, 10 lig, 4 model, GitHub CI](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43061659668).
- [Dört model ve kalibrasyon kaynak sözleşmesi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/IDDAA_PDF_FIRST_WORKFLOW_263.md).
- [Yeni bağımsız gol matematiği deneyi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/test_263_independent_goal_math_audit.py).
- [4.617 gerçek skor sabit model denetimi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/real_4617_math_readiness_audit_263.py).
