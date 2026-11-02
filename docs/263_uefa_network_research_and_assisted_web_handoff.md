# 2.6.3 — UEFA canlı bağlantı engeli: tek teşhis, güvenli web destekli alternatif

**2 Kasım 2026. Durum: Resmî sayfaya GitHub runner bağlantısı hâlâ BAŞARISIZ;
ChatGPT web kaynağından elle doğrulanmış kaynaklı veri aktarımı uygulandı.**

## Bağlantı teşhisi (neden)

https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41470705155

Aynı GitHub Actions runner üzerinde sadece **bir** kontrollü karşılaştırma yapıldı:
- `raw.githubusercontent.com`: DNS başarılı, HTTP 200, 0.14s.
- `www.uefa.com` hem 2026/27 CL resmî haber URL'si, hem kök sayfa:
  DNS IPv4 23.45.46.208/209; HTTPS read **TimeoutError** ≈5s.
- `editorial.uefa.com`: aynı DNS IP aralığı, HTTPS **TimeoutError**.
- `documents.uefa.com`: **HTTP 200**, 0.43s, farklı IP/CDN.

**Sonuç:** Kaynak URL hatası değil; GitHub çıkışı ile belirli UEFA CDN /
sunum servisi yolundaki erişim sorunu güçlü biçimde destekleniyor.
Akamai'nin kasten engellediği, UEFA'nın özel yasak uyguladığı veya
geçici ağ güvenlik politikası olduğu gibi daha kesin nedenleri
bu testten çıkarmak mümkün DEĞİL. Kaynağı zorla aşacak proxy,
scraping veya sahte domain denenmeyecek.

`documents.uefa.com` yalnız regülasyon ve maç takvimi sağlar; kulüplerin
2026/27 tekil maç eşleşmelerini ve saatlerini onun içinden
**çıkaramayız**.

## Güvenilir yol — tek kaynak ChatGPT üzerinden

ChatGPT web kaynağı resmî 2026/27 CL ve EL UEFA sayfalarını 2 Kasım
günü **doğrudan açabildi**. Bu sayfalardan yalnız gerçek maçın
kaynak adı / tarih / saat / turnuva kayıtları alındı:
- CL: https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/
- EL: https://www.uefa.com/uefaeuropaleague/news/02a8-2174cafa5bb6-82bbc20c9b92-1000--2026-27-europa-league-all-the-league-phase-fixtures-and-results/

Bu kayıtlar **tüm UEFA fikstürünün kopyası değil**, yalnızca
kapsam kontrolüne aday birkaç seçili maçın olgusal referansları.
Kullanıcı 'maç bul' demedikçe otomatik maç önerisi/taraması yok.

`uefa_web_evidence_handoff_263.py` sırasıyla:
1. **Her zaman önce 10 lig kapsam kapısını** çağırır.
   Celtic vb. kayıt dışı eşleşmelerde dosyayı bile açmaz.
2. Sonraki aşamada kaynak dosyasının şemasını, sabit UEFA
   resmî sayfa URL'sini, kaynakta açık 21 CET varsayılanını,
   maç gününü, haftasını, açık maç satırını ve ev/deplasman
   canonical eşleşmesini kontrol eder.
3. Web kaynağı gözlem tarihini en fazla **1 gün** eski kabul eder,
   maç başlangıcı gelecek 7 güne girmelidir. Yanlış saat,
   takım, turnuva, tarih ya da eski gözlem reddedilir.
4. Sonuç ayrı adla üretilir:
   `ASSISTED_WEB_OFFICIAL_ARTICLE_FIXTURE_REFERENCE_ACCEPTED`.
   **GitHub runner tarafından resmî kaynak canlı yeniden doğrulanmış
   gibi gösterilmez.** Kaynak olgusu web incelemesinde doğrulandı,
   ancak repo içi JSON tek başına bağımsız orijin kanıtı değildir.
5. Kadro/xG/istatistik/model/sonuç/EV/A-B-C/pilot yoktur.
   Kaynağı otomatik indirme sorunu **çözülmüş sayılmaz**.

Örnek resmî sayfadan 2 Kasım'da doğrulanan gözlem paketinin
adı: `experiments/263/evidence/uefa_web_2026-11-02_review_only.json`.
Kaynak doğrulaması eskiyse otomatik sonuç çıkarmak yerine yeni
web incelemesi gerekir. Kullanıcıya üçüncü taraf ligleri
elle araştırma görevi verilmez; ChatGPT kaynakla ilerler.

## Tekrarsızlık ve devam kararı

İlk 15/15 fixture/10-lig güvenlik testleri zaten geçti.
GitHub Actions otomatik `www.uefa.com` denemesi başarısızdı.
Ek ağ teşhisi bir kez tamamlandı. Artık aynı ağ testini
her seferinde tekrar başlatmayacağız.

Sıradaki **ayrı iş paketi**: Resmî kaynaktan tarihli UEFA takım kimliği
kanıtı ve mevcut 10 ligin dahil olduğu eşleşmelerin güvenilir
pre-match güç köprüsü için verisinin eşleştirilmesi. Bunun için
geçmiş H2H, kapsam dışı ligler veya keyfî motivasyon katsayısı
araştırılmayacak. Henüz canlı tahmin motoru yok.
