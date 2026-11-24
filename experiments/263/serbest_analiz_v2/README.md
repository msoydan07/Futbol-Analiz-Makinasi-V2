# Üçlü Sistem — Serbest Analiz V2 / Operasyon Paketi

**Tarih:** 23 Kasım 2026  
**Güncel durum (24 Kasım 2026):** Modüler araştırma kodu, iki kaynaktan doğrulanmış 4.700 maçlık araştırma verisi ve Mobil Hafıza V1.3 eksik oran ekranı hazır. **İki ayrı gerçek gelecek maç** için resmî fikstür → M4/C3 → KO öncesi GitHub SHA kaydı yolu başarıyla denendi. Bu kayıtlar yalnız **araştırma dalında**; ana 2.6.3 matematiği, Hakem V1 katsayıları ve önceki mühürler değiştirilmedi. PDF akışı ayrı/local çalışır; ana üretim dalına dağıtım yapılmadı.

## Üç bağımsız çalışma yolu

1. **PDF geldi, M4 hazır değil:** P0 çalışır, 35.938 maçlık tam özel Hafıza dosyası yüklenmişse Hafıza çalışır. Eksik oranda, tam pazar marjları varsa yalnız *teorik* oran hesaplanır. Yalnız kullanılabilen alt pazarlar değerlendirilir.
2. **PDF geldi, M4 de hazır:** Üç tam kaynak olduğunda eski dondurulmuş Hakem V1 karar formülü korunur. Bir uzman yoksa mevcut uzman(lar) kendi kararını üretir; iki kaynaklı birleştirme *ayrı ve daha az kanıtlı araştırma sonucu* diye etiketlenir.
3. **PDF yok, yalnız adlandırılmış 10 lig maçı:** Resmî fikstür doğrulaması ardından M4/C3 kendi gerçek tarih-öncesi futbol verilerinden tahmin üretebilir. Güncel veri kaynağı ve resmi KO doğrulaması olmazsa ileri mühür oluşturulmaz. `--research-only` araştırma yolu ise isim + tarih + model kaynağı ile çalışır; sonuç açıkça *mühürsüzdür*.

## Bilgisayarda tek komut

Gerekli: Python 3.11+, `numpy`, `scipy`, `pymupdf`.

```
python GUNLUK_SERBEST_ANALIZ_KAPISI_V2.py \
  --pdf examples/pazartesi.pdf --archive oran_hafizasi_tam.json \
  --date 2026-11-23 --rule hakem_karar_kurali_v1.json --out-dir results
```

PDF olmadan **önceden kaydedilmiş M4** ile mühürsüz arşiv araştırması:

```
python GUNLUK_SERBEST_ANALIZ_KAPISI_V2.py \
  --league GER1 --home Elversberg --away Freiburg --date 2026-11-21 \
  --research-only --model-index M4_KAYNAK_6_MAC_ORNEK.json \
  --rule hakem_karar_kurali_v1.json --out-dir results
```

**Resmî yeni 10 lig maçı**: Ana GitHub model deposunun çalışma kopyasına `--engine-root`, güncel ve SHA-doğrulanmış `--history`, takımları eşleyen `--registry` ver. `--research-only` verme. Kod `OfficialFixtureGateway` üzerinden aynı maçın gerçek kimliğini/KO bilgisini doğrular; sabah saati koşulu yoktur. En geç KO öncesinde işlemin ve Git commit'in tamamlanması zorunludur. Tarihsel kaynak 10 günden eskiyse ana makinenin sıkı *ara fikstür yok* kaynak doğrulaması çalışır; yeni oynanmış eksik maç varsa kayıt durur.

## Telefonda: Mobil Hafıza V1.3

`MOBIL_ORAN_HAFIZASI_V1_3_SERBEST.html` dosyasını Chrome/Android'de aç. `Veri aktar` üzerinden `oran_hafizasi_tam.json` dosyasını yükle. Sonra `Eksik oran` sekmesinden PDF seçip, alınan satırları kontrol ederek `Mevcut oranlarla analiz et` düğmesini kullan.

- Önceki V1.2'nin normal **7 tam oran** ve Hakem staging dışa aktarımı korunur. Eksik-oran pazarları yeni `Eksik oran` sekmesinde işlenir; bu ayrı sekme **staging JSON üretmez**.
- Sunucu bağlantısı gerekmez; ancak telefonda PDF okumak için PDF.js kütüphanesi ilk seferde CDN'den indirilebilir. 
- Piyasa marjı ölçülemezse veya aynı markette iki/üç değer eksikse varsayımsal oran icat edilmez. Hafıza sorgusu yalnız mevcut sağlam piyasa boyutlarında yapılır ve *zayıf koşullu örneklem* diye görünür.
- 35.938 arşiv dosyası **GitHub'a hiçbir zaman yüklenmedi**; yalnız özel indirilen pakettedir.

## GitHub araştırma dalı

Depo `msoydan07/Futbol-Analiz-Makinasi-V2`, araştırma dalı `experiment/p0-oran-hafizasi-22-lig-20261122`.

- `experiments/263/serbest_analiz_v2/` altında gerçek modüler Python kaynakları + 9 resmî kapı test dosyası tutuluyor.
- `.github/workflows/263-serbest-analiz-v2.yml`: kod güncellemesinde modüler analiz, KO, SHA ve veri kilidi regresyon kontrolleri, ayrıca manuel `workflow_dispatch` ile doğrulanmış isimli kayıt yolu. GitHub Actions tetikleme arayüzü iş akışının default dalında olmamasından etkilenebilir.
- `.github/workflows/263-serbest-analiz-request-v2.yml`: chat'ten tek maç adıyla gönderilebilecek `requests/<benzersiz>.json` dosyasının araştırma dalına GitHub commit edilmesi üzerine çalışır; resmî fikstür + güncel veri + gerçek KO şartını sağlarsa yalnız **yeni** `official_receipts/` dosyasını başlangıç öncesi Git commit eder. Kaynak yoksa işlem başarısız olur; sahte sonuç yazılmaz.
- Kaydedilecek talep şeması: `{"schema":"SERBEST_NAMED_REQUEST_V2","league":"TUR1","home":"Besiktas","away":"Kasimpasa"}`. Bu yalnız **istek örneğidir**, gerçek maç doğrulaması değildir. Kullanıcı isteği olmadan otomatik sahte talep gönderilmez.
- **Kanıt:** [Werder Bremen–Mönchengladbach GitHub çalışması](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/45259881704) ve [Hamburger SV–Bayern Münih ikinci çalışma](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/45265694055) başarıyla GitHub'a iki farklı pre-KO araştırma kaydı ekledi. İkinci kayıt oluşturulurken ilk kayıt değişmedi. **Bu araştırma kaydıdır; main üretim mührü olarak tanıtılmaz.**

## Yerel testler

- Python modüler yönlendirici + eksik fiyat + P0/Hafıza + Hakem: **27/27** (ilk kabul).
- Bağımsız saat/KO/gate güvenliği: **9/9**. Eski mühür yanında ikinci kayıt ve SHA/staging güvenliği: **11/11**. Yeni 4.700 kaynak kilidi: **3/3**; GitHub regresyonu başarılı.
- Yeni Mobil V1.3: Chrome tabanlı tarayıcı DOM'da PDF.js'in metin öğeleri için simüle edilmiş geometrik çıktı ile **4/4 maç**, bir fiyatın kasıtlı eksiltilmesi, tam **35.938 Hafıza dosyası yükleme**, **4/4 benzerlik sayımı** doğrulandı. Cihazda gerçek PDF.js CDN indirimi ve Android dosya izinleri ayrıca denenmeli.
- Gerçek resmî yeni fikstür üzerinden araştırma dalına **iki ayrı** GitHub ön maç SHA kaydı başarılı. İkisi de henüz oynanmamış maçlar; geçmişe yönelik tahmin yazılmadı.

## İlk kullanım sınırları

PDF varsa ilk analiz yapılıyor. 10 ligden maç adı verilirse model kaynakları bulunduğunda araştırma analizi yapılabiliyor. Yeni canlı M4/C3, 4.700 satırlık SHA kilitli araştırma kaynak sürümüne bağlandı; 83 yeni skor Football-Data ve ESPN'de uyumlu, fakat resmî federasyon tarafından tek tek teyit edilmiş sayılmaz. Orijinal resmî tahmin dalının sabah iş akışı *bu sürümde kapatılmadı*; yeni modüler yol ayrı bir alternatiftir. Bu düzeyde tamamlanan işler çalışır; canlı operasyonun son kabulü için gerçek bir yeni maç koşusu gerekir.

## Güncel gerçek veri ve iki canlı kayıt kanıtı

- **Model geçmişi:** [4.700 satırlık araştırma dosyası](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/p0-oran-hafizasi-22-lig-20261122/data/research_263/2026-11-23_4700_two_source_research.csv); SHA `37bf74e820df85325213c2e0ef8ce9a88a16c1f452edf5bd2a41814f10f261bd`; eski 4.617 korunuyor. [83 maçlık iki kaynaklı skor defteri](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/p0-oran-hafizasi-22-lig-20261122/data/research_263/2026-11-23_83_two_source_match_ledger.json).
- **İlk gerçek pre-KO kayıt:** [Werder Bremen–Mönchengladbach, 27 Kasım](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/p0-oran-hafizasi-22-lig-20261122/experiments/263/serbest_analiz_v2/official_receipts/2026-11-27_770bb05a304b6e2d4031e43f.json). Araştırma ana tercihi KG Var %59,67.
- **İkinci gerçek pre-KO kayıt:** [Hamburger SV–Bayern Münih, 28 Kasım](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/p0-oran-hafizasi-22-lig-20261122/experiments/263/serbest_analiz_v2/official_receipts/2026-11-28_47dab11049caeb3343339380.json). Araştırma ana tercihi MS 2 %80,48. İlk dosyanın SHA'sı aynen korundu.
- **Tetikleme:** 10 ligden istenen yeni maçın `requests/<benzersiz>.json` dosyasını araştırma dalına commit et; `263-serbest-analiz-request-v2.yml` yalnız resmî kimlik + güncel futbol geçmişi + KO sonrası olmayan an için sonuç yazabilir. Saat sabah/akşam fark etmez; eğer GitHub commit KO öncesine yetişmezse pre-KO mühür verilmez.
- **PDF kullanımı:** Kullanıcı iddaa PDF'si + özel `oran_hafizasi_tam.json` ile Python yerel akışı veya Mobil V1.3 kullanılabilir. Eski PDF'leri aynen işlemek mümkündür; PDF girişinin otomatik GitHub tahmini üreten üretim servisi kurulduğu iddia edilmez. Bu arşiv **GitHub'a yüklenmemeli**.
- **Sınırlar:** 23 Kasım'da oynanan yeni maçlar bu as-of `2026-11-23` dışlama tarihli 4.700 verisine ekli değildir. Aynı maç için birden fazla analiz üretilirse ilk GitHub kaydı üzerine yazılmaz, ek kayıtların farklı sürüm olarak değerlendirilmesi gerekir. Üretim `main` dalı değişmedi.


## 24 Kasim 2026 — Hakem 2 ve P0/Hafiza yeni mac izleme koprusu

**Araştırma dalı; ana üretim M4/C3 ve önceki SHA mühürleri değişmedi.**

- Donmuş 504 eğitim maçlık **Hakem 2** kuralı `hakem2_kural_504_v1.json` olarak bu dalda sabitlendi. `HAKEM2_GUNLUK_SECICI_V1.py`, tek uzmanı MS / OU25 / KG pazar ailesi bazında seçer; olasılıkları harmanlamaz. P0'ın seçilmesi araştırma eğitim kaynağı olan **1xBet arşiv vekilinden** gelir; canlı iddaa üstünlüğü kanıtı değildir.
- Serbest analiz yönlendiricisi ve günlük kapı yeni **isteğe bağlı** `--hakem2-rule experiments/263/serbest_analiz_v2/hakem2_kural_504_v1.json` argümanı kabul eder. Üç uzman varsa Hakem 2; iki uzmansa **Hakem kararı yok**, uzmanların bireysel tahminleri var. Tek kaynak varsa yalnız doğrudan uzman kararı. V1 varsayılan/karşılaştırma yolu korunur; canlı üretime geçiş yapılmadı.
- `P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1.py` özel mobil JSON + **orijinal PDF** bütünlüğünü yeniden doğrular. PDF'nin tamamı ile seçilmiş satırların sayısı eşit olmak zorunda değildir: kayıtlar **maç adı + saat + gerçek yedi oran** üzerinden bağımsız eşleşir. Bağımsız ayrıştırılamayan satır resmî kapıya GİREMEZ.
- `capture` komutu yalnız 10 lig için bağımsız `OfficialFixtureGateway.lookup` doğrulaması, eşleşmiş resmi KO ve gelecekte kickoff varsa **yeni**, SHA içerik adresli araştırma adayı oluşturur. Dış liglerde P0/Hafıza çalışır ama 10-lig gateway'i dışına resmî pre-KO kanıtı uydurulmaz. Bu kayıt ancak KO **öncesi GitHub'a kabul edilip** `263-p0-hafiza-preko-guard-v1.yml` başarılı olunca Git tabanlı araştırma mühürü sayılabilir.
- `evaluate` komutu gerçekleşen skoru dışarıdan verilmiş kaynak dosyasıyla eşleştirerek P0/Hafıza ayrı isabet/Brier raporu çıkarır. **Bu skor girdisini kendi başına internette doğrulamaz.** Resmî sonucu otomatik getiren kapsam-geniş sonuç kaynağı henüz bağlı değildir; değerlendirme geçici etiketlidir.
- Özel 35.938 arşiv, ham mobil JSON ve orijinal PDF **Github'a yüklenmez**. Kaydedilecek özet yalnız resmî doğrulanmış fikstür, pazar olasılıkları ve kaynak SHA'larını içerir.
- 24 Kasım `deneme1.pdf`: kaynak PDF ayrıştırıcısı toplam 27 maç satırı buldu; mobil tam-yedi-oran aktarımı 19 satır. Yerel bağımsız satır denetiminde 19'dan **18'i birebir** yeniden yakalandı, Cong An Nha… — Vissel Kobe satırı bağımsız ikinci ayrıştırıcıda yakalanamadı. O satır kaynak matematiği doğrulanmış olsa da resmî kayıt kapısına giremez. 19 kaydın hiçbirinde yetkili fikstür kimliği / KO yok; **resmî maç önü mühür oluşturulmadı**.

### İlgili kullanım (özel PC ortamında)

```bash
python experiments/263/serbest_analiz_v2/GUNLUK_SERBEST_ANALIZ_KAPISI_V2.py \
  --pdf bulten.pdf --archive oran_hafizasi_tam.json \
  --rule experiments/263/serbest_analiz_v2/hakem_karar_kurali_v1.json \
  --hakem2-rule experiments/263/serbest_analiz_v2/hakem2_kural_504_v1.json \
  --out-dir /tmp/serbest_hakem2

# Resmî doğrulanmış 10 lig eşleşmeleri için satır listesi ayrı özel dosyada olmalı.
# Orijinal PDF + staging + satır bindings olmadan capture ASLA mühür yapmaz.
python experiments/263/serbest_analiz_v2/P0_HAFIZA_MUHUR_SONUC_ZINCIRI_V1.py capture \
  --staging mobil_hakem_aktarim_v1_2.json --pdf bulten.pdf \
  --bindings matches_to_verify.json --engine-root . \
  --out-dir experiments/263/serbest_analiz_v2/odds_receipts
```

**Kalan gerçek operasyon bağı:** Desteklenen maçlar için yeni KO öncesi P0/Hafıza kaydının GitHub kapısından canlı geçmesi ve sonuç sağlayıcısının bağımsız otomatik sorgu katmanı. Bunlar tamamlanmadan uçtan uca otomatik üretim hazır denmeyecektir.
