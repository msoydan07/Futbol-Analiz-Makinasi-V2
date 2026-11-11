# 2.6.3 — İddaa PDF önce, tek resmî fikstür kontrolü, dört model, oranlı PDF

**Tarih:** 11 Kasım 2026 | **Güvenlik:** Deney dalı `experiment/263-toplu-karsilastirma`; ana motor ve 96 mühürlü pilot değişmez. Ana 10 lig yalnızca: ENG1, ENG2, GER1, ESP1, ITA1, FRA1, NED1, TUR1, POR1, BEL1. LITE ve basketbol ayrı.

## Kabul edilen kullanıcı iş akışı

1. Kullanıcı iddaa.com **futbol bülteninde** yalnız istediği kapsam liglerini filtreleyip tarayıcının **Yazdır → PDF olarak kaydet** seçeneğiyle **tek PDF** verir. İddaa PDF'si maç listesi + **oranlar için birinci kaynak**, ayrıca ikinci bir bahis operatöründen oran teyidi istenmez.
2. PDF'nin metin sütunları topluca okunur; **MS1/MSX/MS2, 2.5 Alt/Üst, KG Var/Yok**. **1.5 Üst ve 3.5 Alt, ayrıca bütün 1.5/3.5 pazarları raporda yasak**. Karşıt fiyat eksikse sadece o pazar no-vig dışıdır; diğer pazarlar ilerler.
3. Mevcut SHA-kilitli takım siciline ek bir alias çözümleyici team UUID'si bulur. Kısaltılmış veya belirsiz isim sadece ilgili maçı ayırır; yanlış ev/deplasman eşleştirmesine izin yok.
4. Mevcut 10 federasyon/lig/kulüp resmî adapterinden **tek sorgu / maç** yapılır. Maçın iki ekibi, tarih, saat, source host ve henüz başlamamış olması kontrol edilir. Adapter sorguları **en çok beş eşzamanlı** yürütülür; aynı maç için defalarca alternatif kaynak yoktur. **Bu sürüm lig başına tek HTTP isteği değil, maç başına tek mevcut resmî adapter çağrısı kullanır**; yerinde farklı bir şey iddia edilmez.
5. Resmî olarak doğrulanmış ve verisi yeterli maçlar, **eski matematik kodu değiştirilmeden** `forward_quad.predict_quad_from_verified_gate` yoluyla B/C2/C3/M4 hesaplarına bağlanır. Model tahmini PDF'den *sonra* oluşturulur ve ayrı SHA ile kaydolur. Orijinal 96 maçlık dosyalara dokunulmaz. Tarihsel kaynak güncel/as-of değilse model engel verir; başka maçların çalışması devam eder.
6. Siyah-beyaz, 7 oranlı, seçilebilir metinli, telefon uyumlu PDF raporu oluşturulur. **M4 ham % ile piyasanın marjsız % farkı bilgilendirme amaçlıdır.** Dört modelin temel yüzdeleri varsa gösterilir.
7. **Tamamlanmamış kalan ayrım:** eski `four_model_value_policy_263.py` fiyatın tahminden *sonra* en çok 10 dakika içinde gözlenmesini bekler. Yeni PDF-first akışı bununla henüz güvenilirce birleştirilmedi. Bu nedenle **ana/alternatif bahis önerisi üretimi şu an bilinçli PAS**; sadece geçmiş matematik yüzdeleri + kaynak fiyatı + piyasa farkı gösterilir. Geçerli tahmin/kod veya olumlu EV kanıtı gibi sunulmaz. Bir sonraki tek kapsamlı iş: PDF-first SHA'lı fiyat snapshotını mevcut donmuş geliştirme kalibrasyonuna bağlayarak fiyat zamanı farklılığını `ARCHIVED_PDF_PRE_FORECAST` şeklinde sınıflandırmak ve tüm karar şablonlarını topluca test etmek. Fiyatı canlıymış gibi yeniden adlandırmak yasak.

## Eklenen dosyalar

- `iddaa_pdf_team_alias_preflight_263.py`: 215 mevcut takım UUID'sini korur, daha önce gözlemlenmiş 20 dış isim biçimini aynı kimliklere bağlar.
- `iddaa_pdf_bulletin_263.py`: gerçek Chrome/Android print-to-PDF metin/koordinatlarını, PDF SHA ve oluşturulma saatini alır; fiyat hücresini asla komşu pazarına kaydırmaz.
- `iddaa_pdf_session_263.py`: on maç/lig sayısı ne olursa olsun satır bazında hızlı resmî kaynak kontrolü, 3 pazarda no-vig ve (isteğe bağlı) önceki B/C2/C3/M4 matematik çağrısı.
- `iddaa_pdf_report_263.py`: siyah-beyaz ayrı maç kutuları, yedi oran, M4/piyasa/fark, dört model özet ve **PAS korunumu**.
- `test_iddaa_pdf_*_263.py`: fixture kimliği, ters takımlar, tek resmî sorgu, geç kalan PDF, eksik fiyat, Türkçe font/PDF rapor, sahte onay/PAS testleri.
- `.github/workflows/263-iddaa-pdf-team-alias-bulk-preflight-ci.yml`: tek GitHub Actions işinde ilgili testleri yürütür; dış bahis fiyatı API'sine hiç çıkmaz.

## Hazır komutlar (yerel repo veya kullanıcı PDF'si erişimli çalışma ortamı)

Python bağımlılıkları: `PyMuPDF`, `reportlab`; yalnız dört model etkinleştirilirse mevcut proje matematik bağımlılıkları.

```bash
export PYTHONPATH=experiments/263
python experiments/263/iddaa_pdf_bulletin_263.py \
  --pdf /path/to/kullanicidan-iddaa.pdf --out /tmp/iddaa_bulten.json

# Bu adım gerçek mevcut resmî federasyon adapterlerine ağ erişimi gerektirir.
python experiments/263/iddaa_pdf_session_263.py \
  --intake-json /tmp/iddaa_bulten.json --out /tmp/iddaa_oturum.json \
  --history /path/to/verified_historical_results.csv \
  --m4-lock experiments/263/m4_lock.json \
  --baseline /path/to/accepted_baseline.csv \
  --source-acceptance /path/to/accepted_source.json

python experiments/263/iddaa_pdf_report_263.py \
  --session-json /tmp/iddaa_oturum.json --out /tmp/263_oranli_rapor.pdf
```

Sadece fikstür testinde `--history` bayrağını çıkar; resmî kontrolü ve fiyat kıyasını çalıştırır fakat **model yüzdesi üretmez**.

## Fiilî test kanıtı ve sınırlar

- Kullanıcının 11 Kasım 2026 tarihli 3 sayfalık **gerçek iddaa.com PDF'si** yerel görsel/metin incelemesinde **30 maç satırı** içeriyor. **28 satırda 14 sıralı fiyat sütunu**, **2 satırda 13 sütun** var; son ikisi güvenli biçimde şüpheli kabul edilir. Bu PDF'deki organizasyonlar ana 10 lig kapsamında değil; **gerçek 10 lig fiyatı/isim eşleşmesi başarısı varmış gibi iddia edilmez**.
- Mevcut 8 Kasım 2026 haricî arşiv (iddaa değil): dokuz lig, 43 karşılaşma, 86 kulüp adı kullanımı. Eski aliasla 66/86, yeni aliasla 86/86; bu iddaa isim garantisi değildir.
- GitHub eylemi: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43053085410 — ilk birleşik tur **28 testin 28'i geçti**. Son güvenlik değişikliğinden sonra testin yeniden yeşil olması gerekir.
- Bu sürüm gerçek kapsam maçının **canlı federasyon + B/C2/C3/M4 + PDF-first kalibre değer seçimi uçtan uca kabulünü henüz tamamlamadı**. Eski dönem pilotu / tahmin doğruluğu garantisi değildir. Maç günü yeni örnek PDF ile bir kez, toplu kabul gereklidir.

## Akışın tekrar etmeme kuralı

**Bir PDF al → toplu satır ayıklama → her resmî fixture için en çok bir çağrı → analizi çalıştır → tek PDF.** Eksik tek pazar, bilinmeyen tek isim veya tek resmî kaynak hatası diğer maçları bloke etmez. Tamamlanan maçları tekrarlı olarak ikinci odds sitesine gönderme veya artık başlamış maçın fiyatını yeniden öncesiymiş gibi yazma. Eski/Pinnacle API kota tüketimi bu yolun parçası değil.

## Mevcut durum defteri

- Yeşil: PDF kolon çıkarımı + 215 takım aliasları + resmî tek-sorgu simülasyonu + no-vig + Unicode PDF renderer + 28 alt test.
- Açık: Gerçek 10 lig İddaa PDF başlıklarının/görünür takım adlarının ilk canlı kabulu; gerçek resmî adapter ve dört model uçtan uca koşusu; **PDF-first zaman sıralı fiyatın mevcut donmuş değer politikasına bağlanması (ana/alternatif/PAS)**.
- Sonraki tek iş: tam/tek seferlik gerçek 10 lig PDF kabulü ve kalibrasyon bağlantısı; baştan yeni pilot veya yeniden model yarıştırması yok.
