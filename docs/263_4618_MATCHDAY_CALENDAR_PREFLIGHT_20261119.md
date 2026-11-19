# 2.6.3 — 4.618 özel skor verisi ve takvime duyarlı güncellik kapısı

**Denetim tarihi:** 19 Kasım 2026.  
**Durum:** **YEREL KOD VE TEST TAMAMLANDI — CANLI MAÇ ÖNÜ BAĞI HENÜZ ONAYLANMADI**.  
**Kilitli kararlar:** [Karar Defteri](263_KARAR_DEFTERI_TEK_GECERLI_KAYNAK.md), D-ODDS-001 (iki PDF / tek sabah mührü), D-MARKET-006 (oran beşinci referans; tercihi yönetmez).

## Bir kez yapılan iş (eski pilot ve M4'e müdahale yok)

- `experiments/263/private_4618_matchday_preflight_263.py`: Sabit SHA ile 4.413 eski skoru ve özel 4.618 maçlık **yalnız skor** projeksiyonunu doğrular. Eski satırları birebir korur, 205 ek satırın skor/result/lig/sezon/teklik/bütünlük sözleşmesini denetler. xG sütunlu dosyayı kabul etmez.
- Güncellik kapısı sabit `MAX_DATA_AGE_DAYS=10` varsayımı yerine **son arşiv maçı sonrası, hedef maç tarihinden önceki tam günlerin** resmî tamamlanmış maç takvimini sorgulayan adapter sözleşmesi ister.
- Adapter, her ligin tam pencere kapsamını, gözlem tarihini, resmî alan adını, tamamlanmış/ertelenmiş/iptal edilmiş maçları bildirir. **Tek bir oynanmış ama arşivde olmayan maç** görünürse kod `BLOCKED_NEW_COMPLETED_MATCH_MISSING` döndürür. Eşleşen resmî URL, tek başına internette bağımsız doğrulama sayılmaz.
- Millî maç arası yüzünden arada tam maç yoksa `RESEARCH_GAP_CANDIDATE...` çıkar, **ama** `production_forecast_allowed=False`, `calendar_verified_by_code=False` sabit kalır. Gerçek kaynağı sorgulayan adapter henüz yazılmadı.
- Repo içindeki `forward_quad.py` / `forward_c3.py` eski 10-gün kaynağı, M4 kilidi, mevcut mühürler ve GitHub sabah workflow'u **değişmedi**. Bu yeni kod kendi kendine modele veya üretime bağlanmış sayılmaz.
- Özel 4.618 CSV ve xG verileri GitHub'a **yüklenmedi**. Çalıştırma sırasında yerel dosya gerekir.

## Test kanıtı ve kalite sınırları

- Yerel Python 3 standart kitaplıkla `python -m unittest -v test_private_4618_matchday_preflight_263.py`: **15/15 sentetik senaryo geçti**. Kontroller arasında eski 4.413'ün değişmesi, aynı maçın iki kez yazılması, xG sızıntısı, skor-sonuç tutarsızlığı, resmî adaptör eksikliği, takvim boşluğu, geç eklenmiş tam maç, eksik pencere, yanlış kaynak hostu, eski gözlem, ileri tarih, yarım kapsama ve tekrar kayıt var.
- Gerçek **özel dosyalarla**, SHA/4.413 eski + 205 yeni = 4.618 bütünlük kontrolü **geçti**. Gerçek resmî sonuçları çekmeyen modda `OFFICIAL_RESULTS_ADAPTER_NOT_PROVIDED` beklendiği gibi **engelledi**.
- Araştırma CI: `.github/workflows/263-private-4618-matchday-preflight-ci.yml`. **Yerel test başarısı, GitHub CI run'ının geçildiğini kanıtlamaz.**
- 19 Kasım itibarıyla 10 gün kuralının neden sorun olduğunu açıklayan **dış kaynak**: Premier League'in 8 Kasım sonrası 21 Kasım'da devam ettiği resmî takvim: https://www.premierleague.com/en/news/4689113/when-are-the-international-breaks-for-202627 ; EFL resmî 2026/27 uluslararası pencere: https://www.efl.com/supporters/faqs/fixtures/ . Bu, **diğer 8 ligin** canlı tamamlanmış maç listesi yerine geçmez.

## Açık kapılar (sıradaki somut mühendislik işi)

1. Mevcut resmî lig fikstür adaptörlerinden **oynanmış sonuçları eksiksiz zaman aralığıyla** çıkaran, kaynağın HTML/JSON satırlarını kendi başına indiren doğrulayıcı eklemek. EFL TV sayfası yalnız seçili maçları verir; tam Championship kapsamı diye kullanılamaz.
2. İlgili ligde yeni oynanmış maç varsa kullanıcının dondurduğu 4.618 kaydına dokunmadan **yeni append-only tarihsel sonuç sürümü** oluşturarak kaynağı güncellemek. Var olan xG yoksa maç sonucunu yanlışlıkla xG var diye etiketlememek.
3. Korunan sabit M4 matematiği / ilk PDF iş akışı için yeni kaynak kabul SHA'sını, iş akışı tetikleyicisini ve takvim kapısını **araştırma dalında entegre edip** gerçek kapsam ligi sabah PDF'siyle uçtan uca kabulü göstermek. Piyasayı ana/alternatif/PAS tercihi kapısı yapmak **yasak**.
4. Testten bağımsız gerçek resmî adaptör kabulü olmadan 20 Kasım maçlarına “sorunsuz hazır” dememek.

**Çıktı kapsamı:** Veri bütünlüğü kapısı, takvim sözleşmesi, testler, CI dosyası ve bu araştırma raporu. **Çıktıda üretilmiş gerçek maç tahmini, canlı kaynak kabulü, oran değişikliği veya ikinci mühür yoktur.**

## Sayısal durum — 19 Kasım 2026

Özel 4.618 skor projeksiyonunun en son 10 lig tarihinden bugüne gün sayısı:

| Lig | Arşiv son maçı | Gün farkı | Mevcut kör 10 gün kuralı |
|---|---|---:|---|
| BEL1 | 8 Kasım | 11 | BLOKE |
| ENG1 | 8 Kasım | 11 | BLOKE |
| ENG2 | 7 Kasım | 12 | BLOKE |
| ESP1 | 8 Kasım | 11 | BLOKE |
| FRA1 | 8 Kasım | 11 | BLOKE |
| GER1 | 8 Kasım | 11 | BLOKE |
| ITA1 | 8 Kasım | 11 | BLOKE |
| NED1 | 8 Kasım | 11 | BLOKE |
| POR1 | 8 Kasım | 11 | BLOKE |
| TUR1 | 8 Kasım | 11 | BLOKE |

Bu **10/10 teknik risk** anlamına gelir; 10 ligin tümünde gerçekten eksik maç var anlamına **gelmez**. Tam resmî sonuç penceresi olmadan takvim boşluğu kanıtı ilan edilmez.

**Güvenlik ayrımı:** Model değeri açısından `PAS` ile `OFFICIAL_RESULTS_ADAPTER_NOT_PROVIDED` / `BLOCKED_NEW_COMPLETED_MATCH_MISSING` gibi teknik veri blokları ayrı gösterilecek; kararlaştırılan ilk PDF seçiminde oranı yöneten EV kapısı **eklenmeyecek**.
