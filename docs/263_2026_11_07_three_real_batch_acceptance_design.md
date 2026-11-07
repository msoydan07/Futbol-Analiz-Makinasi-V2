# 2.6.3 — 7 Kasım gerçek üç-maç GitHub ve mobil kabulü

## Amaç
18 resmî kaynak+takım kimliği kontrolünden geçmiş maçtan üçü için tek mühendislik kabulü:

- ESP1: Valencia – Real Madrid; 2026-11-07T20:00:00+00:00
- ENG1: Arsenal – Hull City; 2026-11-07T15:00:00+00:00
- TUR1: Samsunspor – Konyaspor; 2026-11-07T13:00:00+00:00

Bu saatler yalnız **ön kanıttır**; yeni GitHub Actions çalışması her maçı yeniden canlı resmî sayfada ve eşsiz takım/lig kimliği kapısında doğrular. Verilen saatler doğrulanmış kabul edilerek tahmin başlatılmaz.

## Kesin mühendislik sınırları
- acceptance3 = ayrı en fazla üç maçlık teknik test; **eski 96-match** ve **yeni 100-match** ileri pilotu değiştirmez, hiçbir sayaca eklemez.
- Yeni tahminler yalnız forward_acceptance_263/YYYY-MM-DD/SHA.json altına; dört model B/C2/C3/M4 orijinal dondurulmuş motorlardan, güncel sınırlı araştırma-kabul kaynağından üretilir.
- Her birinde dört model AVAILABLE, geçerli baselines, DEV karar kilidi ve gerçek oran olmadan RESEARCH_PAS şarttır. S2 ana/alternatif bahis YOK.
- Kaynak SHA ve geçerli insan inceleme penceresi korunur; 4518 dosyanın tamamının bağımsız doğrulandığı iddia edilmez.
- Tek toplu özet ve üç tekli telefon sayfası mühürlü SHA ile **birebir yeniden üretilebilir** olmalıdır. Karar yoksa kayıt başarılı sayılamaz.
- GitHub commit işleminden önce ve rebase sonrasında tekrar **kickoff'a en az 2 dakika** kala kontrol edilir. Uygun değilse commit/push yasak.
- Yeni tek sabah_acceptance_requests/20261107_three_real_acceptance.json dosyasının eklendiği commit workflow tetikleyicisidir; bu manifest haricinde otomatik maç seçim işlemi yapılmaz.
- Pinnacle ve bookmaker anahtarları, oran API'si, tahmin kalibrasyon değişikliği ve bahis modeli KAPALI.
- Deney dalı: experiment/263-toplu-karsilastirma; main'e değişiklik yok.
- Tek kabul: 3 gerçek forecast SHA, 3 tarihsel baseline, 3 decision PAS SHA, 1 batch report, 1 mobil summary ve 3 mobil single, 1 karşılaştırmalı acceptance receipt, başarılı GitHub push ve uzak git ref kanıtı.

**Teknik sıralama:** önce sadece offline testler; yeşil olursa yeni request tek commit. GitHub run tamamlanmaz veya hata alırsa kullanıcıya başarılı mühür iddiası yapılmaz.
