# M4 — Aşama 5 xG geçmiş sürüm / yayın zamanı / kullanım hakkı kabul denetimi
**2026-11-03 · KESİN DURUM: ASOF_EVIDENCE_MISSING / RESEARCH_ONLY / MODEL TERFİSİ YOK**

## Amaç ve değişmezlik
873 ortak C3/M4 maçındaki 289 adet iki takıma da ≥5 **saha-özel geçmiş xG** kaydı bulunan adayın, gerçekten o maçların tahmin tarihinde elde edilebilir veriyle değerlendirilip değerlendirilemeyeceğini denetlemek. Ana dal, eski C3/M4 matematiği, 4.413 maçın SHA'sı, eski tahminler ve 100 maçlık ileri pilot değiştirilmedi. Test/performance tekrar çalıştırılmadı.

## İncelenen somut kanıt
- 4.413 maç SHA256: `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- Doğrulanmış xG CSV: 2.155 satır, SHA256 `a97b23172820ef17b715f6b31a6c279f5a33080ccc83f595081a0490b68e36b5`.
- xG arşivi: GitHub Actions `41287280687`, artifact `13074948510` (`understat-xg-pilot`), oluşturulma: **2026-11-01T09:06:49Z**. Arşivde `historical_verified_xg.csv`, `understat_matches.csv`, kaynak URL'leri, denetim eşleştirmeleri var.
- Dondurulmuş ortak 873 cohort ve 289 yeterli-saha-geçmişli aday, bir önceki [kesişim kanıtından](263_M4_asama5_873_xg_kesisim_kabul_2026_11_03.md) alındı. 289 hedef maçın tarihleri **2026-08-15 – 2026-10-29**. Tamamı incelenen xG arşivinin oluşturulmasından önce.
- CSV alanları: fixture_id, league, season, match_date, home_id, away_id, home_goals, away_goals, home_xg, away_xg, understat_source_url. **published_at, retrieved_at, model_version, source_value_version bulunmuyor.**
- Dosya içi kaynak URL'si ve match_date, xG'nin hedef maçtan önce hangi sürümde yayımlandığını kanıtlamıyor.

## Kanıta dayalı sınıflama
| Kontrol | Sonuç |
|---|---|
| 2.155 satırın maç kimliği, ev/deplasman ve skor eşleşmesi | Önceki denetim PASS |
| 873 ortak maç içinde ≥5+5 saha xG geçmişi | 289 araştırma adayı |
| Kaynak xG değerleri hedef tarihten eski maçlara ait | Tarihsel maç kesimi PASS |
| 289 hedef için maç öncesi zaman damgalı xG snapshot | **0/289 KANITLANMIŞ** |
| Understat'ın xG'yi geriye dönük güncellediğine dair özgül sürüm değişikliği | KANIT YOK; gerçekleştiği iddia edilmez |
| Geçmiş xG sürümünün sabit ve zamanında hazır olduğuna dair kanıt | KANIT YOK |
| Public ham xG dosyasını yeniden dağıtma izni | DOĞRULANAMADI |

**Yorum:** '0 kanıtlanmış' = incelenen arşiv ve metaveride karşılaşılmayan kanıt. 'Gerçekte o tarihte xG yoktu' demek DEĞİLDİR.

## 289 örneğin dağılımı
| Lig | n |
|---|---:|
| ENG1 | 57 |
| ESP1 | 70 |
| ITA1 | 64 |
| GER1 | 42 |
| FRA1 | 56 |
| **Toplam** | **289** |

Ağustos 71, Eylül 109, Ekim 109. Aynı gün sonraki maç bilgisi geçmişe dahil edilmedi, ancak bu kontrol sonradan hesaplanmış/yenilenmiş xG modelinin tarihsel sürümünü kanıtlamıyor.

## Dış kaynak ve hukuki kontrol
1. SoccerData resmi belgeleri, Understat sayfalarından indirilen verinin önbelleğe alınabildiğini ve güncellemenin kaynakta ne zaman yapıldığını SoccerData'nın bilemediğini belirtiyor: https://soccerdata.readthedocs.io/en/stable/reference/understat.html ve https://soccerdata.readthedocs.io/en/stable/intro.html.
2. Understat'ın xG verilerine **kamusal okuma erişimi**, üçüncü kişilerin ham veriyi açık depoda **yeniden dağıtma hakkı** olduğunu kendi başına kanıtlamaz. İncelemede resmî, yeterince açık bir public redistribution lisansı doğrulanamadı; herhangi bir hukuka aykırılık hükmü de verilmedi.
3. GitHub deposunun görünürlüğü `public`. Yukarıdaki eski artifact `historical_verified_xg.csv` dahil **ham sağlayıcı verisi** içeriyor, hâlen mevcut; `expires_at=2027-01-30T08:04:15Z`. GitHub belgeleri read erişimi olanların artifact indirebildiğini belirtir: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts. Dolayısıyla önceki 'ham xG public GitHub'a konmadı' varsayımı **yanlıştı**: Git deposuna commit edilmemiş olmak, GitHub Actions artifact'inin public repo üzerinden erişilebilir olmasını engellemez.
4. Ayrıca eski workflow `.github/workflows/understat-xg-pilot.yml` (`feature/01-kimlikler`), artifact paketine hem `data/understat_matches.csv` hem `data/historical_verified_xg.csv` yüklüyor. Bu yol ileride aynı riski tekrarlayabilir.
5. GitHub'ın artifact silme kılavuzu: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/remove-workflow-artifacts. Silme geri alınamaz; bu denetimde artifact silinmedi.

## Kesin mühendislik kararı
- **Sıkı tarihsel maç-öncesi M4+xG backtest: ŞİMDİLİK BLOKE.** 289 yeterli örnek içindeki `as-of` kanıtı 0. Önceki 1.549 maçlık xG-Poisson karşılaştırması tekrarlanmaz; xG'nin M4'e yeni katkısı kanıtlanmış sayılmaz.
- **İzinli ve izolasyonlu keşifsel duyarlılık analizi** teorik olarak mümkün; tarihsel sürüm yanlılığı yüzünden böyle bir analizden model terfisi veya pilot bahis sinyali çıkarılamaz. Yeni bir deney çalıştırılmadı.
- Doğru alternatif: İzin ve kaynak şartları doğrulandıktan sonra, hâlihazırda devam eden ileri pilot için gerçek zamanlı `as-of` xG snapshot: (1) bitmiş maçın değeri ilk görüldüğünde UTC çekim zamanı, maç URL/id, kaynak/izin, verinin SHA'sı kaydedilir; (2) hedef maç kickoff zamanından **önce** sabitlenmiş snapshot dışında bilgi kullanılmaz; (3) yayın gecikmesi ve geriye dönük değişiklikler yeni snapshot'lar arasında denetlenir; (4) C3/M4 olasılıkları aynen korunur; xG kolu ayrı, önkayıtlı shadow araştırmadır; (5) yeterli bağımsız maç birikince tek toplu değerlendirme.
- **Public artifact riskini azaltma önceliği:** Önce ham veriyi izinli özel alanda koruma ve eski `understat-xg-pilot` artifact'inin erişimini/silinmesini değerlendirme; gelecekteki public Actions upload listesinden iki ham CSV'yi çıkar. Mevcut workflow ve artifact bu raporla otomatik değiştirilmedi; GitHub bağlantısında artifact silme aksiyonu mevcut değil.
- Ham xG ve özel maç satırları **bu yeni GitHub raporuna ya da script output'una aktarılmadı**. Yalnız agregalar gönderildi.

## Tek denetim kodu
`experiments/263/xg_vintage_gate_263.py`. `--archive`, `--cohort`, `--artifact-created-at`, `--out` argümanlarıyla çalışır. Çalıştırmada **2155 / 873 / 289**, 289 hedefin tamamının incelenen artifact'ten eski oluşu ve eksik dört provenance alanı doğrulandı. Sonuç `ASOF_NOT_CERTIFIED_FOR_STRICT_HISTORICAL_BACKTEST`. Model çalıştırılmaz.

**İlerleme kaydı:** Aşama 5 veri ve xG geçmiş-sürüm denetimi tamamlandı; as-of/izin kapısı açılmadı. Sıradaki proje işi: izinli snapshot toplama tasarımının kurulması ve eski public xG artifact riskinin giderilmesi; eski M4/C3 ve matematik testleri tekrarlanmayacak.
