# P1 — Lisanslı çok ligli kapanış piyasası örnek araştırması

**Tarih:** 21 Kasım 2026  
**Deney:** [GitHub Actions tek çalıştırma](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44944654777)  
**Veri sahibi / lisans:** [OddsIntel](https://github.com/msellin/oddsintel-football-closes-sample) — © 2026 Codename OÜ, CC BY-NC 4.0 (ticari olmayan araştırma, atıf).  
**Kaynak sabit commit:** `622bd876667ce1d1b6e831e25b3a2b4ed5e1f9fc`  
**Kaynak CSV SHA-256:** `51f0f66feb9e914f67fc94b783fe97d8a09c0df2e422bbee7191761d76600959`

## Karar
P1 bağımsız araştırmada kalır. Ana 2.6.3, M4/C3, aktif on lig ve SHA mühürleri değişmedi. P1 tarihsel araştırma girişinden on-lig zorunluluğu kaldırıldı. **P0, uygun son gün örneğinde hem kalibrasyonsuz hem sıcaklık kalibrasyonuyla az farkla daha iyi proper scoring gösterdi; fark anlamlı üstünlük iddiası için yeterli değil.**

## Veri kabul
- Kaynaktaki bitmiş maç: **4468**
- MS 1/X/2 + 2.5 Alt/Üst + KG Var/Yok, tam 7 fiyatlı: **3626**; **435 organizasyon**
- Eksik yedi oran gerekçesiyle dışlanan: **842**
- Gün: **2026-10-10–2026-10-22**, sadece **13 gün**
- Zaman sıralı öğrenme: **3091 maç** (19 Ekim öncesi); sonradan ayrılan test: **535 maç** (19–22 Ekim)

### Özellikle fiyatın ne olduğu
Kaynakta `close` adı verilen fiyatlar, **bir tek şirketin gerçek, marjlı bahis oranları değil**; en az üç bağımsız soft-book kaynağının **önceden marjı kaldırılmış uzlaşı fiyatlarıdır**. Bunu ters fiyat toplamı da doğruluyor: MS 1.000002, OU 1, KG 1.000001. Bu nedenle **iddaa ve tek-bahis-şirketi geçmiş fiyatları yerine kullanılamaz**. Kaynağın geçmişe ait kapanış sınıflaması ve gösterdiği zaman bilgisi bağımsız olarak üçüncü taraf noterli mühür seviyesinde doğrulanmadı.

## Test sonuçları (son 535 maç, düşük Brier/log-loss daha iyi)

| Model | Brier (3 pazar makro) | Log-loss | 7 olaydan ana tercih isabet |
| --- | ---: | ---: | ---: |
| P0 uzlaşı | 0.514211 | 0.772732 | 336/535 (62,80%) |
| P1 ters Poisson | 0.514637 | 0.773557 | 332/535 (62,06%) |
| P0 + öğrenilmiş sıcaklık | 0.513956 | 0.772367 | 335/535 (62,62%) |
| P1 + öğrenilmiş sıcaklık | 0.514449 | 0.773312 | 334/535 (62,43%) |

**Sadece ilk 3091 maçta öğrenilen sıcaklıklar:**

| Pazar | P0 | P1 |
| --- | ---: | ---: |
| MS | 1.075 | 1.025 |
| 2.5 | 0.975 | 0.975 |
| KG | 0.75 | 0.75 |

Test maçları kalibrasyon parametrelerini etkilemedi. Brier üç bağımsız bahis sonucu olarak yedi olay üstünden değil, birbirini dışlayan **üç ayrı pazar** üzerinden makro ortalamayla hesaplandı. Ana tercih isabeti olasılık kalitesiyle aynı şey değildir. Tek kaynak, 13 gün ve heterojen 435 organizasyon, bağımsız as-of doğrulaması veya ileri dönem mühürlü kör test değildir. Finansal getiri/pozitif EV hakkında çıkarım yapılmaz.

## Sonraki araştırma kapısı
**En yüksek öncelik:** gerçekten maçtan önce yayımlanmış, **aynı bahis şirketinden ham yedi fiyat**, açık lisans veya yazılı izin + sonuçlar, tercihen farklı tarihlerden yeterli örnek; lig ve sezon sınırı **YOK**. Kullanıcı iddaa PDF'leri ayrı ve kullanıcı kaynaklı kohortta kalır. Bu uzlaşı örneğinin sıcaklıklarını üretimde uygulama. Yalnız yeni doğrulanmış kohortta, tarih bloklarına göre ayrılmış sonuç ve olasılık güven aralıklarından sonra tekrar değerlendir.

**Ham OddsIntel CSV'si bu depoya kopyalanmadı**; sürüm/SHA referansı, test işlemi ve toplu sonuçlar mevcut. Bu rapor araştırma dokümanıdır, bahis tavsiyesi değildir.
