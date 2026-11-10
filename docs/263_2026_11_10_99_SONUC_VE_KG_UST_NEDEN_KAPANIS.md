# 2.6.3 futbol — veri doğrulama + KG/Üst neden analizi, kapanış (10 Kasım 2026)

**Karar:** 99 adayın 10 ligde kaynak/kimlik köprüsü doğrulandı; resmî lig sonucu sayfalarından manuel okunan **28/99 maç** kaynak skoru/tarih/ev-deplasman/kanonik takım kimliğiyle birebir uyuştu. Bunlar henüz **federasyonun her maç için tekil maç ID'siyle bağımsız API attestation** değildir. **71 maç** yalnız kaynak adayı. 984 eski tarihsel maçta KG ve toplam gol sapması incelendi; ana M4 **değişmedi**.

## 1. Tek seferlik veri köprüsü — tam kanıt

- Esas kaynak: 4.518 araştırma amaçlı kabul edilmiş maç, SHA256 `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`.
- İlk hafif kaynak gözlemi 10 lig için 2026/27 CSV'nin SHA'sını ve 99 yeni skor adayının sayılarını mühürledi.
- **İkinci ve son haftalık hafif kaynak kontrolü:** Sağlayıcı SHA'sı her 10 ligde ilk kontrolle aynı; eski tarih+sonuç+CSV-satır kaynak eşleşmeleri değişmedi; yeni takımlar ad→kanonik ID geçici eşleşmesini sağladı. Bu hafta aynı kaynağa daha fazla otomatik indirme YOK. [Kaynak kullanım kuralları](https://football-data.co.uk/contact.php).
- Türkiye Futbol Federasyonu 11. hafta 9 maç, Bundesliga resmî 9. hafta 9 maç, Lega Serie A 11. hafta 10 maç skorları **resmî lig sayfalarında gözlendi**, `research/opponent_goals/official_rounds_nov06_08_2026.json` içine kulüp ID ve kaynak URL'siyle **araştırma kanıtı** yazıldı. Bunlar otomatik olarak resmî maç ID'si veya network attestation sayılmaz.
- CSV'den tekrar tek seferlik okunan bu 28 maçın **ev/deplasman kimliği, tarih ve gol sonucu, resmî sayfadan insan/araştırma tarafından aktarılan skorlarla 28/28 eşleşti**; skor çelişkisi **0**. Yalnız kaynak adayı kalan 71 maçın sonuçları **bağımsız resmî skor olarak aktarılmadı**.

| Lig kodu | Yeni aday | Resmî sayfa+CSV eşleşen | Resmî sonuç tekil teyidi eksik |
|---|---:|---:|---:|
| BEL1 | 10 | 0 | 10 |
| ENG1 | 10 | 0 | 10 |
| ENG2 | 15 | 0 | 15 |
| ESP1 | 10 | 0 | 10 |
| FRA1 | 9 | 0 | 9 |
| GER1 | 9 | 9 | 0 |
| ITA1 | 10 | 10 | 0 |
| NED1 | 9 | 0 | 9 |
| POR1 | 8 | 0 | 8 |
| TUR1 | 9 | 9 | 0 |
| **TOPLAM** | **99** | **28** | **71** |

Önemli: Lig sayfasından okunmuş sonuçlar ayrı bir kanıt sınıfıdır, federasyonun gerçek maç ID'siyle tüm sonuçları dijital şekilde mühürleyip `sabah_postmatch_inputs` veya 4.518 maçlık veri kümesine kabul etmekten farklıdır. Orijinal veriler/mühürler değiştirilmedi.

## 2. KG ve 2.5 Üst: sapma hangi ligde?

Kilitli M4, 2026/27 **984** ortak geçmiş maçta haftanın önceki Pazartesi bilgi kesimiyle tekrar değerlendirilmişti. Bu dönem daha önce incelendiği için **hipotez keşfi**; yeni kör pilot değil.

- 2,5 Üst M4 tahmin ortalaması **53.3%**, gerçek **60.6%**, fark **+7.3 yp**.
- KG Var tahmin **53.0%**, gerçek **56.1%**, fark **+3.1 yp**.
- 2025/26→2026/27 lig bazlı gözlenen 2,5 Üst frekansının yükseldiği **9 lig**, düştüğü **1 lig (Premier League)**. Bu artışın sezon sonuna kadar kalıcı olduğu veya modelin kolayca düzeltileceği **kanıtlanmadı**.
- En büyük M4 2,5 Üst olasılık alt-tahmin farkları **BEL1, ITA1, ENG2**. Premier League'de ise yön tersine: 2026/27 maçlar önceki sezon kadar gollü değil.

| Lig | Değerlendirilen M4 n | 2025/26 gözlenen Üst2,5 | 2026/27 gözlenen Üst2,5 | M4 tahmini Üst2,5 | M4 tahmin eksiği (gerçek–tahmin) |
|---|---:|---:|---:|---:|---:|
| Belçika Pro League | 89 | 49.2% | 65.2% | 50.6% | +14.6 yp |
| Serie A | 100 | 45.8% | 61.0% | 48.0% | +13.0 yp |
| Championship | 165 | 50.7% | 61.2% | 50.9% | +10.3 yp |
| Bundesliga | 72 | 63.7% | 69.4% | 60.7% | +8.7 yp |
| Süper Lig | 90 | 52.9% | 60.0% | 52.0% | +8.0 yp |
| Eredivisie | 98 | 61.8% | 71.7% | 65.7% | +5.8 yp |
| Ligue 1 | 81 | 52.6% | 59.3% | 54.1% | +5.2 yp |
| La Liga | 109 | 50.0% | 57.8% | 52.7% | +5.1 yp |
| Primeira Liga | 90 | 53.9% | 54.4% | 50.2% | +4.2 yp |
| Premier League | 90 | 55.0% | 46.7% | 51.1% | -4.4 yp |

**Yorum:** Üst 2,5'te global +7 puan eklemek, Premier League gibi **zaten ters yönde sapma gösteren ligleri daha kötü yapabilir.** Birleşik modelde her ligin gol ortamı, maç kesimi ve takım güç eşleşmesi ayrı değerlendirilmelidir. Bu gözlem tek başına katsayı güncellemesi gerekçesi olamaz.

## 3. Rakip gücü / Beşiktaş örneği: mevcut verinin gösterebildiği

Elo proxy'si lig içinde geçmiş maçlardan ve aynı hafta maç sonuçlarına sızmadan hesaplandı. **Taktik formasyon veya pres verisi değildir.** Geçmiş 984 maçta M4 hatalarının segmentleri:

| Ev sahibi–deplasman ön-güç bandı (Elo) | n | Üst 2,5 tahmin | Üst 2,5 gerçek | KG Var tahmin | KG Var gerçek |
|---|---:|---:|---:|---:|---:|
| away_150_plus | 37 | 60.0% | 73.0% | 51.5% | 48.6% |
| away_50_to_150 | 200 | 53.2% | 58.5% | 54.3% | 55.5% |
| close_under_50 | 522 | 51.1% | 57.9% | 53.5% | 57.5% |
| home_150_plus | 32 | 66.1% | 62.5% | 47.5% | 50.0% |
| home_50_to_150 | 193 | 55.9% | 67.4% | 51.5% | 55.4% |

- Ev sahibi yalnız az/orta güçlü olduğunda (50–150 Elo önde), n=193, Üst2,5 **55.9% beklenirken 67.4% gerçekleşmiş**. Bu bantta gol çizgisi sapması özellikle incelenmeye değer; taktik nedensellik göstergesi değildir.
- Çok güçlü ev sahibi (150+ Elo) n=32: Üst2,5 M4 **66.1%**, gerçekleşen **62.5%**; her kuvvet bandında sistematik olarak aynı yönde sapma yok.
- Her iki takımın en az 8 geçmiş maçının bulunduğu **750** maçta 2,5 Üst ortalama M4 **52.9%**, gerçekleşen **60.9%**. Az veri nedeniyle bilinemeyen takımların problemi tek açıklama gibi görünmüyor.
- Genel 4.518 maçlık kaynakta 150+ Elo daha güçlü ev sahibiyle oynanan 85 maçta ortalama skor **2.75–0.75**; **Üst2,5 64.7%, KG Var 48.2%**. Favorinin çok gol atması KG Var'ın yüksek olması anlamına gelmez.

Bu yüzden kullanıcı Beşiktaş örneği için **hangi rakibe ne kadar pozisyon, şut kalitesi, pres, geçiş ve savunma bloğu** üretilmiş diye sormakta haklıdır. **Ancak elimizdeki sonuç+şut arşivi pres ve oyun şekli etiketleri içermez.** Aynı Elo gücüne karşı farklı taktikler oynanabilir; bunun adı olmayan veriyi matematiğe eklemek hata üretir.

## 4. Rakip modellerin kararı

- Sabit `DC rho=-0,08` ve ortak şoklu bivariate Poisson, aynı 984 geçmiş maçta KG ve belli gol çizgilerinde çok küçük Brier kazanımları; diğer gol pazarları ve MS tarafında kayıplar üretti. **Tek yöntem tüm marketlerde üstün değil.**
- M4 MS yönü ile KG/Üst Alt değerlendirmesi ayrı raporlanmalı; `PAS` korunmalı; bağımsız skor kaynağı olmadan testin yeşil olması başarı doğrulaması değildir.
- **M4 veya karar yüzdelerine global düzeltme YOK**. Bu dönemdeki gol artışı araştırma hipotezidir, yeni resmî veri ve bağımsız maç önü mühürlü sonuçlar geldikçe izlenebilir.

## 5. Sonraki tek teknik engeller

1. 71 adayın lig/federasyon maç ID'si ve resmî skor eşleştirmesi (99 içindeki 28'de de tekil maç ID attestation eksik). **Kaynak indirme kotası bu hafta doldu**; federasyon sayfaları üzerinden doğrudan ve az sayıda, gerektiğinde manuel doğrulama yapılabilir. Kaynak veriyi yeniden izinsiz indirmeyin.
2. Doğrulananlar için **ayrı append-only, haklarla uyumlu, zaman damgalı resmî kabul dosyası** hazırlayıp kendi `fixture_id/home_id/away_id/date` kanıtı üzerinden doğrulamak. Mevcut 4.518 satırı sessizce değiştirmeyin.
3. Asıl değişken araştırması: lig dönemi/gol temposu, rakip güç grubu, geçmiş gol şansı ve gerçek oyuncu-olay verisi lisanslı-kapsamlıysa KG/Üst'e sayısal katkısının bağımsız ölçümü. Eski sonuçları tekrar tekrar “yeni pilot” diye işlemeyin.

## 6. Kanıtlar ve değişmezler

- [Kaynak ve gol analizinin ana raporu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-opponent-goals-20261110/docs/263_2026_11_10_OPP_GOALS_ENGINEERING_DECISION.md)
- [28 resmî sayfa insan/araştırma kayıtlı skor](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-official-score-reconcile-20261110/research/opponent_goals/official_rounds_nov06_08_2026.json)
- [Aynı-haftalık son kaynak 28/28 karşılaştırma sonucu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-official-score-reconcile-20261110/research/opponent_goals/reports/official_round_score_concordance_20261110.json)
- [99 aday resmî olmayan ilk kaynak preflight](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-data-source-preflight-20261110/research/opponent_goals/reports/current_source_preflight_20261110.json)
- [984 rakip-ortak skor karşılaştırması](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-opponent-goals-20261110/research/opponent_goals/reports/goals_weekly_2026_27_exploratory.json)
- [Kaynak/skim test CI](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42781593466)
- Resmî lig sayfaları: [TFF hafta 11](https://www.tff.org/Default.aspx?hafta=11&kulupID=3610&pageId=198), [Bundesliga hafta 9](https://www.bundesliga.com/en/bundesliga/matchday/schedule), [Lega Serie A son sonuçlar](https://www.legaseriea.it/serie-a).
- `main`, `experiment/263-toplu-karsilastirma`, `m4_integrated.py`, mevcut 4.518 history, 40 SHA mühür ve eski kararlar, LITE, bahis oran/sabah kotası, basketbol **dokunulmadı**.

**KAPANIŞ:** 99/99 kaynak kaynak-satır kimliği güvenliği; 28/99 resmî sayfa skor uyuşması; 71 araştırma adayı. Gol sapmasının önemli bir bölümü 2026/27 lig bazında gol ortamının 2025/26'dan farklı görünmesiyle birlikte görülüyor; **bu korelasyon neden-sonuç kanıtı değildir**. Üretimde yeni model terfisi yok.
