# Futbol Maç Analiz Makinası 2.6.3 — UEFA 3–5 Kasım / AŞAMA 8 T−60 HAZIRLIK VE KAYIT PROTOKOLÜ

**3 Kasım 2026 — 10:40 civarı (TSİ).** Bu belge tahmin kaydı değildir. Altı ayrı oturumun çalışma kuralları, tutulan zaman damgaları ve **yalnız gerçek maç öncesinde** izin verilecek kayıt akışıdır.

## 0. Mevcut kanıt ve iş planı

17 UEFA CL/EL maçı, 34 takım, 9 üst yerel lig, Aşama 3–7 kabul kanıtları sabit ve dışarıdan erişilebilir. Kalıcı tahmin veya 100 maç pilot kaydı: **0**. Onaylanmış kalibrasyon kanıtı: **yok**.

- Yeni altı oturum: \`experiments/263/evidence/uefa_nov3_5_t60_six_slots_263.json\`
- Kayıt kodu: \`experiments/263/europe/uefa_t60_shadow_lock_263.py\`
- Tetikleyici: \`.github/workflows/263-uefa-t60-shadow-lock-on-request.yml\`. Yalnız **yeni bir dosya eklenince** çalışır; kendi kendine fikstür bulmaz veya deney dalının her commit'inde kayıt başlatmaz.
- Sadece hazırlık testleri: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41597333515 (11/11 başarılı).
- Baştan sona kayıt yapmayan gerçek veri provası: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41597623905 (2/2 başarılı; **6 oturum, 17 maçın tamamı bellek içinde; 0 dosya kaydı**).
- Yalnız \`experiment/263-toplu-karsilastirma\`; \`main\` ve yerel B/C2/C3/M4 üretim kodları değişmedi.
- **Web destekli resmî ilk 11 kontrolü ve GitHub otomatik kaynağı indirme farklı şeylerdir.** Talepteki URL ve gözlem zaman damgası, GitHub Actions'ın UEFA sayfasını gerçekten kontrol ettiğini kanıtlamaz.

## 1. Altı gerçek T−60 oturumu (Türkiye saati)

| Tarih | Başlama | Hedef T−60 | 17 resmî adaydan kayıt edilecek maç |
|---|---:|---:|---|
| 3 Kasım | 20:45 | **19:45** | Galatasaray – Stuttgart |
| 3 Kasım | 23:00 | **22:00** | Atlético – Bayern; Barcelona – Aston Villa; Feyenoord – Inter; Man United – Roma; Villarreal – PSG |
| 4 Kasım | 20:45 | **19:45** | Fenerbahçe – Liverpool |
| 4 Kasım | 23:00 | **22:00** | Dortmund – Betis; Porto – Napoli; PSV – Club Brugge; Leipzig – Manchester City; Lens – Como |
| 5 Kasım | 20:45 | **19:45** | Crystal Palace – Hoffenheim; Real Sociedad – Lyon |
| 5 Kasım | 23:00 | **22:00** | AZ – Juventus; Leverkusen – Marseille; Celta – Union SG |

**Tek eylem hedefi:** Söz konusu gün/oturum için *bir defa* web kaynak kontrolü + bir adet yeni GitHub istek JSON dosyasının oluşturulması. Her oturumdaki bütün maçlar beraber değerlendirilir.

UEFA 2026/27 madde 55.04'e göre maç formu maçtan **en geç 75 dakika önce** teslim edilir; kamuya açık formun duyurulması birebir aynı anda garanti değildir:
- https://documents.uefa.com/r/Regulations-of-the-UEFA-Champions-League-2026/27/Article-55-Match-sheet-Online
- https://documents.uefa.com/r/Regulations-of-the-UEFA-Europa-League-2026/27/Article-55-Match-sheet-Online

## 2. Her oturumun tek sıralı işlemi

1. Saat hedef T−60 yaklaştığında **yalnız ilgili oturumdaki** resmî UEFA maç sayfalarını web'de kontrol et: doğru maç, ev/deplasman yönü, tarih ve başlanma saati. Kaynak URL'sini kendi \`uefa_nov3_5_t60_six_slots_263.json\` ve \`uefa_2026_11_03_05_fixture_scope_review.json\` dosyalarındaki tekil maç URL'leriyle karşılaştır. Değişiklik varsa otomatik kayıt YAPMA.
2. UEFA veya resmî kulüp maç merkezi / güvenilir FotMob, Sofascore, LiveScore gibi tekil maç sayfasından **CONFIRMED** olarak gösterilen iki tarafın 11'er oyuncusunu gözlemle. URL ve UTC görülme zamanını yaz. Yalnız tahmini kadro varsa, iki ayrı kesin 11 bulunmuyorsa veya URL site tarafından doğrulanamıyorsa **\`NOT_CONFIRMED\` yaz**. Analiz devam eder; oyuncu uydurulmaz.
3. Mevcut \`experiments/263/europe/t60_requests/\` klasörüne **tek YENİ** istek dosyası ekle. Dosya adı slot anahtarıyla aynı olmalı, örnek \`2026-11-03_2045_TR.json\`. **Bu dosyanın eklenmesi gerçek kayıt eylemini tetikler.** Hazırlık sırasında veya T−75 aralığından önce asla oluşturma.
4. GitHub Actions 9 yerel ligden **güncel sezon sonuç CSV'sini bir kez**; beyondELO'dan **güncel puan dosyasını bir kez** çeker. Eski dondurulmuş 812 sonuç karşılaştırmada değişmişse otomatik durur. Kaynak/kimlik/zaman kontrolleri ve T−75 ile T−15 dakika aralığı dışında tahmin kilidi yok.
5. İki kol tam aynı veri ve aynı tarihsel sabit protokolle hesaplanır: **M0 gol temelli xG'siz referans** ve **M0 + yalnız keşif amaçlı Elo farkı**. İki model için beklenen goller, 1X2, 2,5 Alt/Üst, KG Var/Yok ve en olası skor hazırlanır. İlk 11 ve kaynaklı haberler, kanıtlanmamış bir gol λ çarpanı şeklinde otomatik katılmaz.
6. GitHub Actions bir **tek Git commit** içinde her maçın \`payload_sha256\` damgalı JSON kaydını \`experiments/263/europe/t60_locked/<slot>/<uefa_match_id>.json\` dizinine; ayrıca slot toplu özetini \`experiments/263/europe/t60_lock_reports/<slot>.json\` konumuna ekler. Önceden varsa *asla değiştirmez*.
7. **Gerçek kayıt kanıtı yalnızca başarılı GitHub commit SHA + CI SUCCESS + kickoff öncesi UTC kayıt zamanıyla vardır.** Başarısız veya gecikmiş koşu prematch kayıt değildir. Kullanıcıya böyle bildirilmelidir.

## 3. GitHub'da oluşturulacak tek istek biçimi

Aşağıdaki örnekteki \`reviewed_at_utc\` ve \`official_urls\` değerleri **gerçek T−60 web doğrulamasından sonra** doldurulur. Bu bir *örnek*, hazır kullanıcı talebi veya kanıt değildir:

\`\`\`json
{
  "schema": "263_UEFA_T60_SHADOW_LOCK_REQUEST_V1",
  "slot_key": "2026-11-03_2045_TR",
  "fixture_review": {
    "status": "ASSISTANT_WEB_OFFICIAL_PAGE_REVIEWED",
    "reviewed_at_utc": "GERCEK_UTC_WEB_KONTROL_ANI",
    "official_urls": {
      "2049614": "https://www.uefa.com/uefachampionsleague/match/2049614--galatasaray-vs-stuttgart/"
    }
  },
  "lineups": {
    "2049614": {
      "status": "NOT_CONFIRMED",
      "observed_at_utc": null,
      "source_url": null,
      "home_starting_xi": null,
      "away_starting_xi": null
    }
  }
}
\`\`\`

İki kesin 11 gerçekten tekil kaynaktan incelendiğinde yukarıdaki \`NOT_CONFIRMED\` kaydı yerine \`TWO_CONFIRMED_XI_SOURCE_CLAIM\` yazılır. \`observed_at_utc\`, \`source_url\`, \`home_starting_xi\`, \`away_starting_xi\` doldurulur; her listede tam 11 benzersiz oyuncu bulunur. Bu liste kaynaklı kontekst olarak saklanır; henüz sayısal model etkisi yoktur. JSON oluşturulmadan önce görülen ilk 11 asla sezgiyle tahmin edilmez.

## 4. Açık hata ve etik güvenlik

- **Maç başladıysa veya GitHub kuyruğu koşuyu çok geciktirdiyse:** kayıt yok, sonradan tahmin yazıp eski zamana taşımak yasak.
- **Kadro yayımlanmadıysa:** \`FIRST_XI_NOT_CONFIRMED_NON_BLOCKING\`, koşu devam edebilir.
- **Kaynak erişilemiyorsa, orijinal skor kaynaklarından biri değişmişse, bir kulübün adı/kimliği karışırsa, UEFA maç zamanı değişmişse veya Elo güncel değeri yoksa:** tahmin kilidi YOK; yalnız hata raporu.
- **Kapsam yalnız seçilmiş 17 UEFA maçı, 34 takım ve altı T−60 penceresi;** otomatik yeni maç seçimi yok.
- **Bu çalışma deneysel iki-model ileri dönem gölge karşılaştırmasıdır.** Kalibrasyon/üretim veya bahis onayı değil, yerel 100 maç pilotunu artırmaz. Oran/EV hesaplamaz.
- **Betalar değişmez:** \`β=0,525476...\` yalnız önceki 76 keşif eğitiminin sabit deneysel katsayısı; sonuçlara göre yeniden ayarlanmaz.
- 2026/27 UEFA ilk 11/cevap kaynakları, resmi lineup gözlem kaynakları ile yerel lig ve beyondELO gerçek skor kaynaklarının zaman damgaları birbirine karıştırılmaz.

## 5. Operatör iş yükü

Hazırlıktan sonra maç saatine kadar başka teknik test veya dosya yükleme gerekmiyor. T−60'da görev ChatGPT tarafından başlatılırsa önce resmî tekil sayfaları kontrol edip **yalnız o slotun yeni istek dosyasını** GitHub'a eklemesi yeterli. Bu, kilitlenen 1 veya 2 veya 3 veya 5 maçlık grubu arka arkaya kaydeder. GitHub Actions'ın dış ağ bağlantısı, servis yoğunluğu veya güvenlik kapısı bloke olursa çalışmış gibi gösterilmez; kullanıcıya tek özet raporla bildirilir.

**Ana durum:** 3 Kasım öğlen saatine kadar \`t60_requests\` ve \`t60_locked\` dosyası **HİÇ YOK**. Aşama 8'in *hazırlığı* ve provası tamamlandı, gerçek kayıt **henüz başlamadı**.
