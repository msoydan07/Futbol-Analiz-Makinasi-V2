# Avrupa kupaları / maç öncesi puan ve turnuva bağlamının etkisi: ÖN KAYIT

**2 Kasım 2026 — Deney dalı:** experiment/263-toplu-karsilastirma.
Yeni tahmin modeli/ana model eklenecek diye bir karar verilmemiştir. B, C2,
C3, M4, yerel 10 lig, Salı saat 10:37 güncellemesi ve 100 maçlık kayıt
DEĞİŞMEZ.

## Kanıtlı kaynak ve sınır
- Açık tarihî kaynak: openfootball/champions-league projesinin
  abfaeddc2ee3d14f99ecc163c9ddb46cb4d67cef commit'i. Üç dosya:
  2024-25/cl.txt, 2024-25/el.txt, 2025-26/cl.txt.
- 2024/25 CL lig aşaması 144 maç 470 gol; 2024/25 EL 144 maç 408 gol;
  2025/26 CL 144 maç 487 gol. Bu toplamlara ilişkin bağımsız UEFA
  yayınları: https://www.uefa.com/uefachampionsleague/news/02a2-1fd452956166-e9ccaec7d032-1000--league-phase-delivers-again-more-goals-more-competitiveness-/
  https://www.uefa.com/uefaeuropaleague/news/0295-1cf1a1ba73b4-c67c43530524-1000--uefa-europa-league-2024-25-league-phase-in-numbers/
- Bu toplamsal doğrulama MAÇ BAZINDA bağımsız UEFA teyidi yerine geçmez.
  2025/26 Europa League bu korpusta mevcut değil; onu test edilmiş
  saymıyoruz. Ayrıca lig takımlarının kendi ev liglerinin gücünü ölçen
  kimlik/doğrudan oranlar burada yer almıyor. Bir "rakip güç" özelliği
  yalnız önceki UEFA maçlarının averaj ve PPG vekilidir.
- Yasak kaynak: akla uygun gibi görünse bile UEFA resmî fikstürü ile
  karşılaştırılmamış 2026/27 üçüncü-taraf satırları doğrudan kabul
  edilmez. Önce bütün sonuçlar bağımsız doğrulanmalıdır.

## Önceden belirlenmiş tek karşılaştırmalı deney
1. Kıyas B0: turnuvaya göre ortalama toplam gol Poisson referansı.
2. Kıyas B1: B0 + geçmiş UEFA maçlarından rakip puan/averaj farkı
   ve ev/deplasman takımlarının önceki toplam golü.
3. Kıyas B2: B1 + maç haftası, son üç haftaya girilmesi ve
   son haftalarda takımların maç öncesi puan farkı/az puanlı takımın
   maç başına puanı (puan ihtiyacının kesin göstergesi DEĞİL).
- **Hedef**: sadece normal süre toplam gol sayısı ve 2.5 Alt/Üst.
  Şut/kadro/xG/oyun içi kırmızı kart/uzatmalar kullanılmaz.
- **Eğitim**: 2024/25 CL+EL (288 maç); **tek mühürlü ileri sezon
  karşılaştırması**: 2025/26 CL (144 maç). Mühürlü sezonu model
  seçimi, katsayı/ceza ayarı ve tekrar eğitim için kullanma.
- Her maçın maç öncesi puan ve averajı sadece önceki UEFA maç
  haftalarının bitmiş sonuçlarından yeniden oluşturulur; aynı gün /
  aynı maç haftası sonuçları kesinlikle kullanılmaz.
- Üç seçenek tek sabit ridge cezasıyla eğitimde hesaplanır;
  parametre arama, model yer değiştirme veya katsayı önerisi yok.
- Sonuçta ortalama Poisson log-loss, 2.5 üst Brier, gol MAE ve
  maç haftası bloklarına göre belirsizlik aralığı raporlanır.
- Belirsizlik aralığı yalnız sekiz maç haftasına dayanır; nedensel
  taktiksellik kanıtı değildir.

## Karar eşiği
Başarı görülse bile UEFA 2025/26 EL bağımsız sonuçları, UEFA
maç sayfası teyidi ve farklı sezonda tekrar edilmeden hiçbir
Avrupa maçında gol katsayısı uygulanamaz. Maç başına golü
otomatik %10 azaltmak veya C2/M4'i Avrupa'ya zorla taşımak yasak.

Çıktı sadece data/europe_staged_263/uefa_context_ablation_263.json
ve GitHub Actions artefaktına yazılır. Kayıt açılmaz.
