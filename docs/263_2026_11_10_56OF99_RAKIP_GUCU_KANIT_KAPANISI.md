# Futbol 2.6.3: 99 kaynak adayı + rakip gücü örneklem denetimi — mühendislik kapanışı

**Durum:** 10 Kasım 2026 | Araştırma, değişmez orijinal M4 | Sıradaki iş: kalıcı bağımsız skor ve güncel olay verisinin kaynak/hak fizibilitesi.

## 1. Tam olarak ne doğrulandı?

| Sınıf | n | Kanıt | Bu sınıf ne değildir? |
|---|---:|---|---|
| Kaynak CSV ile resmî/kulüp skor sayfası birbirine uyan, **eski araştırma düzeyindeki** küme | 28 | 9 TUR1, 9 GER1, 10 ITA1; [mühürlü çapraz denetim](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-official-score-reconcile-20261110/research/opponent_goals/reports/official_round_score_concordance_20261110.json) | Federasyonun tekil resmî maç ID'siyle sonuç attestasyonu değildir |
| Doğrudan lig/federasyon sayfasında yayımlanan, **henüz CSV maç satırıyla eşleştirilmemiş** skorlar | 19 | ESP1 10: [La Liga](https://www.laliga.com/laliga-easports/resultados/2026-27/jornada-12); NED1 9: [KNVB](https://www.knvb.nl/competities/eredivisie/uitslagen) | 19 provider konkordansı değildir; KNVB skorlarında 5 iş gününe kadar değişiklik uyarısı vardır |
| Kulüp haftalık toplu sonuç özetinden skorlar, **henüz CSV maç satırıyla eşleştirilmemiş** | 9 | FRA1 9: [PSG lig 10. hafta](https://www.psg.fr/en/content/ligue-1-matchday-10-results-2026-2027-paris-saint-germain-estac-troyes) | Fransa ligi federasyonunun maç kimliği/sonuç attestasyonu değildir |
| Kaynakta tam maç adayı var; bu turda uygun resmî/kulüp sayfasında skor tek tek yakalanmadı | **43** | BEL1 10, ENG1 10, ENG2 15, POR1 8 | “Sonuç yok” demek değildir; yalnız bizim kanıt dosyamızda birincil skor bağlantısı henüz yok |
| **TOPLAM** | **99** | Tüm 10 ligde önceki veri sağlayıcı SHA ve kanonik kimlik kaynak eşlemesi başarılı | **99 resmî kabul edilmiş maç değil** |

Bu turda yeni kayıtların sayısı **28**, toplam kamuya açık lig/kulüp kaynaklarında skor gözlemi **56/99**. Resmî kaynak sonuçlarının karşılaştırması için bu hafta Football-Data'dan **üçüncü indirme yapılmadı**. Site kişisel/akademik hafif indirmeyi haftada en fazla ikiyle sınırlıyor. Lisans ve kaynak hakkı kararı korunur.

[28 yeni kayıt](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-additional-official-evidence-20261110/research/opponent_goals/official_additional_28_nov06_08_2026.json), [ayrı hata-zorlama/offline test raporu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-additional-official-evidence-20261110/research/opponent_goals/reports/extra_official_28_evidence_20261110.json), [birleşik kanıt katmanı hesabı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-public-scoreboard-expansion-20261110/research/opponent_goals/reports/official_public_evidence_layers_20261110.json).

## 2. Beşiktaş örneğindeki asıl matematik riski

Rakip gücü segmentlerini sıkça böldüğümüzde **1.280 takım × iç/dış saha × güç aralığı hücresinin 609'u (%47,58) beş maçtan az** içeriyor. Yalnız **477 hücre (%37,27) sekiz veya daha fazla maç** içeriyor. Bu grupların çoğunda “rakibe karşı nasıl oynuyor” istatistiklerini anlamlı bir yeni katsayıya dönüştüremeyiz.

Beşiktaş'ın kendi sahasında, yalnızca mevcut 4.518'lik kabul edilmiş tarihi arşivde:

| Rakip ön-Elo sınıfı | n | 2,5 Üst geçmiş frekansı | %95 Wilson **bağımsız maç varsayımıyla referans aralık** |
|---|---:|---:|---:|
| Benzer güçte rakip | 11 | 7/11 = %63,6 | yaklaşık **%35,4–84,8** |
| Beşiktaş 50–150 Elo daha güçlü | 10 | 8/10 = %80,0 | yaklaşık **%49,0–94,3** |

Aralıklar **örtüşüyor**. Bu, ikinci sınıfta “gerçek %80 olasılık” diye model kurmaya yetmez. Maçlar bağımsız değil, dolayısıyla Wilson gerçek belirsizliği *azımsayabilir*. Aynı taktiksel oyun planını izleyip izlemediklerini de goller/şutlar tek başına söylemiyor. [Yeni belirsizlik denetimi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-public-scoreboard-expansion-20261110/research/opponent_goals/reports/team_opponent_strength_uncertainty_20261110.json) ve [GitHub başarılı test](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42786095868).

**Mühendislik hükmü:** Eski M4'ün maçlar üstünden güç düzeltmesini koru; küçücük hücrelerde yeni “rakip taktiği” katsayısı ekleme. Pres/blok yüksekliği, pozisyon konumu, gerçek xG, game-state ve kadro etkisi için farklı kaynak verisi gerekiyor.

## 3. Gerçek oyun tarzı verisi araştırması

- [StatsBomb/Hudl Open Data](https://github.com/hudl/open-data): GitHub'daki açık `data/competitions.json` kataloğunda **80 competition-season kaydı var; 2026/27 yok**. Tarihsel event ve 360 için yöntem/prototip mümkün; güncel 10 lig gerçek pres verisi sağlanmış sayılmaz.
- [Wyscout Pappalardo örneği](https://github.com/koenvo/wyscout-soccer-match-event-dataset): açık CC BY 4.0 örnekler büyük beş lig **2017/18** ve turnuvaları kapsıyor. Kavram denemesi için uygun; 2026/27 güncel takım davranışı için doğrudan kullanılamaz.
- [Metrica Sports sample](https://github.com/metrica-sports/sample-data): iki anonim örnek maçla tracking/event formatı öğretir; 10 lig güncel sayısal gösterge kaynağı değildir.

**Sonuç:** “Rakip güç ve taktik Poisson'dan önce gelsin” fikrini açıklayıcı özellik mühendisliği açısından araştıracağız. Fakat veri yokken pres/oyun stili etiketi çıkarıp %KG veya %Üst'e eklemeyiz.

## 4. Bu turda nerede duruyoruz?

- 4518 özgün owner-accepted historical CSV SHA, M4 matematik kilidi, 40 orijinal maç önü mühür ve 40 karar SHA'sı **değişmedi**.
- `experiment/263-toplu-karsilastirma` dalında ayrıca **10 Kasım Salı veri güncellemesi staged/pending review** olarak hareket etmiş; bu tek başına kabul edilmiş güncel eğitim verisi değildir. Research dalından otomatik birleştirilmedi.
- Sabit KG/Üst alternatiflerinin 984 maçlık geçmişe dönük denemesi zaten yapılmıştı; KG'de ufak kazanım diğer bazı gol marketleri/MS aleyhine olduğundan **model terfisi YOK**.
- Asıl sonraki kabul kapısı: 43 ek maç için uygun tekil resmî sayfa/fixture ID; mevcut 56'nın 28 yeni skorunda kaynak satırı rekonsilyasyonu ve resmî maç ID attestation; sonra haklara uygun ayrı append-only veri kabulü.
- Yeni olay/oyun tarzı veri kaynağına ticari/kapalı lisans varsayımıyla geçme; sadece doğrulanabilir sezona uygun coverage varsa ve **ayrı bağımsız ileri maç kanıtı** üretebiliyorsa sayısal model denemesi.
- Bu araştırmayı, 96 maçlık diğer pilotları ve görülmüş 984 maçlık 2026/27 araştırma sonuçlarını yeni testmiş gibi tekrar çalıştırma.

**Nihai karar:** 56 adet resmî lig/federasyon/kulüp sonuç gözlemi, bunların 28'i önceki sağlayıcıyla çapraz tutarlı; 43'ünde bu turda kamuya açık resmî/kulüp skoru tespiti tamamlanmadı. Mevcut M4 çalışmaya devam. Hileli kesinlik, dış veri/kaynak lisansı varsayımı veya geçmiş set üzerinden yeni katsayı YOK.
