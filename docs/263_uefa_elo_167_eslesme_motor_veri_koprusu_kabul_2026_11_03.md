# FUTBOL MAÇ ANALİZ MAKİNASI 2.6.3 — AVRUPA ELO KİMLİK KÖPRÜSÜ TEK KABUL RAPORU

**Tarih:** 3 Kasım 2026  
**Dal:** \`experiment/263-toplu-karsilastirma\`  
**Durum:** **167/167 kanonik kulüp ↔ beyondELO kaynak adı/slug eşleştirmesi ve Avrupa tek maç girişine veri bağlantısı TEST EDİLEREK KABUL EDİLDİ.**  
**Sınır:** Sadece açıklayıcı Elo girdisi; matematiksel tahmin doğruluğu, geleceğe dönük kalibrasyon, Poisson lambda değişimi veya pilot kabulü **YOK**.

## 1. Kanıt ve tek deneme

- GitHub Actions: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41585362134
- Sonuç: **SUCCESS, 37/37 test**. Eski kapsam ve resmî fikstür testleri de aynı planlı koşuda çalıştırıldı.
- Yeni workflow: \`.github/workflows/263-europe-elo-bridge-single-acceptance.yml\`
- Veri kanıtı: \`263-uefa-elo-167-bridge-single-acceptance\` artifact, kimlik listesi \`elo_bridge_crosswalk_167.json\`.
- Veri sağlayıcısı: beyondELO, https://beyondelo.com/developers, **CC BY 4.0**. Bu test sırasında sağlayıcıdan yeniden veri çekilmedi: daha önce tek seferde arşivlenmiş \`41582947375\` koşusundaki snapshot tekrar kullanıldı.
- Arşivlenen ve testte sabitlenen \`club-ratings.csv\` SHA-256: \`073a461d810396af6ae74216e8d400d5c5d27a654a153014d36dc4a4c7ee8be5\`; \`as_of\`: 2026-11-03.
- İşlevsel kapı testleri: resmî UEFA fikstürü öncesinde Elo sorgusu yapılmaz; tarih/fikstür doğrulanamazsa Elo getirilmez; maç başladıysa eski veriden yeni maç tahmini üretilmez; bozuk/farklı provider adı, mükerrer slug, yaşlı rating ve gelecek tarihli snapshot reddedilir.

## 2. Kapsam ve kimlik uzlaştırma

Kullanıcının açık kapsam kararı ile Championship'in 24 takımının tamamı ve Erzurumspor FK sadece **Avrupa Elo aday çalışma listesinden** çıkarıldı. Kalan **167 kulüp / 9 üst lig**:

| Lig | Kulüp |
|---|---:|
| BEL1 | 18 |
| ENG1 | 20 |
| ESP1 | 20 |
| FRA1 | 18 |
| GER1 | 18 |
| ITA1 | 20 |
| NED1 | 18 |
| POR1 | 18 |
| TUR1 | 17 |
| **Toplam** | **167** |

167 eşleşme içinde **134** kulüp resmî dizindeki mevcut, normalize edilmiş isim/alias üzerinden tekil eşleşti; **33** kulüp için resmî lig takım adı ve kaynakta beklenen slug, ad, ülke kodunu açıkça sabitleyen incelemeli eşleştirme kullanıldı.

Dosyalar:
- \`experiments/263/evidence/elo_uefa_active_cohort_2026_11_03.json\` (aktif 167 takım kimliği ve 25 hariç tutulan takım).
- \`experiments/263/evidence/elo_33_alias_name_review_2026_11_03.json\` (33 kaynak ad eşleştirmesi, resmî lig adı ve URL kanıtı).
- \`experiments/263/europe/uefa_elo_reference_263.py\` (kaynak bütünlüğü, eşleştirme, tarihe/kimliğe göre reddetme, veri farkı).
- \`experiments/263/europe/uefa_requested_match_entry_263.py\` (resmî fikstür onayından **sonra** çağrılan isteğe bağlı açıklayıcı veri katmanı; CLI'da açık).
- \`experiments/263/europe/test_uefa_elo_reference_263.py\` (yeni deterministik testler).

**Kimlik sınırı:** beyondELO ücretsiz CSV'si birleşik UEFA kulüp kimlik numarası içermez; bu alanın API erişimi anahtar gerektirir. Dolayısıyla 167/167 sonucu **isim + lig + ülke + tekil slug temelli ve koşullu kimlik eşleştirme** başarısıdır, bağımsız provider/UEFA ID doğrulaması değildir. Bu sınır model eğitimi/prod kabulu önünde açıkça tutulur.

## 3. Makineye veri bağlantısı ve doğru sınır

Var olan \`requested_europe_match\` akışında:

1. Kullanıcının belirttiği UEFA CL / EL eşleşmesi için mevcut **10 lig kapsam kapısı** çalışır.
2. UEFA'nın resmî fikstürü ve yedi günlük pencere doğrulanır.
3. Yalnız uygun iki takım, yeni **167 kulüplük Elo çalışma kapsamı** içerisindeyse sağlayıcı CSV'si kaynaklı olarak incelenir.
4. Birinin Elo değeri yoksa, tarihi bayatsa, kaynaktaki isim/slug değişmişse veya kimlik çakışıyorsa **bilgi reddedilir**, sayı uydurulmaz.
5. İki taraf için güvenli kaynak bulunursa yalnızca **Elo / RD / tarih / kaynak SHA / gol matematiği için onaysız fark** açıklayıcı alanda gösterilir.

Alan durumu \`ELO_DESCRIPTIVE_REFERENCE_ATTACHED_NOT_MODEL_CALIBRATED\`.

**ŞİMDİLİK ÇALIŞMAYAN:** Elo'ya kaç gol çarpanı verileceği, bu çarpanın ligler arası farkla çifte sayılmaması, tarihsel maç öncesi as-of ve tahmin kalibrasyonu. Bunlar bağımsız kanıt olmadan mevcut Poisson modeline bağlanmadı. Görüntülenen Elo farkı kazanma yüzdesi değildir.

## 4. Güvenli mühendislik kararı ve sonraki tek safha

**Kabul edildi:** kaynak ad/slug ↔ resmî kanonik kulüp kimliği **167/167**, tekil/mükerrer/uygun ülke/snapshot denetimi ve Avrupa doğrulanmış maç girişiyle veri katmanı bağlantısı.

**Henüz kabul edilmedi:** bağımsız UEFA sağlayıcı ID eşleştirmesi; Elo → gol lambda dönüşümü; 1X2/kazanma olasılıklarını değiştiren Elo etkisi; gerçek sonuçlara göre Elo katsayısı kalibrasyonu; pilot ve üretim \`main\` entegrasyonu.

**Sıradaki matematik işi:** Eski M1/M2/C2/M4 sonuçları tekrar çalıştırılmadan, sadece kullanılabilir ve maç öncesine güvenli tarihli kayıtlar ile **Elo destekli ve Elo'suz mevcut gol modeli karşılaştırmasının planını**, sızıntı/çifte sayım kontrolüyle tek seferde oluşturup gerekirse kanıtlayıcı tek toplu deney yapmak.

**Korunanlar:** 10 yerel lig altyapısı, xG/H2H kuralları, \`main\` dalı, 0/100 pilot, model B/C2/C3/M4 ve mevcut kapsam kapısı.

— Bu belge, yeni bir tahmin başarısı veya canlı bahis onayı iddiası değildir.
