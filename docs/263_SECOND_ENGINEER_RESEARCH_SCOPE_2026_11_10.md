# 2.6.3 bağımsız ikinci mühendis denetimi — araştırma sınırları

Kapsam: 8 Kasım 2026 tarihli, `new100` 40 orijinal SHA mühürlü dört-model tahmin; sonradan web üzerinden gözden geçirilmiş **39 sonuç, 1 erteleme**. **35** maçta lig/kulüp birincil sayfası; **4** maçta medya çapraz teyidi. Resmî yeni100 insan onaylı veya bağımsız ağ üzerinden teyit edilmiş sonuç kaydı olarak gösterilemez.

## Denetimin birbirinden bağımsız kapıları

1. Tahmin dosyası ve batch raporu hash eşleşmesi; resmî kaynak kapısı, maç önü zamanlar, iki kulübün farklı kimlikleri, maç gününün yerel tarihine sadakat.
2. Her *AVAILABLE* B/C2/C3/M4 çıktısının aynı skor dağılımından türemesi gereken tutarlılık: H+D+A=1; KG Var+Yok=1; Üst1,5 ≥ Üst2,5 ≥ Üst3,5; Alt+Üst=1; KG Var≤Üst1,5; MS1/MSX/MS2 aliasları.
3. Gerçek maç sonucu **olmayan** maçın her performans paydasından çıkarılması. Kısmi model çıktısı kalan modellerin kapsamına hileli şekilde eklenemez.
4. **%70 kontrolü**: %65–75 tahmini üretilmiş kaç maçta olay gerçekleşmiş; ayrı ayrı MS en yüksek yönü, ev/beraberlik/deplasman, KG Var, Üst1,5 / 2,5 / 3,5. Wilson referans aralığı ve **farklı maç günleri** sayısı. Korelasyon nedeniyle marketler havuzlanıp sahte n oluşturulmaz.
5. En az 100 aynı tip tahmin ve en az 5 farklı maç günü olmadan sadece örneklem tanımı; bu eşik geçilse bile bağımsız gelecek veri ve kaynak doğrulaması olmadan “%70 gerçektir” sonucu yasaktır. Rastgele eşik istatistiksel üstünlük kanıtı değildir.
6. **Görülmüş sonuçlarla yeni katsayı veya güven sınıfı ayarlamak yasak.** 8 Kasım araştırma veri kümesi hem bulgu üretip hem bağımsız ispat için kullanılamaz.
7. **896 maçlık retrospektif 2026/27 ortak haftalık kesit, gerçek sabah mühürlü 896 maç değildir.** Geçmiş araştırmadan gelen 53,35% MS isabet, “%70 bin güvenilir” sorusunun kanıtı sayılmaz.

## İkinci mühendisin baştan itirazları

- Her sonuç için lig+kulüp adından ve sonradan açıklanan web sonucundan bağ kurmak **resmî sonuç tarafında değişmez kulüp/maç ID eşleşmesi** demek değildir. Yanlış kaynağa bağlama ihtimali kapanmış sayılmaz.
- Resmî skor/ertelenme kaynakları aynı kalite katmanında değil; yalnız birincil kaynaklı alt küme de mutlaka raporlanır.
- Bir günde 39 maç ve aynı takımların/liglerin koşulları, %70/30 kalibrasyonunun tekrarlanabilirliğini ispatlayamaz.
- 1,5 Üst ve 3,5 Alt gibi temel oranlar yüksek gerçekleşme sıklığına sahip olabilir; yön isabeti tek başına üstünlük veya parasal değer değildir.
- Dört modelin çıktıları eşit kapsamlı değil; 35 ortak ve M4'ün tek başına değerlendirilen maçları karıştırmayın.
- Üretim mevcut `experiment/263-toplu-karsilastirma`, `main` ve `research/model-challenge` dalları **değiştirilmedi**. Ayrı `research/263-second-engineer-audit` araştırması yalnız doğrulama kodu, sentetik test ve kanıt raporu üretir.

## Sonlu iş sırası

- Gerçek, sağlayıcıdan yeniden doğrulanmış tamamlanmış skorları **aynı kanonik fikstür kimliğiyle** postmatch attestation dosyasına güvenli şekilde bağlamak; isim tabanlı geçmiş research skorlarını otomatik resmî sayma.
- Aynı piyasa ve aynı as-of kesiminde B/C2/C3/M4 ve basit karşılaştırma modellerinin Brier/logloss/lig/olasılık dilimi testini yeterli *farklı gün* boyunca yürütmek. Önce performans dürüstçe raporlanır; ancak destek varsa model değişir.
- Yeni model/xG/oyuncu/rotasyon/şut hızları eklemek öncelik değildir. Şimdiki sınırlı sonuçlar model yükseltmesi veya para kazandırdığı iddiasına izin vermez.
