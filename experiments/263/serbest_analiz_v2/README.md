# Üçlü Sistem — Serbest Analiz V2 / Operasyon Paketi

**Tarih:** 23 Kasım 2026  
**Durum:** Modüler araştırma kodu ve mobil V1.3 kısmi oran ekranı yerel testlerden geçti. Ana 2.6.3 model kaynakları, eski mühürler ve Hakem V1 katsayıları değiştirilmedi. Resmî ön maç GitHub commit akışı **kuruldu ancak henüz gerçek yeni maç üzerinde denenmedi**.

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
- `.github/workflows/263-serbest-analiz-v2.yml`: kod güncellemesinde 9 regresyon kontrolü, ayrıca manuel `workflow_dispatch` ile doğrulanmış isimli kayıt yolu. GitHub Actions tetikleme arayüzü iş akışının default dalında olmamasından etkilenebilir.
- `.github/workflows/263-serbest-analiz-request-v2.yml`: chat'ten tek maç adıyla gönderilebilecek `requests/<benzersiz>.json` dosyasının araştırma dalına GitHub commit edilmesi üzerine çalışır; resmî fikstür + güncel veri + gerçek KO şartını sağlarsa yalnız **yeni** `official_receipts/` dosyasını başlangıç öncesi Git commit eder. Kaynak yoksa işlem başarısız olur; sahte sonuç yazılmaz.
- Kaydedilecek talep şeması: `{"schema":"SERBEST_NAMED_REQUEST_V2","league":"TUR1","home":"Besiktas","away":"Kasimpasa"}`. Bu yalnız **istek örneğidir**, gerçek maç doğrulaması değildir. Kullanıcı isteği olmadan otomatik sahte talep gönderilmez.
- **Önemli:** Workflow ve GitHub write permissions uygulama ortamında henüz gerçek yeni maç için doğrulanmadı. Bunun doğrulanması ve güncel ana futbol veri beslemesi halen operasyonel kabul kriteridir. Bu koda, bu koşul sağlanmadan “canlı olarak tam otomatik” denmemeli.

## Yerel testler

- Python modüler yönlendirici + eksik fiyat + P0/Hafıza + Hakem: **27/27**.
- Bağımsız saat/KO/gate/append-only güvenliği: **9/9**.
- Yeni Mobil V1.3: Chrome tabanlı tarayıcı DOM'da PDF.js'in metin öğeleri için simüle edilmiş geometrik çıktı ile **4/4 maç**, bir fiyatın kasıtlı eksiltilmesi, tam **35.938 Hafıza dosyası yükleme**, **4/4 benzerlik sayımı** doğrulandı. Cihazda gerçek PDF.js CDN indirimi ve Android dosya izinleri ayrıca denenmeli.
- Gerçek resmî yeni fikstür üzerinden GitHub Actions SHA mühürü **henüz denenmedi**; testlerde sahte takımlar gerçek maç gibi kaydedilmedi.

## İlk kullanım sınırları

PDF varsa ilk analiz yapılıyor. 10 ligden maç adı verilirse model kaynakları bulunduğunda araştırma analizi yapılabiliyor. Yeni canlı M4/C3 için güncel, kaynak onaylı maç geçmişi hâlâ gerekli. Orijinal resmî tahmin dalının sabah iş akışı *bu sürümde kapatılmadı*; yeni modüler yol ayrı bir alternatiftir. Bu düzeyde tamamlanan işler çalışır; canlı operasyonun son kabulü için gerçek bir yeni maç koşusu gerekir.
