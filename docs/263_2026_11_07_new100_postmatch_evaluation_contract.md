# Futbol Analiz Makinası 2.6.3 — Yeni100 maç sonu değerlendirme sözleşmesi

## Çalışmanın amacı
Yeni 100 maçlık ileri pilotun resmî sonucu geldikten sonra MS, KG Var, 1.5 / 2.5 / 3.5 Üst isabeti, Brier, log-loss ve kalibrasyon sonuçlarını ayrı değerlendirebilmek. Önceden mühürlü B/C2/C3/M4 hesapları değiştirilmez. Eski 96 ve ayrı 3 mühendislik maçı yeni 100 sonuçlarına taşınmaz.

## Gerçek sonuç için kanıt kontratı
Maç skoru sadece experiments/263/sabah_postmatch_inputs/YYYY-MM-DD/AD.json dosyasından okunur. Dosya aşağıdaki alanların **tamamını** içerir:
- schema = 263_NEW100_HUMAN_OFFICIAL_RESULT_ATTESTATION_V1
- cohort = new100
- forecast_sha256 = 64 hex orijinal ileri tahmin SHA
- league, home_id, away_id, kickoff_utc = tahminde mühürlenmiş kimliğin birebir kopyası
- home_goals, away_goals = resmî tam zaman skoru (0–20, int)
- final_status = FULL_TIME_HUMAN_REVIEWED
- source_url = maç skoru gösteren, lige ait resmî HTTPS sayfası
- source_checked_at_utc = maç başlangıcından en az 90 dakika sonrası
- reviewed_at_utc = kaynak incelemesinden sonra, gelecekte olmayan zaman
- reviewer = kaynak inceleyenin adı/kimliği
- verification_scope = HUMAN_ATTESTED_OFFICIAL_PAGE_NOT_NETWORK_REVERIFIED

İnsan tarafından resmî sayfadan kontrol edilmiş bilgi ile ağ üzerinden bağımsız doğrulanmış bilgi aynı değildir. Uygulamanın şu an ikinci kontrolü yapan kaynağı bulunmadığından **independently_network_verified_result_count = 0** gösterilir. Kaynak URL'sinin resmî alan adına ait olması sayfadaki skoru internet üzerinden gerçekten kontrol ettiğini kanıtlamaz. Geçersiz kaynak, kimlik, SHA, çelişik skor, kickoff öncesi kaynak tarihi veya iki kez gelen kanıt skorlamayı durdurur; skor uydurulmaz.

## İstatistik değerlendirme
- MS 1-X-2: tüm üç olasılıklı Brier / log-loss ve en yüksek olasılıklı yönün isabet yüzdesi.
- KG Var: gerçekleşen olayın ikili Brier / log-loss, eşik 0.5 ile yön isabeti yüzdesi ve beş kalibrasyon kovası.
- 1.5 / 2.5 / 3.5 Üst: her çizgi kendi olay sonucuyla ayrı puanlanır, Brier / log-loss ve 0.5 yön yüzdesi raporlanır.
- DEV tarafından kalibre olasılıklar: yalnız orijinal kararda mevcut C3/M4 dayanaklı, pozitif DEV Brier skill ve en az üç model destekli pazarlar. Bunlar ayrı tanısal ikili olaylar olarak değerlendirilir; farklı modeller keyfî ağırlıkla birleştirilmez.
- M4 ile B/C2/C3 kıyası: yalnız iki modelin de mevcut olduğu aynı maçlar. Eksik B yüzdeleri doldurulmaz. 10 farklı maç gününden önce üstünlük / CI iddiası yok.
- Güvenilir, aynı maçla kimliklenmiş korner kaydı yoksa korner isabeti **HESAPLANMADI**. Olasılık ve sonuçlar geriye dönük eğitime yazılmaz.

## Kalıcı güvenlik sınırı
- Maks. 100 mühürlü forward_morning_263 dosyası. 96 ve acceptance3 kaynakları ile testler bağımsızdır.
- Kaynaksız maçların status=PENDING, n=0, Brier=null, accuracy=null. Boş veri için yüzde 0 veya %100 üretilmez.
- Tahmin dosyası veya karar dosyası değişmez. Model matematiği, sabit kalibrasyon ve API fiyatları etkilenmez.
- Sonuçlar yalnız araştırma amaçlıdır; doğrulanmamış result ile bahis getirisi ya da güven sertifikası verilmez.
- Bağımsız çalışan workflow: .github/workflows/263-sabah-new100-postmatch-readonly.yml. Araştırma raporu JSON ve telefona uygun Markdown olarak GitHub Actions artefaktında okunur, yeni kalıcı ileri tahmin veya eski pilot sonucu yazılmaz.

## Şimdiki sonuç
7 Kasım 2026 itibarıyla asıl yeni100 pilotunda **0 mühürlü tahmin** olduğundan, bu yeni postmatch hattı **0/100 ve sonuç 0** bildirmelidir. Gerçek maç/sonuç kanıtı girilmeden yüzdeler yayımlanmaz. Sıradaki gerçek kullanım ilk pilot maçının başlamadan önce mühürlenmesi ve bitişten sonra resmî skor kanıtının eşlenmesidir.
