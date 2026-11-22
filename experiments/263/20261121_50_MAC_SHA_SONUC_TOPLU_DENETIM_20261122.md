# 21 Kasım 2026: 50 maç önü SHA tahminine tek toplu maç sonu değerlendirme

**Durum:** BAĞIMSIZ ARAŞTIRMA DENETİMİ — ESAS MÜHÜRLER VE ANA KOD DEĞİŞMEDİ. Bahis/pilot yetkisi yok.

## 1. Tahmin kimliği ve önceden mühürlenme
- 50 / 50 güncel `experiments/263/sabah_research/new100/2026-11-21/*/decision.json` SHA tam; ilgili 50 `forward_morning_263` tahmini, 50 tarihsel baseline SHA'sı ve takım kimlikleri eşleşiyor.
- Yedi olayın tamamı normalize; ana tahmin yedi olayın en yüksek yüzdesi; alternatif farklı pazar grubundan.
- GitHub'daki bu dosyaları oluşturan 10 commit 21 Kasım saat 08:04–09:40 UTC arasında; en erken müsabaka 10:30 UTC. Tahminler geriye dönük yeniden üretilmedi.
- Her 50 kararda `status=RESEARCH_CANDIDATE_NOT_APPROVED`, `betting_authorized=false`; onaylı resmî bahis performansı gibi sunulmaz.
- 12 ikinci-iddaa-PDF yorumu/ilk-son oran arşivi 50 ilk kararın SHA'sıyla karşılaştırıldı; ikinci fiyatlar sabah tercihini değiştirmedi.
- SHA/ön maç envanter CI: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/45021192699

## 2. 90 dakika gerçek skor karşılaştırması

| Ölçüm | Sonuç |
| --- | ---: |
| ANA doğru | 27/50 (%54) |
| Alternatif doğru | 25/50 (%50) |
| ANA veya alternatif doğru | 34/50 (%68) |
| Her ikisi doğru | 18 |
| Yalnız ana | 9 |
| Yalnız alternatif | 7 |
| İkisi de yanlış | 16 |
| Ana tercih ortalama tahmin olasılığı | %62,09 |
| Modelin beklediği ana isabet | 31,047/50 |
| Ana gerçekleşme | 27/50 |
| Ana binary Brier | 0,24366 |
| Ana binary log-loss | 0,68079 |

Başarı bölümü tek günün **araştırma SHA'sı**, bağımsız gelecekteki tüm maçların doğrulanmış kalibrasyonu değildir. Üç pazar ailesi tam normalize 50 maçta ayrıca puanlandı: M4/MS 27/50 (%54); C3/KG Var/Yok 28/50 (%56); C3/2.5 Alt/Üst 23/50 (%46). Üst/Alt 2.5 bu örneklemde zayıf kalıyor.

### Lige göre ana seçim

| Lig | Doğru / sayı |
| --- | ---: |
| Premier League | 2/7 |
| Championship | 5/11 |
| Bundesliga | 3/6 |
| LaLiga | 3/4 |
| Serie A | 4/4 |
| Ligue 1 | 1/5 |
| Eredivisie | 4/5 |
| Türkiye Süper Lig | 1/4 |
| Belçika Pro League | 4/4 |

### Kalibrasyon grupları
- %50–59 model güven: 9/24 (%37,5) gerçekleşme; ortalama tahmin %56,65.
- %60–69: 14/20 (%70) gerçekleşme; ortalama tahmin %65,06.
- %70–79: 3/5 (%60); ortalama tahmin %72,49.
- %80+: 1/1 (%100); yalnız tek kayıt.
- Yüksek güvenle kaçanlar: Amed–Rizespor **MS1 %77,07; 0-2**, West Ham–Preston **MS1 %73,80; 1-1**. 50 kayıt katsayı güncellemesi için yeterli tek başına kanıt değildir.

## 3. Oran piyasa makinesi P0/P2'nin ayrı örneklem denetimi
- 12 ikinci PDF arşivi var; bunların yalnız **7** tanesinde ilk-piyasa 7 olayın fiyatları tamdır. **5** tanesine eksik/karşılaştırılamayan yedi-pazar lideri uydurulmadı.
- Aynı yedi maçta P0 bağımsız fiyat lideri **3/7**, ana model **4/7** doğru. P2 uyumlu etiketli 4 kayıtta ana doğru 2/4; farklı etiketli 3 kayıtta ana doğru 2/3. Küçük ve seçilmiş örneklem; P0/P2 üstünlüğü veya dezavantajı ispatlanmış değildir.
- İkinci PDF'de oran değişimine bakmak, maç öncesi ana tercihin değiştirilmesine neden olmadı.

## 4. Gerçek skor kaynakları
- Soccerbase 21.11.2026: https://www.soccerbase.com/matches/results.sd?date=2026-11-21
- LiveScore 21.11.2026: https://www.livescores.com/football/2026-11-21/?tz=8
- ONTOUR fikstür ve maç sonuçları: https://ontourfootball.com/fixtures/2026-11-21
- Belçika Pro League / Le Soir / RotaScore sonuçları bağımsız tarandı; ayrıntı kullanıcıya teslim edilen JSON/CSV'nin `score_sources` alanlarındadır.
- **Kaynak çelişkisi:** ONTOUR Nice–PSG 1-3 yazarken Soccerbase, Reuters ve Nice kulübünün maç sonu haberi 2-3 diyor. Sonuç olarak **2-3** kullanıldı; çelişki saklanmadı.
- 90 dakika + hakem uzatması, penaltı/uzatma devresi dahil edilmedi.

## 5. Operasyon kararı
**M4/C3 ve v4 SHA karar katmanını bu tek güne bakarak değiştirmiyoruz.** Güncel ve ileriki maç öncesi SHA kohortlarında özellikle KG Var ve 2.5 Üst yanlılığı, 50–59 güven bandının fazla iyimserliği, lig bazlı sapmalar ve P0/P2'nin ancak tam yedi fiyatlı karşılaştırmalarını bağımsız izliyoruz. Geçmiş tahmin, fiyat, skor veya kaynak SHA'sı değiştirilmez.

Denetim JSON tam içeriği SHA-256 (payload): `187101c8abb30fa52a6c9c886ca65e8218ea220a4f15de3625c59437dbc01c1a`. Kullanıcıya teslim edilen tam ayrıntılı PDF 7 sayfa, CSV 50 satır ve JSON maç bazlı tüm karar, skor, olasılık ve kaynakları içeriyor.

**İş kapatma:** Dünkü SHA kararları puanlandı ve tek toplu araştırma raporu hazırlandı; yeni pilot, model terfisi veya bahis önerisi oluşturulmadı.
