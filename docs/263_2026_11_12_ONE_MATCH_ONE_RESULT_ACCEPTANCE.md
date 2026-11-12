# 2.6.3 — Tek maç, tek sonuç kaydı: nihai basit sonuç kabul sözleşmesi

**Tarih: 12 Kasım 2026.** Bu, 2.6.3 araştırma deney dalının gelecekteki maç-sonu kaydı içindir. Eski SHA mühürleri, M4/B/C2/C3, 4617 geçmiş maç ve LITE değişmez.

## Bir maç, iki aşama

1. **Maç önü (yalnız bir kere):** resmî fikstürden doğru lig, iki kanonik takım ve saat doğrulanır. B/C2/C3/M4 hesaplanır, SHA mühürlenir.
2. **Maç sonu (tek sonuç kararı):** skor yayınlandıktan sonra doğru maçın tam zaman / 90 dakika sonucu alınır. Kaynak seçimi:
   - **A:** doğrudan lig/federasyon veya kaydı önceden onaylanmış kulübün maç sonucu; tek gerçek, okunmuş final skor kaynağı yeterlidir.
   - **B:** A okunamazsa farklı yayıncılar VE farklı bilinen üst veri kaynaklarından en az iki eşleşen final skor; bu sonuç *iki bağımsız yayıncıyla teyitli*, **federasyon-resmî** olarak etiketlenmez.
   - **C:** tek ikincil kaynak, arşivde sonuca ilişkin çelişki, devre arası, canlı skor, ertelenme, terk, henüz bitmemiş maç veya kimlik uyuşmazlığı: tamamlandı skorunu kabul etme. Yalnız bu maç için HOLD/POSTPONED durumu; diğer maçları engellemez.

**Önemli:** bir URL'yi listeye koymak **skoru sayfadan okumak değildir**. Tek sonuç kabulü için lig/klüp sağlayıcısına gerçekten bağlanan ve tam skor + ev/deplasman + maç kimliğini çıkaran güvenilir veri okuyucusunun ürettiği gözlem gerekir. Bir kullanıcı/dosya alanına LIVE_PARSED_SCORE_ADAPTER yazılması tek başına gerçek HTTP sonucu ispatlamaz. Kabul kodu dış kaynağı kendisi fetch etmez; bunu sağlayıcı okuma katmanı yapmak zorundadır. Henüz tüm 10 ligde sağlanmamış okuma uyumluluğu kanıtlanmış gibi gösterilmez.

## Kalıcı arşiv / no-repeat

Her maç için **SHA anahtarlı tek dosya**:
data/results_only_263/accepted_forward_263/YYYY-MM-DD/SHA.json

Dosya: tahmin SHA, tarih, kanonik ev/deplasman ID, kickoff, skor veya erteleme, kaynak kanıt sınıfı, tekil kaynak maç kimliği, HTTPS URL, sayfa içerik SHA, saat ve bütün sonuç belgesi SHA içerir.

- Kaynak sonucu uygun ise **bir kez** diske yazılır. Aynı SHA tekrar gelirse dosya geri okunur: kaynak sitesini **yeniden çekme, yeniden karar oluşturma, ikinci kayıt oluşturma**.
- Eski dosyanın SHA'sı veya kimliği bozulmuşsa hata ver; düzeltiyormuş gibi sonuç üzerine yazma.
- Yeni güvenilir skor çelişkisi sonradan bildirilirse ilk kayıt korunur, ayrı hata incelemesi açılır. Sessiz geçmiş skor düzeltmesi yok.
- Erteleme sonucu yok olarak ayrı arşivlenir, MS/KG/Alt-Üst puanlamasına girmez. Yeni tarihte yeni fikstür ve yeni mühür varsa ayrıca değerlendirilir.
- **Puanlama:** eski maç önü olasılıkları ile kabul edilen tam skorun MS, KG, 1.5/2.5/3.5 sonucu karşılaştırılır; yeni model eğitimi yok.
- **Rapor:** yalnız yeni kabul edilen veya çelişkili maçları bildir. İstatistikte resmî kaynaktan kabul ile iki-yayıncı kabul ayrıdır; resmî federasyon insan attestation'ı uydurulmaz.

## Eski 8 Kasım verisi geri dönmez

Önceden saklanmış 8 Kasım 40 tahmin = 39 sonuç + 1 erteleme ayrı ve dokunulmaz.
Kanıt sınıfları: 3 TFF sayfasının canlı okunmuş skoru; 22 lig, 13 kulüp web araştırması; 1 dış federasyon araştırma. Bunlar yeni kabul kapısından geçirilip sahte güçlü kanıt sınıfına yükseltilmez. Günlük sonuç kontrolü eski maçları sürekli yeniden taramaz.

## Kod ve kabul sınırı

- Kabul kapısı: experiments/263/postmatch_once_accept_263.py
- Dış kaynak kaydı: schema 263_LIVE_RESULT_OBSERVATION_V1
- Eski skor modülünün yeni arşivden okuması: experiments/263/postmatch_csv_bridge_263.py
- Tek kabul testleri: experiments/263/test_postmatch_once_accept_263.py
- Gerçek eski SHA üzerinde uçtan uca yeni arşiv sıfır CSV okuma denemesi: experiments/263/test_postmatch_once_bridge_263.py

**Yayına alma gereksinimi:** güvenilir kaynak okuyucusu gerçekten HTTP gövdesinden skor/maç kimliğini çözmeden herhangi bir gözlem dosyasını kendiliğinden LIVE_PARSED_SCORE_ADAPTER diye kabul ettirme. Bu kod karar ve idempotent arşiv katmanını sağlar; tüm 10 ligin canlı veri okumasını veya yeni maçların günlük kendiliğinden arşivlenmesini tek başına iddia etmez.
