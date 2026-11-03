# M4 Aşama 5 — 873 maç / doğrulanmış xG geçmişi: tek kesişim kabul raporu

**Tarih:** 2026-11-03  
**Durum:** `COHORT_COVERAGE_MEASURED_RESEARCH_ONLY` — M4+xG testi çalıştırılmadı; C3/M4 olasılıkları, sonuç başarıları ve pilot değiştirilmedi.

## Kaynak zinciri
- Dondurulmuş 4.413 maç SHA256: `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`; Actions kaynak paketi run `41251343847`, artifact `13061725424`.
- **Ham ve doğrulanmış xG arşivi bulundu:** 2026-11-01 `Understat xG kaynak ve eslesme piloti` run `41287280687`, artifact `13074948510`, paket SHA256 `14944c0c3c2153ce995a79d400afec3fbb7ef0607854d235d04e97fa1b572ce3`. Bu artifact `historical_verified_xg.csv` içeriyor; daha önce bakılan `verified-xg-audit` artifact `13077519072` ise yalnız raporları içeriyordu. İkisi ayrı pakettir.
- Ham doğrulanmış xG CSV SHA256: `a97b23172820ef17b715f6b31a6c279f5a33080ccc83f595081a0490b68e36b5`. 2.155 satır; run raporundaki 2.155 sayısı ile uyuşuyor; diğer 28 kaynak satırı `UNMATCHED` olarak reddedilmiş.
- Her iki artifact'in `historical_results.csv` dosya hash'i dondurulmuş 4.413 maç SHA256'sı ile birebir eşit.
- Aşama 4 sabit C3 matematiğinin **yalnız 2026/27 maç uygunluk kapısı** eski SHA ile bir kez yeniden üretildi. 880 hedeften 873 geçti, 7 geçmedi; önceki Aşama 4 sayısıyla **873/880 regresyon kapısı PASS**. Eski M4 bütün 880 için tahmin verdiğinden bu, C3/M4 ortak maç evrenidir. **Olasılık veya 1X2/KG/Alt-Üst performansı YENİDEN hesaplanmadı.**
- Bu audit yeniden hesaplama kodunun lokal SHA256'sı `8c9d710a80e56eb270803ba56944da9bdb89ada21553d046e24e140ded0d8e97`; aggregate JSON SHA256 `08b326e400ab028312ef733ee91988a9294b9b351a1960297fe183bed9e4e2f3`. Ham veya per-match xG public GitHub'a gönderilmedi.

## Çifte eşleşme sonuçları
Eşik: **hedef maç tarihi dışlayıcı (`source.match_date < target.match_date`)**, ev sahibi için önceki kendi iç saha maçlarında xG, deplasman için önceki kendi dış saha maçlarında xG; hangi sezon olursa olsun aynı ligde doğrulanmış tarihsel kayıt. “5+5” yalnız verinin keşifsel yeterlilik eşiğidir, model parametresi değildir.

| Lig | Ortak C3/M4 n | Her iki takımda ≥1 xG geçmişi | Her iki takımda toplam ≥5 maç | Her iki takımda uygun sahada ≥3 xG | Her iki takımda uygun sahada ≥5 xG |
|---|---:|---:|---:|---:|---:|
| ENG1 | 80 | 77 | 66 | 63 | 57 |
| ESP1 | 98 | 95 | 84 | 82 | 70 |
| ITA1 | 90 | 87 | 76 | 73 | 64 |
| GER1 | 60 | 57 | 48 | 45 | 42 |
| FRA1 | 72 | 70 | 62 | 60 | 56 |
| **Bu beş lig** | **400** | **386** | **336** | **323** | **289** |
| ENG2, NED1, TUR1, POR1, BEL1 | 473 | 0 | 0 | 0 | 0 |
| **10 lig toplamı** | **873** | **386** | **336** | **323** | **289** |

Notlar:
- Hedef maçın kendi xG satırının mevcut olması, o tahminde xG geçmişi kullanılabileceği anlamına **gelmez**; hedef maçın kendi xG'si asla geçmiş girdisi değildir. Ortak 400 maçın 399'unda hedef maç xG kaydı mevcut, biri yok; asıl uygunluk önceki maç kayıtlarından hesaplandı.
- Diğer beş ligde 0, **yalnız incelenen Understat doğrulanmış arşivinin veri kapsamı** için geçerlidir, gerçek dünyada xG yokluğu iddiası değildir.
- Aynı gün veya ileri tarihli hiçbir xG gözlemi geçmişe katılmadı; ama sağlayıcının hangi tarihte hangi xG sürümünü yayımladığını kanıtlayacak historik `as-of` veri sürüm arşivi yok. Tarih kesimi, model-vintage revizyon veya geç yayın sızıntısının olmadığını tek başına **kanıtlamaz**.
- 2026/27 maçları önceki deneylerde görülmüştür, bağımsız dokunulmamış test değildir.

## Mühendislik sonucu ve sonraki tek iş
1. En çok **400** ortak değerlendirme maçı beş xG ligi içinde; daha sıkı “iki takıma da 5 uygun saha xG” eşiğiyle **289 araştırma adayı** bulunuyor. M4+xG lehine bir kazanç henüz kanıtlanmadı.
2. Önce mevcut 289 kaydın **as-of yayın zamanı / xG revizyon sürümü / kaynak kullanım hakkı** belirsizliğini ayrı güvenilirlik kapısında raporla; bu olmadan prospektif xG performans iddiası üretme.
3. Sonra (yalnız kanıt yeterliyse) 289 sabit eşleşme üzerinde kilitli C3/M4'e karşı önceden sabitlenmiş **tek, izole M4+xG model kolu** için deney taslağı hazırlanabilir; Poisson vs xG Poisson 1.549 maç testi **tekrarlanmayacak**.
4. Raw xG içeren `understat-xg-pilot` eski artifact'inin GitHub erişim ve lisans koşullarını ayrıca kontrol etmek gerekir; bunu başka bir public artefakta yeniden yükleme.
5. Ana dal, C3, M4, 100 maçlık ileri pilot, dondurulmuş 4.413 kaynak verisi ve önceki Aşama 4 sonuçları **değişmedi**.
