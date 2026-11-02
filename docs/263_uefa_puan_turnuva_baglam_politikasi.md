# 2.6.3 — UEFA maç aşaması / puan ihtiyacı / gol temposu riski

2 Kasım 2026 — Avrupa kupaları aday katmanına eklenen **tahmin üretmeyen, yalnız maç öncesi bağlam**.

## Resmî UEFA 2026/27 kuralları
- CL ve EL lig aşaması: 36 takım; her takım sekiz farklı rakiple oynar; 3/1/0 puan; ilk 8 doğrudan son 16, 9-24 play-off, 25-36 elenir.
  https://documents.uefa.com/r/Regulations-of-the-UEFA-Champions-League-2026/27/Article-17-Match-system-league-phase-Online
  https://documents.uefa.com/r/Regulations-of-the-UEFA-Europa-League-2026/27/Article-17-Match-system-league-phase-Online
- Eşit puanda ilk kriter averaj, ikinci atılan gol. Skorun önemi sadece kazan/kaybet değildir.
  https://documents.uefa.com/r/Regulations-of-the-UEFA-Champions-League-2026/27/Article-18-Equality-of-points-league-phase-Online
- Elemede normal durumda iki ayak ve toplam gol. İkinci ayak öncesi **mevcut ev/deplasman yönünde** toplam skor tutulur. Uzatma ve penaltılar 90 dakikalık bahis pazarlarına karışmaz.
  https://documents.uefa.com/r/Regulations-of-the-UEFA-Champions-League-2026/27/Article-20-Match-system-knockout-phase-Online
  https://documents.uefa.com/r/Regulations-of-the-UEFA-Champions-League-2026/27/Article-21-Knockout-system-extra-time-and-penalty-shoot-outs-Online
- Avrupa için 'daha temkinli, gol beklentisini %10 indir' gibi bir sabit kural **YANLIŞ**. UEFA 2025/26 Şampiyonlar Ligi lig aşaması **487 gol / 144 maç = 3,38 gol/maç** raporlamış.
  https://www.uefa.com/uefachampionsleague/news/02a2-1ff0ca380c74-2f4592c3f969-1000--champions-league-goals-analysis-of-the-league-phase/

## Bu değişiklik hangi bilgiyi hazırlıyor?
`experiments/263/europe/uefa_match_context_263.py` yalnız Avrupa staging adayına ayrı kaynak ve zamanlı veri iliştirir:
- **Lig aşaması:** maç haftası; maç ÖNCESİ iki takımın puanları, maç sayıları, averajı, mevcut sırası, bitmemiş maç adedi. Mevcut ilk 8/9-24/25-36 sırası *nihai eleme* olarak işaretlenmez.
- **Elemeler:** 1. veya 2. ayak, ikinci ayaksa o maç başlamadan önce mevcut ev/deplasman takımları için toplam gol durumu, ilk ayak ayrı UEFA maç linki.
- **Final:** tek maç ve tarafsız saha.
- Zaman damgası maçtan önce olmak zorunda. Maçtan sonraki puan durumunu veya skoru geri taşıma (lookahead) kabul edilmez. Kaynak URL'sinin doğru görünmesi gerçekten açılıp teyit edildiği anlamına gelmez.
- `goal_multiplier=None` ve `forecast_authorized=False`. Bu veri gözlem; gol beklentisine göre otomatik ağırlık/alt-üst kararı üretmez.

## Sonraki deney (henüz yapılmadı)
Gerçek UEFA geçmiş ve ligler arası takım kimlikleri toplandıktan sonra kronolojik karşılaştırma:
1) Yerel lig gol ortalaması **tek başına** (referans),
2) aynı hesap + rakibin ülkeler arası kalibre edilmiş gücü,
3) aynı hesap + maç türü/ev/deplasman/puan-sıra/hafta/eleme turu/ilk ayak skoru.
Performans: MS logloss+Brier, gol sayısı likelihood ve 2.5 Alt/Üst kalibrasyonu; yalnız eşleşen ve maçtan önce doğrulanmış veriler. Modül ablation ve farklı sezon bağımsız doğrulama. Verinin azlığında geniş belirsizlik, zorla model terfisi yok. 'Must win' puandan tek başına kesin çıkarılmaz. Dört modelin mevcut matematiği ve 10 lig değişmez.
