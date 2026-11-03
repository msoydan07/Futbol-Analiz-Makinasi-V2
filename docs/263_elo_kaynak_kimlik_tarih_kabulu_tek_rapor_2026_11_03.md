# Futbol Maç Analiz Makinası 2.6.3 — Avrupa Elo tek kaynak kabulü: TOPLU SONUÇ

**Tarih:** 3 Kasım 2026  
**Durum:** KAYNAK KISMEN KABUL; TÜM 10 LİG İÇİN ELO KABUL EDİLMEDİ; MODEL VE PİLOT ONAYSIZ.  
**Kapsam:** UEFA CL/EL maçında iki takım da önceden onaylanmış 10 ligden birinde olacak. Kapsam kapısı, yerel makine ve \`main\` değişmedi.

## 1. Tek koşu ve tekrar kullanılabilir kanıt

- Tek planlı bütünlük iş akışı: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41582947375
- İş akışı: \`.github/workflows/263-elo-integrity-single-acceptance.yml\`
- Kod: \`experiments/263/europe/elo_integrity_acceptance_263.py\`
- Kanıt artifact: **263-uefa-elo-integrity-single-acceptance** (ID **13206273674**). İçinde \`single_integrity_report.json\`, \`identity_review_queue.json\` ve **aynı koşuda indirilen dört kaynak CSV** var. Önceki bağlantı testlerini yeniden çalıştırmaya gerek yok; sonraki kimlik incelemesi arşivlenmiş bu ham dosyalardan yapılır.
- Kaynak ve atıf: beyondELO (https://beyondelo.com), CC BY 4.0; API belgesi https://beyondelo.com/developers
- Bu GitHub koşusunun **SUCCESS** olması yalnız yazılımın tamamlanmasıdır; matematiksel kalibrasyon veya tahmin başarısı değildir.

## 2. Kaynak bütünlüğü: gerçek sonuçlar

| Kaynak | Gözlenen satır | Özellik |
|---|---:|---|
| Güncel \`club-ratings.csv\` | 1.472 | Güncel anlık liste; **39 satırda slug boş**, diğer alanları dolu |
| Tarihsel 2024–25 | 20.116 | **89 satırda club boş** |
| Tarihsel 2025–26 | 20.052 | **150 satırda club boş** |
| Tarihsel 2026–27 | 9.866 | **88 satırda club boş** |

- Tarihsel toplam **327 kimliği boş satır**, otomatik eşleştirilmedi. Üç tarihsel dosyada kulüp kimliği dolu satırlar arasında **aynı tarih + aynı kulüp için çelişkili sayısal Elo/RD çifti yok**.
- Tarihsel dosyaların sezon pencereleri birbirine taşıyor: farklı sezon dosyaları arasında **7.783 aynı tarih/kulüp/güç kaydı tekrarı** saptandı, bunlar bağımsız gözlem veya yeni maç değildir.
- Önceki 7/40/29 "aynı tarih-kulüp" tekrar sayılarının boş \`club\` kimliklerinden geldiği anlaşıldı: kimliği boş satırlar karantinaya alındığında her bir tarihsel dosyada kimliği belirli aynı gün-kulüp yinelenmesi **0**.
- Güncel dosyadaki boş \`slug\` satırlarının ülke kodları AZE, POL, AUT, CZE, NOR ve DEN; bu 39 boş güncel kimliğin hiçbiri doğrudan bizim dokuz birinci seviye ligimizden değil. Tarihsel boş \`club\` satırları ülke alanı içermediğinden aidiyetleri bilinmiyor, geri doldurulmadı.
- 2026–27 verisi, eski bağlantı koşusundaki 9.816'dan 9.866 satıra çıkmış. Eski CSV sürümü bugünkü veriyle aynı kabul edilemez.
- Tarihsel dosyalarda etiketlenen sezondan önce (Mart) başlayan tarihler var. Etiket, takvim sezonu ve bağımsız maç sayısıyla eşitlenmeyecek.

## 3. 192 takım kimliği için gerçek kapsam

İlk yeni bütünlük koşusunda **153** sıkı otomatik ad/ülke eşleşmesi adayı ve **39** inceleme bekleyen takım bulundu. Bu incelemeden sonra, **33 güncel isim/alias adayı**, **1 ülkeler arası lig üyeliği istisnası (Cardiff City)**, **4 güncel kayıtta bulunmayan kulüp** ve **1 gerçek kimlik çatışması** şeklinde açıklığa kavuştu. Böylece 39 açık vaka = 33 + 1 + 4 + 1. **34 alias/isim önerisi üretime onaylanmadı; kaynak ile resmî kulüp kimliğinin bağımsız eşleştirmesi tamamlanmalı.**

Önerilerin ayrıntılı, salt okunur dosyası: \`experiments/263/evidence/elo_provider_alias_review_only_2026_11_03.json\`.

**Kaynakta bulunmayan 4 kulüp (tamamı ENG2):** Bristol City, Lincoln City, Preston North End, Wrexham. Bu isimler diğer benzer isimli kulüplere yakınlık puanıyla bağlanmayacak.

**Çatışmalı 1 kulüp (TUR1):** resmî kayıt \`ERZURUMSPOR FK\`; beyondELO'da iki ayrı kaynak kimliği var:
- \`erzurumspor\`: 31 Ekim 2026 son maç, \`is_ranked=true\`;
- \`erzurumspor-fk\`: 11 Mayıs 2021 son maç, \`is_ranked=false\`.
Birini seçip eskisinin geçmişini ona bağlamak, bağımsız kimlik/isim değişikliği kanıtı olmadan yasak. Bu nedenle bu kulüp ihtiyatla belirsiz.

**Cardiff City istisnası:** Kulüp İngiltere lig üyelik kapsamımızda (ENG2), sağlayıcının \`country_code\` alanı ise \`WAL\`; bu bir ülke-lig üyeliği istisnasıdır. Dolayısıyla her ENG2 kulübünü körlemesine \`ENG\` ülke koduna zorlamak doğru değil. Kaynak satırı var, ancak son puanlanan maç **12 Mayıs 2019** olduğu için bugün güncel Elo verisi sayılmaz.

## 4. 10 ligde "güncel Elo" ile "arşiv Elo" ayrımı

Tek başına \`club-ratings.csv\` içinde bir sayı bulunması, 2026/27 maçlarını izlediği anlamına gelmez. Salt \`is_ranked=true\` da yeterli değil: örneğin Southampton kaydı listede ranked olsa da son puanlanan maç **25 Mayıs 2025**.

**Kaynağın son puanladığı maçın Kasım 2026'ya yakınlığı** esas alındığında:

| Lig | Güncel kaynak eşleştirme adayı / kapsam |
|---|---:|
| BEL1 | 18 / 18 |
| ENG1 | 20 / 20 |
| ENG2 Championship | **0 / 24** |
| ESP1 | 20 / 20 |
| FRA1 | 18 / 18 |
| GER1 | 18 / 18 |
| ITA1 | 20 / 20 |
| NED1 | 18 / 18 |
| POR1 | 18 / 18 |
| TUR1 | **17 / 18** (1 belirsiz kimlik) |
| **Toplam** | **167 / 192** (aday; onaylı üretim kimliği değil) |

Buradaki **167**, otomatik eşleşmelerle birlikte henüz teyit edilmemiş 34 önerinin ilgili güncel bölümünü de içerir; "167 takım doğrulanarak modele entegre edildi" anlamına GELMEZ.

**Önemli:** Championship'in 24 takımının 4'ü güncel sağlayıcı dosyasında hiç yok, kalan 20'sinin son puanlanan maçı Ağustos 2026 öncesine dayanıyor. Örneğin Stoke City'nin kaynak tarihindeki son puanlanan maç Mayıs 2018; Mayıs 2026'da puanlanmış West Ham/Wolves/Burnley de Championship'te oynadıkları yeni sezonun taze Elo'suna sahip değil. Bu 24 takıma eski puanları **güncel güç** diye atama yapılmayacak. On lig kapsam politikası DEĞİŞTİRİLMEYECEK; Elo kaynağı o kulüpler için güvenilir değilse analizde açıkça gösterilecek.

## 5. Tarihsel tahmin ve çifte sayım açısından güvenlik

1. beyondELO geliştirici belgesi kulüp geçmişini **maçtan sonraki rating** olarak tanımlıyor. Geçmiş maç öncesi temsil için **aynı günün** Elo satırı kullanılamaz; yalnız fikstür tarihinden önceki güvenilir gözlemler adaydır.
2. Tarihli CSV bir gözlemin o tarihte internette **ilk yayımlandığını kanıtlamaz**. Olası geriye dönük düzeltmeler nedeniyle "tamamen sızıntısız tarihsel backtest" iddiası onaylanmadı. Bundan sonraki gerçek maçlar için kaynak anlık görüntüsünü önceden saklayıp \`first_seen\` zamanını kilitlemek daha güçlü kanıt olur.
3. Elo doğrudan skor, gol lambda'sı veya 1X2 kazanma yüzdesi değildir. Aynı bilgi lig katsayısıyla ikinci kez sayılmayacak. Ağırlık/kalibrasyon ayrı geçmiş dönem testi gerektirir.
4. Yeni xG/xGA/H2H veya 576 maçlık yeni Elo modeli açılmadı. B/C2/C3/M4, kapsam kapısı, 10 lig yerel raporu, \`main\`, pilot 0/100 korundu.

## 6. Nihai kaynak kabul kararı

- **KABUL:** beyondELO açık CSV erişimi, dört tarihlendirilmiş dosyanın bu koşuda saklanması, eldeki güncel maç takibi bulunan dokuz üst lig için **koşullu güç-verisi adayı** olarak kullanılabilmesi (kimlik onayı ayrı).
- **KABUL EDİLMEDİ:** beyondELO'nun on ligin tamamında, özellikle ENG2'de **güncel ortak Elo** sağladığı iddiası.
- **KARANTİNA:** kimliği boş tarihsel kayıtlar, boş slug'lar ve Erzurumspor kimlik çatışması; bağlantısız takımlara başka kulübün Elo'sunu atama yasak.
- **AÇIK:** 34 isim önerisinin bağımsız kulüp kimliği eşleştirmesi ve tarihsel ilk-yayın/anlık-görüntü sınırlaması.
- **KESİNLİKLE YOK:** Elo→Poisson katsayısı entegrasyonu, tarihsel başarı yüzdesi, canlı tahmin/pilot ve \`main\` değişikliği.

**Tek mühendislik kararı:** Mevcut dört CSV'yi yeniden indirmeden, saklanan anlık görüntüler üzerinden kimlikleri netleştirme ve kullanılabilir dokuz üst liglik alt kümeyi güvenli biçimde hazırlama; Championship eksikliğini kaynak gerçeği olarak kaydetme. Matematiksel model karşılaştırması ancak kimlik ve as-of kapısından sonra, önceden planlanmış tek ayrı testle değerlendirilebilir.

— 3 Kasım 2026, yalnız \`experiment/263-toplu-karsilastirma\` denetim kapsamı.
