# FUTBOL MAÇ ANALİZ MAKİNASI 2.6.3 — KALICI MOBİL MAÇ TABLOSU
**Kullanıcı tarafından 7 Kasım 2026'da açıkça ONAYLANDI. Yeni sohbetlerde varsayılan kullanıcı ekranıdır.**

## Varsayılan görüntü
Kullanıcı "ortak, bugünün maçlarını getir/analiz et" veya "maçları göster" dediğinde, **maçların ana karşılaştırma ekranı** aşağıdaki sıkı, dikey telefona tam oturan **PDF düzeni** olmalı. Yatay sağa-sola kaydırılan geniş Markdown tablo veya açılınca kaynak kod gösteren HTML dosyası OLMAMALI.

Üst satırda her maç için:
- **TSİ saat | Maç (iki takım) | MS1/MSX/MS2 yönü | BİZİM % | PİYASA % | FARK (yüzde puan)**.
- Piyasa yüzde, yalnız aynı MS yönündeki **gerçek, güvenilir, saatli h2h 1-X-2 oranlarından marj çıkarıldıktan sonra** hesaplanır. Piyasa % yoksa açıkça **— / ORAN YOK** göster. Eski üçüncü taraf fiyat gözlemini asla canlı Pinnacle API diye sunma.
- FARK = bizim **kalibre MS olasılığımız (%) − marjsız piyasa MS olasılığı (%)**, artı veya eksi işaretiyle. Fark bir bahis önerisi veya onaylanmış value seçim değildir.
- **GÖRÜNÜR ORAN SAYILARI YOK** (1/X/2 fiyat rakamlarını tabloya koyma): kullanıcı Türkiye oranlarıyla karıştırmak istemiyor. Oranlar içte/kanıt ekinde saklanabilir; hesaplamaya devam et.

Her maçın hemen ALT satırında, aynı genişlikte yatay dört kısa kutucuk:
**KG Var % | 1,5 Üst % | 2,5 Üst % | 3,5 Üst %**.
- Bunlar MODEL yüzdeleridir; MS kalibre % ile aynı tür olmadıkları durumda **ham medyan/model tahmini** etiketi rapor başında görünür olmalı. Eksikse sayı uydurma.
- Kullanıcı özellikle alt satırın bu biçimde aynı kalmasını istedi.

## Görsel düzen
- Dar telefon ekranına uygun, mümkün olduğunca küçük ama okunaklı font ve sıkı satır/sütun aralıkları, uzun isimleri sınırlı ölçüde kısalt.
- Tek maçın iki satırı bir bütün; ince ayraç/alternatif satır gölgesi, çok açık mavi-gri kutucuklar. Fazla dekorasyon yok.
- 44 maç bile olsa tablo 4-7 PDF sayfasına dikey ilerleyebilir; **ekran eninde hepsi birlikte görülür**, yatay kaydırma YOK.
- Önceden onaylanan örnek: **7 Kasım 2026 “ESERİMİZ — 44 maç mobil” PDF**. Görünümün esas unsurları yukarıdakilerdir; eski/bugüne ait yüzdeleri yeni tarihlere kopyalama.
- **Üç ayrı tablo değil**, tek ana oranlı karşılaştırma tablosu önceliklidir. Detaylı dört model, kaynak, oranın sayısal değeri, S1/S2/PAS, SHA mühür kanıtları ikinci ekranda veya dosya ekinde sunulabilir; asla rapordan çıkarılmış gibi davranma.

## Operasyon ve veri doğruluğu
- Kullanıcının maç sabahı talebi ana tetikleyici. Geliştirme dalındaki analiz penceresi TSİ 05:00-14:59; kullanıcı en geç 14:00 civarında yazar.
- B/C2/C3/M4 modeli, resmî fikstür ve takım kimliği, tahmin öncesi kickoff kontrolü, SHA/ekler ve varsa güncel The Odds API Pinnacle koşulu korunur.
- MS piyasa % yalnız gerçekten doğrulanmış fiyat varsa. KG/Üst için piyasa oranı bulunmamışsa yalnız model yüzdesi gösterilir; yüzde yanına bahis oranı icat edilmez.
- Seçim konusunda PAS veya onaysız araştırma uyarılarını olasılık tahminiyle karıştırma. Önceden mühürlü tahminleri görünüm için tekrar hesaplama veya değiştirme.
- Bunun yeni sohbetlerde kullanılması için bu dosyayı ve ana proje raporunu esas al. Sohbet belleği tek başına çalıştırılan PDF çıktı motorunun yerini tutmaz.
- Yeni mobil rapor üreticisi uygulandığında testte **sütun taşması/maç eksikliği/veri-piyasa hizası** kontrol edilmeli. Mevcut append-only mühürlü Markdown raporları toplu olarak değiştirme.

## Tek cümlelik yeni sohbet başlangıcı
**“Ortak, bugün maçları getir ve Futbol Maç Analiz Makinası 2.6.3’ün GitHub'daki `docs/263_KALICI_MOBIL_ORAN_KG_UST_GORUNUMU_2026_11_07.md` dosyasındaki ONAYLI mobil PDF ekranını kullan: maç + MS yönü, BİZİM %, PİYASA %, FARK; alt satır KG Var, 1,5/2,5/3,5 Üst. Oran sayılarını gösterme.”**
