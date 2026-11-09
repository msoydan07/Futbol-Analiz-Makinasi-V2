# 2.6.3 — 8 Kasım maç önü mühürleri × gerçek skorlar: değerlendirme ve kullanım kararı
**Kayıt tarihi:** 9 Kasım 2026  
**Kaynaklı hesaplama:** GitHub Actions [#42602340996](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42602340996) (başarılı, iki kontrol)  
**Kapsam:** Sadece 8 Kasım `new100` grup mühürleri; 6 Kasım legacy96 ve 7 Kasım araştırması ayrı. Ana 2.6.3 M4 kilidi ve LITE değişmez.

## 1. Gerçek sayım — sonuçları uydurmadan
- Birinci gerçek sabah batch: `new100_42469245388.json` → **33** kalıcı mühür.
- İkinci gerçek sabah batch: `new100_42469487639.json` → **7** kalıcı mühür.
- **40** ayrı, SHA doğrulanan maç önü tahmini; kimlikler batch raporu ve kaydedilmiş Git blobları ile eşleşiyor.
- **39** maç tam skorla tamamlandı. **1** maç, **Estoril–Marítimo**, Liga Portugal resmî bildirimiyle ertelendi. `SC Cambuur–PSV` ve `FC Utrecht–NEC` 42 isimli başlangıç listesindeydi ama resmî `new100` SHA kayıtları arasında yok: bu iki maç skor başarı paydasına **eklenmedi**.
- **35** tamamlanan maçta kulüp/lig sayfası skor kaynağı; **4** Portekiz maçında VSports video-sonuç sayfası + ikinci bağımsız skor sayfası çapraz kontrolü. Bu dört kayıt skor karşılaştırmasına **araştırma düzeyinde** eklendi, ayrıca `PRIMARY_ONLY` ölçümü de raporlandı.
- Resmî insan onaylı GitHub sonuç-attestation kaydı yazılmadı (`sabah_postmatch_inputs` altında 0). Bu değerlendirme asistanın webden baktığı skorların **salt okunur araştırma üst katmanıdır**, otomatik resmî sağlayıcı doğrulaması değildir.

## 2. Maç öncesi dondurulmuş 8 Kasım modellerinin MS sonuçları
| Model | Yön doğru | İsabet | MS Brier | MS log-loss |
|---|---:|---:|---:|---:|
| B | 21/34 | %61,76 | 0,533573 | 0,909909 |
| C2 | 21/38 | %55,26 | 0,544410 | 0,916640 |
| C3 | 25/39 | %64,10 | 0,517322 | 0,885233 |
| **M4** | **25/39** | **%64,10** | **0,509959** | **0,875300** |

Örneklem farkları unutulmasın: B 34, C2 38, C3 ve M4 39 maçta çalıştı. C3–M4 **aynı 39 maçta** 1X2 yönü eşit, M4 çok sınıflı Brier ve log-loss daha düşük.
Aynı ortak kayıtlar üzerinde diğer modelin MS Brier'inden M4 Brier'ini çıkarınca: B−M4 **+0,021293** (n=34), C2−M4 **+0,025178** (n=38), C3−M4 **+0,007363** (n=39). Pozitif, bu örnekte M4 lehine. **Bunlar bağımsız uzun-vade üstünlük veya bahis kârı iddiası değil.**

## 3. KG ve 2,5 Alt/Üst — tek örneklemde beliren zayıf alan
| Model | KG yön | KG Brier | 2,5 yön | 2,5 Brier |
|---|---:|---:|---:|---:|
| B | 21/34 | 0,237444 | 16/34 | 0,260184 |
| C2 | 25/38 | **0,225852** | 22/38 | **0,252027** |
| C3 | 19/39 | 0,246367 | 20/39 | **0,247555** |
| M4 | 20/39 | 0,248164 | 21/39 | 0,262744 |

KG'de C2'nin, 2,5 Üst'te C3'ün olasılık hata puanı bu örnekte daha iyi. **Farklı n ve küçük örneklem nedeniyle**, bu tabloya bakarak KG veya gol için yeni otomatik motor seçicisi terfi ettirilmiyor. Bunlar günlük kullanım sırasında takip edilecek açık araştırma bulgularıdır. İlk yarı/köşe gibi eksik pazarlar sırf bu değerlendirmeyle üretilmiş sayılmaz.

## 4. Birincil kaynaklarla sınırlı 35 maç
| Model | Değerlendirilen n | MS doğru | MS Brier |
|---|---:|---:|---:|
| B | 30 | 18/30 | 0,559823 |
| C2 | 34 | 18/34 | 0,568922 |
| C3 | 35 | 21/35 | 0,544014 |
| **M4** | **35** | **22/35** | **0,533531** |

Portekiz'deki dört medya çapraz kontrol skoru çıkarılsa da M4, birincil kaynaklı maçlarda bu dört model arasındaki en düşük MS Brier'e sahip.

## 5. Kod, yeniden üretilebilirlik ve güven sınırı
İzolasyon dosyaları:
- `experiments/263/nov8_webreview_results_263.json`: skor, kaynak URL'si, sınıf ve erteleme.
- `experiments/263/score_nov8_webreview_263.py`: mevcut iki batch'ten SHA yolunu okur; **40 kimliğin birebir eşleşmesini**, orijinal tahmin SHA'sını, kickoff öncesi kayıtları, olasılık toplamını doğrular; sonradan modeli çalıştırmaz. Erteleme otomatik dışlanır.
- `experiments/263/test_score_nov8_webreview_263.py`: 40 SHA, 39 skor, 1 erteleme, 35/4 kaynak ayrımı ve M4 çalışma kapsamı.
- `.github/workflows/263-nov8-webreview-score-readonly.yml`: GitHub'da yeşil; kod hiçbir `new100` tahminini, sonucu, kasayı, Pinnacle kota dosyasını veya `main` dalını değiştirmez. Çıktı Actions artifact'inde 30 gün saklanır.
- Gerçek model sonrası eşleştirici için `sabah_postmatch_new100_263.py` içinde resmî sayfa kontrolü başlangıç damgasından en fazla **60 saniye** sonra olabilir, ancak iki damga da **maç başlangıcı öncesi** olmalıdır. Aynı GitHub SHA üzerinden sentetik kontroller yeşil: [#42602340891](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42602340891). Bu, mevcut dosyaların sonradan düzenlenmesi değildir.

**Saha kararımız:** M4, mevcut 2.6.3 ana analiz matematiği olarak kullanılmaya **devam**. C2/C3/B yardımcı kıyas; KG/2,5 gözlemleri gelişim notu. Yeni pilot için bekleme şartı **YOK**. Geçmiş tahminlerin resmî yeni100 attestation kaydı yoksa o kayıtları otomatik resmî pilot başarı tablosuna terfi ettirmek **YOK**.

## 6. Kaynak sınıfları
- Türkiye: TFF 8 Kasım maç kayıtları; Alanyaspor–Trabzonspor için Trabzonspor resmî maç sonucu.
- İngiltere: PremierLeague.com 8 Kasım Matchweek 10 sonuçları.
- Almanya: Bundesliga.com 9. hafta tamamlanmış maç haberleri.
- İspanya: LaLiga.com 2026/27 Jornada 12.
- İtalya: LegaSerieA.it 8 Kasım haber ve sonuçları.
- Fransa: Ligue1.com 10. hafta özeti ve Stade Rennais resmî kulüp sonucu.
- Hollanda: KNVB Eredivisie sonuçları.
- Belçika: ProLeague.be J11 resmî fikstür/sonuçlar.
- Portekiz dört skor: VSports.pt + ScoresLive.pt (medya çapraz kontrol); Estoril–Marítimo: LigaPortugal.pt 29049 resmî erteleme bildirimi.

**Şimdi kapanış durumu:** 96 adaylı geçmiş program zaten analiz amaçlı değerlendirildi. 8 Kasım kalıcı mühürlerinden 39'una gerçek skor bağlayan *araştırma* karnesi artık sayısal olarak çıkarıldı. Sıradaki operasyonel iyileştirme artık yeni pilot tasarlamak değil; skorların resmî/insan teyitli girişini ve kullanıcının sabah talebiyle GitHub'ın tetiklenmesini sadeleştirmek.
