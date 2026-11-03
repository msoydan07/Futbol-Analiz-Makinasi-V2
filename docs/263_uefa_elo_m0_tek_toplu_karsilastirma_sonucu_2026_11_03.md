# Futbol Maç Analiz Makinası 2.6.3 — Avrupa Elo katkısı: tek toplu karşılaştırma SONUÇ

**Tarih:** 3 Kasım 2026  
**Sonuç:** **Elo, iki ayrı tarih bloklu retrospektif 1X2 karşılaştırmada M0 referansını iyileştirdi. Ancak gerçek maç önü veri yayımlanma kanıtı ve yeterli bağımsız dönem olmadığı için Elo→Poisson katsayısı üretime ONAYLANMADI.**  
**Ana model:** DEĞİŞMEDİ. **Pilot:** 0/100. **Dal:** experiment/263-toplu-karsilastirma.

## 1. Dondurulmuş ön kayıt ve tek test

- Başlamadan önce sabitlenen protokol: docs/263_uefa_elo_m0_ek_katki_tek_deney_onkayit_2026_11_03.md
- Tek GitHub Actions: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41586786116 — SUCCESS.
- Çalıştırılan yeni kod: experiments/263/europe/uefa_elo_m0_paired_retrospective_263.py
- Tek sonuç artifact: 263-elo-m0-paired-one-shot-retrospective, dosya retrospective_elo_vs_m0_report.json.
- Eski dört GitHub artifact indirilip SHA doğrulandı; kaynak yeniden taranmadı, önceki 132/124 ve 432 maç deneyleri tekrar çalıştırılmadı.
- beyondELO — https://beyondelo.com, CC BY 4.0.

**Örneklem:** 124/124 eşleştirilmiş maç, 47 farklı kulüp, iki takımın Elo geçmişi için maksimum 18 günlük son gözlem aralığı. Eğitim Eylül–Kasım 2025: 76 maç, 17 maç günü. Doğrulama Aralık 2025: 16 maç, 3 maç günü. Son tarih bloğu Ocak 2026: 32 maç, 5 maç günü. Aynı gün ve sonrasında güncellenen rating kullanılmadı.

**Kaynak sınırı:** UEFA maç sayfaları kaynaklı 132 link adayı önceki CI tarafından her biri ayrı doğrulanmamıştı; yerel gol geçmişi ve Elo geriye dönük arşivde bulunuyor ama o anda ilk yayımlandığı/ilk görüldüğü saat kanıtlanmadı. Kaynakların REVIEW_ONLY, model_training_permitted=false bayrakları kaldırılmadı. Burada bulunan beta kalıcı model katsayısı değil, sadece karantinadaki metodolojik hassasiyet denemesidir.

## 2. Matematik: iki kol

- **M0:** kendi ligine göre bağıl ev/deplasman gol hücum-savunma güçleri; rol bazında sabit k=5 yumuşatma. Ortak UEFA ev/dep baz oranları sadece ilk 76 eğitim maçından: ev 1,776316 ve dep 1,328947 gol/maç. Beklenen goller 0,15–5,00 aralığına kırpıldı. Bu, **mevcut C2 üretim motoru değildir**; xG'siz Avrupa için önceden tanımlı naif kontrol referansıdır.
- **M0 + Elo:** aynı λ değerlerine ayrıca sadece iki kulübün uluslararası rating farkı eklendi; ΔElo/400 üzerinden simetrik exp(±βd). Ayrı UEFA ülke/lig bonusu veya yerel Elo katılmadı. Tarihi aynı gün veya sonrasına ait skorlar alınmadı.
- Sadece 76 eğitim örneğinde sabit ridge=20 ile bulunan retrospektif **β=0,525476**. Doğrulama ve son dönem skorlarına bakılarak katsayı/eşik değiştirilmedi.

## 3. Gerçek ölçülmüş sonuçlar

Düşük tüm değerlerde iyidir. Δ = (M0+Elo) − M0; negatif iyileşme, pozitif kötüleşmedir.

| Ölçüt | Aralık M0 | Aralık M0+Elo | Ocak M0 | Ocak M0+Elo |
|---|---:|---:|---:|---:|
| **1X2 log-loss** | 1,16403 | **1,04599** | 1,03682 | **0,97606** |
| **1X2 Brier** | 0,70832 | **0,64043** | 0,62970 | **0,58596** |
| Toplam bağımsız gol Poisson log-loss | 3,08189 | **3,02494** | 3,13828 | **3,06570** |
| **2,5 Üst Brier** | **0,24089** | 0,24277 | **0,23184** | 0,23554 |
| **KG Brier** | **0,24631** | 0,24943 | **0,27672** | 0,27754 |

- **Aralık 16 maç:** 1X2 log-loss farkı **−0,11804** (Elo lehine).
- **Ocak 32 maç:** 1X2 log-loss farkı **−0,06076** (Elo lehine).
- **Ocak Şampiyonlar Ligi, 23 maç:** M0 1,04003; Elo 1,00146 (−0,03857).
- **Ocak Avrupa Ligi, 9 maç:** M0 1,02862; Elo 0,91115 (−0,11747). Yalnızca 9 maç — genelleme yapılamaz.
- KG ve 2,5 Üst Brier değerleri **her iki dönemde de az da olsa kötüleşti**. Tüm pazarlarda otomatik Elo avantajı iddiası yanlış olur.

### İstatistiksel belirsizlik

Gün bazında deterministik 2.000 bootstrap:
- Aralık 1X2 log-loss farkı yaklaşık %95 aralık: **[−0,29387, −0,02275]**, yalnız 3 maç günü.
- Ocak aynı fark: **[−0,12604, +0,02491]**, yalnız 5 maç günü. **Sıfırı kapsıyor.**
- Bu bloklar **yeni, bağımsız bir futbol sezonu değil**; tarihsel ilk yayımlanma kanıtı da yok. %95 aralıkları gerçek ileri dönem tahmin başarısı belgesi değildir.

## 4. Nihai mühendislik kararı

**1. KABUL EDİLEN BULGU:** Bu dondurulmuş tarihsel örneklemde, ayrıca ikinci lig gücü katsayısı kullanmadan, uluslararası Elo farkının 1X2 ve tam gol dağılımı metriklerinde kayda değer *araştırmaya değer işaret* sağladığı görüldü. Elo referansının açıklayıcı rapor alanında tutulması mantıklı.

**2. KABUL EDİLMEYEN:** Retrospektif β=0,525476'yi Avrupa λ'sına gerçek kullanıcı maçında otomatik ekleme, Elo+lig katsayısını birlikte kullanma, KG/2,5 pazarlarına otomatik olumlu etkisi olduğunu iddia etme, aynı örnekleme ikinci kez katsayı uydurma veya onaylanmış 1X2 yüzdeleri üretme.

**3. GEREKLİ SONRAKİ KANIT:** Bundan sonraki gerçek uygun UEFA maçları için fikstür ve Elo/kadro/gol verisini *başlamadan önce* kaynak SHA + UTC first_seen ile kilitleyip sonuçtan sonra değişmez snapshot üzerinden Elo'suz/Elo'lu *gölge* karşılaştırma yapılması. Bu yalnız kullanıcı istediğinde başlatılacak; 100 maç pilot ve kupon değildir. Yeterli ayrı tarih ve sezon sayısı oluşmadan üretim terfisi yok.

**4. KORUNAN:** 9 üst ligin 167 Avrupa Elo adayı; Championship ve Erzurumspor Avrupa Elo dışında; mevcut yerel 10 lig altyapısı ve eski UEFA kapsam kapısı değişmedi. xG/xGA/H2H yasakları, main, Model B/C2/C3/M4, oran/EV ve pilot kayıtları korundu.

**Tek test / tek rapor kuralı tamamlandı.** Yeniden sonuç görüp parametre ayarlamak veya geçmiş deneyi tekrar çalıştırmak planlanmıyor.
