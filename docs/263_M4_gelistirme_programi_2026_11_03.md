# M4 GELISTIRME PROGRAMI — 2026-11-03
## Durum
PLAN KILITLENDI / ASAMA 1 VE 2 TAMAMLANDI (2024/25 ARASTIRMA ONLY) / ASAMA 3 HATA ANALIZI SIRADA.
Dal: `experiment/263-toplu-karsilastirma`. Canli motor, main, B/C2/C3/M4 tahmin kurallari, 100 maclik ileri pilot ve eski raporlar DEGISTIRILMEZ.
Yeni bir model terfi ettirilmez. Tum deneyler yalniz arastirma havuzunda.

## Neden yapiyoruz?
Soru: M4'un C3'e karsi beklenen faydayi gostermemesi yetersiz gecmis, zaman agirligi, ek takim-saha parametreleri, rakip gucu veya eksik xG bilgisinden kaynaklaniyor olabilir mi?
Hicbir neden pesinen dogru sayilmayacak. Modelde olmayan bir ozellige 'yanlis agirlik' denmeyecek.

## Sabit calisma asamalari
1. **Kaynak envanteri + ilk kabul incelemesi:** 2024/25 on lig skor arsivlerini tek kaynakla bul; kaynak commit/hash, mevcut skorlar, eksik skorlar, sezon formatlari, playoff farklari, lisans ve ikinci kaynak teyidi durumlarini listele.
2. **Izole gecmis havuzu:** Yalniz gercekten dogrulanan 2024/25 maclarini kabul et. Takimlari ulke/sezon uyeliklerine ve mevcut resmi kimlik sozlugune guvenli bagla; yeni tarihi takimlar icin ayrica kimlik kaydi uret; hatali/eslesmeyen satirlari karantinaya al. Eski 4.413 satiri kesinlikle degistirme. Ayni takim eslesmesinin ayni sezonda tekrarlandigi playoff maclarini yanlislikla duplicate sayma; kimlikte tarih/tur/ayri mac anahtari kullan. Eski `season_refresh_263.py` sadece 2026/27 append-only akisi icin, 2024/25 importuna aynen uygulanmaz. Iki ayri veri havuzu raporla.
3. **Salt-okunur M4 hata diagnostigi:** Eski 880 test macinin ayni ortaktakim/lig penceresinde C3 ile M4 farklarini, favori, ev/deplasman, mac evresi, gol bandi, olasilik guveni ve lig kirilimiyla arastir. Test kohortu gelistirmede goruldu; bagimsiz final degil.
4. **Ablasyon / toplu karsilastirma:** C3, C3+zaman, C3+takima-ozel-saha, eski M4, M4+2024/25 gecmis. Her aday ayni maca, ayni kesim tarihine, ayni temel kaynak donemine tabi. 2024/25 bilgisi ileri tarihli egitime sizmaz. Hiperparametre adaylari testten ONCE sinirlanip kilitlenir. M4 eski SHA ve mevcut pilot ayarlari degismez.
5. **Opsiyonel xG kolu:** Gercek match-level xG ve kaynak zaman damgasi mevcutsa, yalniz ayni maclarin karsilastirmasinda ayri aday. Bes xG-eksik ligi tahmini xG ile gercek veri diye doldurma. UEFA xG'siz veri politikasini DEGISTIRME. Eski xG deneylerini tekrarlama.
6. **Tek karar raporu:** Her pazarda (MS, KG, 1.5, 2.5, 3.5) n, dogru, yanlis, isabet%, basit lig referansi, es kapsam, log-loss, Brier, guven/kalibrasyon, tarih bloklu belirsizlik ve lig kirilimi. Maç sonu korner ayri model/pilot; kanit yoksa M4 basarisi sayilmaz. Tek toplu deney, tekrarli ayar avciligi yok. 2025/26 ve 2026/27 gorulmus kohortlari HICBIR ZAMAN dokunulmamis final degildir; gelistirilen adaylar yalniz daha sonra gercekten yeni maclarda onkayitli test edilir.

## Asama 1: salt-okunur gercek kaynak on taramasi
Kaynak: openfootball/football.json, public domain CC0; `2024-25/*.json`, commit `e6744429ee395bc86f247348c6184bb08d4eb361`.
URL: https://github.com/openfootball/football.json/tree/e6744429ee395bc86f247348c6184bb08d4eb361/2024-25
Kaynak dosyalari gercekten tek tek okunarak JSON `matches[]` ve `score.ft` alanlari sayildi. Bu sayim bagimsiz mac-sonuc dogrulamasi DEGILDIR.

| Lig | Kaynak | Toplam kayit | Son skor mevcut | Skor eksik |
|---|---|---:|---:|---:|
| ENG1 | en.1.json | 380 | 380 | 0 |
| ENG2 | en.2.json | 557 | 557 | 0 |
| GER1 | de.1.json | 306 | 306 | 0 |
| ESP1 | es.1.json | 380 | 370 | 10 |
| ITA1 | it.1.json | 380 | 370 | 10 |
| FRA1 | fr.1.json | 306 | 306 | 0 |
| NED1 | nl.1.json | 306 | 306 | 0 |
| TUR1 | tr.1.json | 342 | 338 | 4 |
| POR1 | pt.1.json | 306 | 306 | 0 |
| BEL1 | be.1.json | 313 | 313 | 0 |
| TOPLAM | 10 dosya | 3576 | 3552 | 24 |

Ayrintilar:
- ESP1 / ITA1 dosyalarinda son hafta (Matchday 38) 10'ar macin `score.ft` alani bos; TUR1 son haftada 4 mac eksik. Bu sonuc dosyada yok diye mac oynanmadi anlamina GELMEZ; bagimsiz kaynaktan teker teker dogrula veya karantina.
- ENG2 557 satir regular sezon + playoff; ayni ev/deplasman eslesmesinden tekrar olan 5 farkli ikili var.
- BEL1 313 satir regular + championship/europe/relegation playoff; ayni ev/deplasman eslesmesinden tekrar olan 73 farkli ikili var. Bunlar otomatik silinmeyecek; tarih/tur kontrol edilecek.
- JSON'da `score.ht` bazi maclarda olabilir ama bu xG, korner veya sut istatistigi saglamaz.
- football-data.co.uk'nin guncel izin politikasi otomatik yuklu AI/training icin kisitlamalar belirtiyor: yeni tarihsel toplu veri icin izinli CC0 kaynagi onceliklidir. https://football-data.co.uk/contact.php
- Bu kaynaklardan HICBIRI henuz resmi fikstur/kulup kaynagiyla capraz dogrulanmadi. Lisans kaynagin kendisinde CC0; orijinal kayit dogrulugu ayri kalitedir.

## Siradaki TEK is
Asama 1 kabulunu tamamla: 24 skorsuz macin karsilastirilabilecegi guvenilir kaynaklari belirle, 10 lig icin sezonsal mac sayisi / final-tur / kaynak kimligi listesini olustur, 2024/25 kadro kimliklerinin mevcut 215 takimli kapsama nasil baglanacagini raporla.
Henüz 2024/25 veri importer'i yazma, eski modelleri yeniden kosma, Actions workflow baslatma, ana dala yazi yazma. Sonraki is Aşama 2 izole toplu veri kabuludur.


## 2026-11-03 uygulama kaydi
Aşama 1 sonuç ve alt dosyalar: [263_M4_2024_25_asama1_kabul_2026_11_03.md](263_M4_2024_25_asama1_kabul_2026_11_03.md).
3.576 2024/25 skor kaydı araştırma olarak kaydedildi. 24 skorsuz maç kaynaklı tamamlandı. 75 mevcut kesin isim eşleşmesi, 96 onay bekleyen mevcut takım adayı, 20 ayrı tarihsel takım kaydı gereksinimi belirlendi. Ana veri değişmedi. Sıradaki iş yalnız 2024/25 kimlik katmanının toplu kabulüdür.


## 2026-11-03 Aşama 2 tamamlandı
- [2024/25 kimlik ve veri kabul raporu](263_M4_2024_25_asama2_kabul_2026_11_03.md)
- 3.576 geçmiş maç ayrı araştırma CSV'sinde, 191 lig/takım kimliği benzersiz, 20 yeni tarihsel kayıt, 78 playoff ayrı, 12 temel QA kontrolü geçti.
- Yeni sezon verisi C3/M4 üretim koduna aktarılmadı. Sırada 880 maçın eski tahminlerinin salt okunur hata ayrıştırması var.

## Aşama 3 — 2026-11-03 ilk yeni teşhis
2025/26+2026/27 dondurulmuş 4.413 maç geri çağrıldı ve hash doğrulandı. **880 maçlık yalnız sayım/örneklem diagnostigi** yeni çalışıldı; eski C3/M4 performans yeniden hesaplanmadı. 
- 272/880 maçta en az bir tarafın 2025/26 aynı lig tarihçesi yok.
- 775/880 maçta en az bir tarafın cari sezon bağlamındaki iç/dış saha örneği 4'ten az.
- 2026/27 lig girişlerinde 31 takım-lig yeni; eklenen 2024/25 aynı lig geçmişi bu 31'in yalnız 7'sini karşılıyor.
- İlgili aşama kanıt dosyası: [M4 Aşama 3 ilk yeni veri teşhisi](263_M4_asama3_veri_yeterliligi_teshisi_2026_11_03.md).
- **Durum:** Veri yetersizliği teşhisi tamam; 880 maçın C3/M4 bireysel olasılık defterleri mevcut eski arşivde bulunmadığından özgül tahmin-hata profili **henüz tamamlanmadı**.
- Tek sonraki iş: dondurulmuş kaynak ve aynı C3/M4 kodlarıyla bir defalık kayıtlı `matched error profile` tanısı; eski aggregate ölçütlere eşleşmezse sonuçları karantinaya al. Bu adım formül tuning veya ana model güncellemesi değildir.
