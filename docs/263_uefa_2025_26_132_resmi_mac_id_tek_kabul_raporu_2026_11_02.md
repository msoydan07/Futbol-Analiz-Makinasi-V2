# 2.6.3 — 2025/26 UEFA CL+EL 132 resmî maç numarası: tek toplu kabul raporu

**Tarih:** 2 Kasım 2026.  
**Durum:** 132 resmî UEFA maç bağlantısı kaynak incelemesi ve eski tarihsel adaylarla eşleştirme **BAŞARILI**. Matematiksel güç modeli henüz **ONAYLANMADI**.

## Yeni kanıt ve gerçekleşen kabul

- Yeni GitHub Actions koşusu **başarılı**:
  https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41488522760
- **11/11 yeni güvenlik testi PASS.**
- Tek kaynak/ID artefaktı:
  `263-uefa-2025-26-official-132-match-id-links`;
  `132_official_match_id_links_report.json` ve
  `132_UEFA_MATCH_IDS_REVIEW_ONLY.json`.
- Girdi: daha önce tamamlanan `41480542512` koşusunun
  **95 CL + 37 EL = 132** maçlık inceleme adayı.
- Önceki resmî 47 UEFA kulüp profil-ID bağlantısı,
  2025/26 10-lig canonical kimliği ve 132 tarihsel
  kayıt **değiştirilmedi**.

| Kaynak bağlantısı | Şampiyonlar Ligi | Avrupa Ligi | Toplam |
|---|---:|---:|---:|
| 2025/26 10 lig kapsamı önceki aday karşılaşma | 95 | 37 | 132 |
| UEFA resmî sonuç arşivi maç-ID URL'si bulundu | **95** | **37** | **132** |
| Tarih, ev/deplasman, iki takım, skor önceki adayla uyuştu | 95 | 37 | **132** |
| Sayısal UEFA match-ID birbirinden farklı | 95 | 37 | **132** |
| GitHub runner UEFA HTML sayfalarını bağımsız indirdi | Hayır | Hayır | **Hayır** |

**Resmî kaynaklar, 2025/26 sonuç arşivleri:**

- CL: https://www.uefa.com/uefachampionsleague/news/029c-1e9a2f63fe2d-ebf9ad643892-1000--champions-league-2025-26-all-the-results/
- EL: https://www.uefa.com/uefaeuropaleague/news/029c-1e9b4e18c28e-3bb76afa22ac-1000--europa-league-league-phase-results-by-team/

**Somut örnekler:**

- Galatasaray–Liverpool (30.09.2025, 1-0): UEFA **2045927**,
  https://www.uefa.com/uefachampionsleague/match/2045927--galatasaray-vs-liverpool/
- Fenerbahçe–Aston Villa (22.01.2026, 0-1): UEFA **2046268**,
  https://www.uefa.com/uefaeuropaleague/match/2046268--fenerbahce-vs-aston-villa/
- Braga–Feyenoord (24.09.2025, 1-0): UEFA **2046157**,
  https://www.uefa.com/uefaeuropaleague/match/2046157--braga-vs-feyenoord/

## İşlem kapsamı ve döngü kontrolü

Yalnız 132 aday maçın **resmî arşivdeki sonuç bağlantıları**
tıklandı ve tarih, skor, iki takım, ev/deplasman yönü,
resmî sayısal UEFA match-ID + URL ayrı kaynak dosyasında
korundu. Kapsam dışı takım veya dış ülkeler ligi için
yeni veri araştırması yapılmadı.

Bu yeni adımda şu önceki çalışmalar yeniden çalıştırılmadı:
- 432 UEFA maçının puan/hafta matematik deneyi
- 288/132 CL+EL 10 lig taraması (41480542512)
- 126/89/0 tarihsel maç öncesi yerel gol/xG kapsama testi (41485016193)
- 47 resmî kulüp profil bağlantısı kaynak testi (41486717971)
- UEFA runner ağ zaman aşımı ve T–60 kadro testleri

GitHub 132 URL ve maç-ID kaydını, daha önce kilitli inceleme
adaylarının 2025/26 kulüp kimliği, tarih ve skorlarıyla
**sıkı bire bir eşleştirdi**. Sahte alan adı, ID
çakışması, skor uyuşmazlığı, farklı takım yönü ve
tarih değişmesi için yalnız yeni odaklı kontroller yapıldı.

**Kaynak dürüstlüğü:** Resmî URL'ler ChatGPT web üzerinden
UEFA sonuç yazısındaki maç bağlantılarının açılmasıyla
elde edildi. **GitHub Actions bu UEFA sayfalarını bağımsız
HTTP üzerinden indirmedi.** Buradaki kabul, web kaynak
bağlantısı + tarih/skor/kimlik tutarlılığıdır; bütün
HTML içeriğinin runner'da bağımsız tekrar doğrulaması
veya kaynakların kriptografik imzası değildir.

## Sıradaki mühendislik kararı

**Maç numarası / takım kimliği açığı 2025/26'daki 132
aday için kaynaklı eşleştirme seviyesinde kapandı.**
Ancak bu, 132 maçta geçmiş yerel lig istatistiklerinin
gerçek başlama anından **önce yayımlandığı ve
sistemce erişilebilir olduğu** anlamına gelmiyor.
2026'da derlenmiş CSV yalnız kronolojik skor kesiti
kanıtlıyor; tarihsel sürümleme ve erişim anı için
kanıt hâlâ yok.

Önceki `41485016193` testinde iki tarafta 4+ geçmiş gol
sonucu olan aday **126**, 8+ geçmiş gol sonucu olan aday
**89**, her iki tarafta yeterli xG çifti olan aday **0**.
Bu değerler yeniden test edilmedi.

**Bir sonraki yeni paket:** tarihsel veri as-of
yayın zamanı ve arşivlenmiş kaynak sürümleri için
toplu kanıt/kapsam denetimi; varsa başlangıç öncesi
güvenilir kaynak durumunu ayır, yoksa gerçek
ön-maç tahmin testini geriye dönük onaylama.

**Değişmez mühendislik kuralları:**
- main, 10 lig, B/C2/C3/M4, pilot 100, A/B/C,
  T–60 ilk 11 ve kullanıcı bildirimi saati değişmedi.
- H2H özel özelliği ve keyfî motivasyon çarpanı yok.
- M0/M1/M2 kıyaslaması veya yeni güç katsayısı yok.
- Yeni model yalnız önceden planlanmış toplu kronolojik
  test ve kararlı dış veri başarısı sonrası
  **ayrıca mühendislik onayıyla** değerlendirilebilir.
