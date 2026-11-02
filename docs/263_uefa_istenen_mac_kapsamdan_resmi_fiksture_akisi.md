# 263 — UEFA istenen maç: 10 lig kapısı → gerçek UEFA fikstürü → DUR

**2 Kasım 2026, ayrı deney dalı.**

İlk canlı giriş:
`experiments/263/europe/uefa_requested_match_entry_263.py`.

Her çağrı, kullanıcı tarafından istenen **tek maç** için sırayla:
1. Yalnız mevcut canonical index'i kullanarak iki takımın **2026/27
   10 ligden birine** kayıtlı olup olmadığını kontrol eder. Kapsam
   dışı veya ismi çözülemeyen takımda **durur, ağ çağrısı yapmaz**.
2. Yalnız uygun iki takımda, seçilen UEFA turnuvasına ait **tek** resmî
   2026/27 UEFA *lig aşaması* haber/fikstür sayfasını canlı okur.
   Resmî URL yanlış alan adına yönlenirse reddeder. Sayfayı okumak
   başarıyla bitse bile görünür yazıda 2026/27, turnuva, ilgili
   takımların sıralı ev-deplasman eşleşmesi, gerçek tarih ve saat
   bulunmazsa maç doğrulanmış sayılmaz.
3. UEFA sayfası 21:00 CET varsayılan saatini açıkça yazıyorsa
   yalnız o eşleşme için uygular; erken saat yazılıysa onu kullanır.
   **Yalnız istek anından itibaren 7 gün** içindeki maç kabul
   edilir. Saat CET olarak *kaynakta yazıldığı gibi* tutulur;
   Türkiye saatiyle karıştırılmaz.
4. Doğrulanmış fikstür bile matematik tahmini, gol katsayısı, oran,
   A/B/C veya pilot kaydı **üretmez**; güvenli `NO_MODEL_YET`
   durumunda durur. Takımın UEFA kulüp kimliği ayrıca
   resmî ID ile eşlenmeden modelde kullanılmaz.

CL sabit resmî kaynak:
https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/

EL sabit resmî kaynak:
https://www.uefa.com/uefaeuropaleague/news/02a8-2174cafa5bb6-82bbc20c9b92-1000--2026-27-europa-league-all-the-league-phase-fixtures-and-results/

Güvenlik: Kullanıcı JSON'undaki 'verified' bayrağına güvenilmez.
İnternet kaynağı dinamik veya erişilemezse **kapalı başarısızlık**.
Kapsam geçişi, maç tahmininin hazır olduğu anlamına gelmez.

Komut:
`python experiments/263/europe/uefa_requested_match_entry_263.py --competition UEFA_CL --home Barcelona --away "Aston Villa"`

Kapsam dışı:
`python experiments/263/europe/uefa_requested_match_entry_263.py --competition UEFA_EL --home Celtic --away "Beşiktaş"`

Önceki DOMESTIC `requested_match_runner_263.py` işlevini
UEFA'ya zorla bağlamıyoruz; bu ayrı giriş sadece UEFA içindir.
Ana 10 lig, Tuesday yenileme, B/C2/C3/M4 ve pilot değişmez.
Yalnız 2026/27 **lig aşaması** desteklenir. UEFA eleme/final
fikstürü, dış sezon otomatik güncelleme ve gerçek Avrupa
tahminleri henüz kabul edilmedi.


## Kabul gözlemi ve GitHub erişim engeli

2 Kasım 2026 hedefli CI:
https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41468839187

**15/15 yeni sentetik kabul testi geçti.** Kapsam dışı ve tanınmayan
takım için resmî UEFA URL'si dahi açılmıyor (gerçek fonksiyon
sınırında test edildi). Turnuva değiştirilirse yanlış resmî
URL reddediliyor, 7 gün dışında maç kabul edilmiyor,
skorlu sonuçtan gelecek fikstür uydurulmuyor. Bu testler
gerçek maç tahmin matematiğini doğrulamıyor.

**Gerçek kaynak erişimi:** Aynı CI'da GitHub runner'ın CL ve EL
resmî haber sayfalarını açma denemeleri ayrı ayrı
`TimeoutError` verdi. Kod **`OFFICIAL_UEFA_FIXTURE_NOT_VERIFIED`**
döndürdü, maç veya tahmin uydurmadı. GitHub workflow'unun
yeşil olması gerçek UEFA canlı ulaşımı başarılı demek DEĞİL.
Bu nedenle canlı UEFA erişimi **AÇIK BLOKER**; ayrı bir
araştırma/güvenilir veri erişim yöntemi olmadan otomatik
"UEFA fikstürü doğrulandı" denemez.

**Tekrarı önleme:** Aynı başarısız iki ağ isteğini
her yeni push'ta tekrar çalıştırmayacağız. Ağ diagnostik
basamağı `workflow_dispatch` moduna taşındı; sadece
bilinçli elle çalıştırılabilir. Manuel denemede resmî
kaynak gerçekten doğrulanmazsa iş **başarısız** biter.
Normal push'ta güvenlik birim testleri yeterlidir.

**Mühendislik kararı:** Kapsam kontrolü + kaynak-adapter giriş
bağlantısı **tamam**; **canlı UEFA otomatik doğrulama ve
Avrupa tahmin motoru henüz tamam değil.** Ana dal,
yerel 10 lig, Salı otomasyonu ve dört model değişmedi.
