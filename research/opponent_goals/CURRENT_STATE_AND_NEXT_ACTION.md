# Futbol 2.6.3 — TEK ÇALIŞMA DURUMU, 10 Kasım 2026

Bu dosya yeni rapor fabrikası değil, **tekrar iş açmamak için durum defteri**. Değişen yalnız burası olsun; birbirinin aynısı 99-maç / KG araştırmaları yeniden üretilmesin.

## KAPANDI — tekrar açma (yeni kanıt yoksa)

- **99 yeni maç adayı:** Tek kayıtla 99/99 mevcut Salı staged 4.617 satırlık dosya ile lig+tarih+home_id+away_id+skor bakımından uyuşuyor, skor çelişkisi **0**. Önceden kabul edilmiş 4.518 kaydın **9 ENG2** satırında `source_url/source_row`, ilk yarı/şut/korner/faul/kart alanlarını sessiz değiştirdiği için staged dosyanın doğrudan kabulü **RED**.
- **Güvenli uygulama:** 4.518 özgün kayıt verisini aynen koruyup **99 adayı ayrı geçici araştırma gölgesine** ekleyen tekrar üretilebilir kod ve SHA manifestosu var. Günlük M4 bu gölgeyi kullanmıyor, kabul edilmiş veri hâlâ **4.518**.
- **Kaynak sınıfları:** 28 kaynak+resmî lig sayfası araştırma konkordansı; 28 resmî lig/federasyon/kulüp sayfası skoru ama ikinci sağlayıcı satırı kontrolü yok; son 43 yayımcı/diğer dış sonuç kayıtları ve kısmi birincil fikstür teyidi. **Hiçbir yeni maçın benzersiz federasyon fixture ID attestasyonu veya haklarına uygun üretim kabulü yok.** Sayı eşleşmesini resmî onay olarak satma.
- **Daha önce araştırılan 984 tarihsel maç:** M4, DC (-0,08), ortak Poisson şoku (0,12) daha önce adil retrospektifte karşılaştırıldı; KG için çok küçük kazanımlar bazı MS ve gol çizgilerini kötüleştiriyor. **Yeni model terfisi yok, aynı testi tekrar yapma**.
- **Rakip gücü:** 4.518 geçmiş maçın as-of basit Elo ile tarif edildiği keşifsel bantları hazır. 1.280 takım×saha×güç grubunun 609'u 5'ten az maç, taktik/PPDA/press doğrudan ölçülmedi. **Küçük n'den takım oyun tarzı katsayısı ekleme yok**.
- **Yeni gerçek mühür incelemesi:** 8 Kasım orijinal 40 maç önü SHA'dan 39 araştırma sonucun skorlandı, 1 erteleme. M4 KG Var tahmin ortalaması **%53,57**, gerçekleşen **%53,85**; 2,5 Üst M4 **%54,40**, gerçekleşen **%51,28**; toplam gol beklenen-gerçek farkı yaklaşık **+0,002 gerçek gol/maç**. Bu, önceki 984 retrospektif maçın 2.5 Üst negatif sapmasının **evrensel sabit olmadığını** gösterir. 39 maç tek gün/4'ü medya; kalibrasyon sertifikası değildir.
- **Karşılaştırma:** 39 araştırma skorunda M4, basit aynı lig tarihsel oran baselinesına KG ve 2,5 Üst Brier bakımından çok az kaybetti; yalnız 35 birincil sonuç alt kümesinde M4 az farkla daha iyiydi. Her iki örnek çok küçük, model kazananı ilan edilmedi.

## AÇIK — yalnız kanıt gelirse ilerletilecek

1. **Veri resmî kabulü / 99:** federasyon/lig maç ID + kimlik/tarih/sonuç, önceki sağlayıcıya ait kaynak satırı güvenilirliği, kullanım hakkı; 9 eski ENG2 için ayrı ve geriye dönük kayıt bozmayan enrichment. **Yeni kaynak kanıtı veya kullanım izni yoksa tekrar CSV arama / yeni dal / eski test YOK.**
2. **Gerçek ileri kalibrasyon:** yeni SHA mühürlü, farklı günlerden gelen, güvenilir maç sonrası skorlar biriktikçe **MS1/X/2, KG Var ve 1,5/2,5/3,5** olaylarının bant bazlı kalibrasyonunu izlemek. Bir tek günden **%70 güvenilir** veya **+%7 üst düzeltmesi** türetme. Gerekli olan yeni bağımsız kanıttır.
3. **Rakibe göre taktik etkileşimi:** pres/blok/oyuncu/game-state için güncel **2026/27 10 lig** kapsamlı, kullanım hakkı açık maç olay verisi bulunmadan yeni “rakip kimliği” çarpanı YOK.
4. **Matematik araştırması** yalnız yeni kanıt mevcut M4 eksikliğini doğrularsa tekrar açılmalı; ayrı C3/DC/Bivariate aynı maçlarda kanıtlı KG/Üst gelişimi + MS güvenliği göstermeli. Pas korunmalı.

## ORİJİNALİ KORUMA (kesin)

`main`, `experiment/263-toplu-karsilastirma` M4 kodu ve kilidi, 4.518 kabul geçmişi, 40 SHA mühür, 40 karar dosyası, 10 lig otomasyon saati, LITE ve basketbol değiştirilmedi. Araştırma dalı `research/263-staged99-evidence-join-20261110` yalnız kanıt/kod/rapor.

## İSPATLAR

- [99 staged+published eşleşme ve 9 orijinal değişiklik](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-staged99-evidence-join-20261110/research/opponent_goals/reports/staged4518_4617_published99_comparison_20261110.json)
- [4518+99 güvenli araştırma gölgesi manifestosu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-staged99-evidence-join-20261110/research/opponent_goals/reports/append_only_4518_plus99_provisional_manifest_20261110.json)
- [Gerçek 40 mühür/39 sonuç M4 KG-Üst-gol beklentisi ve rakip güç incelemesi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-staged99-evidence-join-20261110/research/opponent_goals/reports/sealed_nov8_goal_error_and_strength_20261110.json)
- [Yeni kontrollü KG/Üst/rakip gücü CI testi (success)](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42796904122)

**TEK SONRAKİ YAPILACAK İŞ:** Kullanıma elverişli **yeni ve bağımsız maç sonrası skor kanıtı** geldiğinde, eski 39'u tekrar pilota dönüştürmeden, gerçek tarih bloklu M4 KG/Üst kalibrasyonunu bu yeni günlerde ölçmek. O zamana kadar M4 üretim yüzdeleri değişmesin.
