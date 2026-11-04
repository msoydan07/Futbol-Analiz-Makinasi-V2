# İlk dört model ↔ bahis piyasası karşılaştırması (4 Kasım 2026)

**Maç:** Gaziantep FK – Kasımpaşa, 6 Kasım 20.00 TSİ. 
**Önceden kilitlenmiş gerçek erken tahmin SHA:** `1038b6e9cd1f0bcbceb97367e261bc579b07a56e4e2dc5193c2f247e51e18ffb` (`forward_quad_shadow_263/2026-11-06/1d6b6f16fef8bac971c184c4.json`).
**Piyasa gözlemi:** <https://oddsfilter.com/event/1001584462-gaziantep-fk-kas-mpasa> sitesinin gösterdiği **Betano** sütunu. OddsFilter bağımsız piyasa toplayıcısıdır; Betano üzerinden canlı ticari fiyat doğrulaması yapılmadı. 1X2 panosundaki çekim zamanı **2 Kasım 2026 16:52 UTC**; 2,5 ve KG pazarlarının aynı anda güncellendiğine dair kanıt YOK. Bu nedenle bu rakamlar **güncel / T−60 / iddaa.com / Nesine / bahis yapılabilir / kaynakça bağımsız kabul edilen** oranlar değildir. Sayfada mevcut diğer firmalarla alışılmış oran karşılaştırması için kullanıldı; kullanıcı hesabı, bahis emri veya otomatik scraper yok.

## Tek bookmaker satırı üzerinden hesap (sağlayıcıları karıştırmadan)

| Pazar | Betano oranları (ikincil panodan) | Piyasa marjsız olasılığı | M4 olasılığı | M4 fark |
|---|---|---|---|---|
| MS1 | 2,50 | %37,36 | %32,16 | −5,20 yp |
| MSX | 3,30 | %28,30 | %26,88 | −1,43 yp |
| MS2 | 2,72 | %34,34 | %40,96 | +6,62 yp |
| 2,5 Alt | 1,95 | %49,48 | %54,43 | +4,95 yp |
| 2,5 Üst | 1,91 | %50,52 | %45,57 | −4,95 yp |
| KG Var | 1,67 | %55,94 | %50,62 | −5,31 yp |
| KG Yok | 2,12 | %44,06 | %49,38 | +5,31 yp |

1X2 overround %7,07, 2,5 Alt/Üst %3,64 ve KG %7,05. **Formül:** `p_no_vig(i)=(1/oran_i)/sum(1/oran_j)`, `indicative_EV=p_model*oran - 1`. Eski piyasa fiyatı üzerinden görünen M4 MS2 EV yaklaşık +%11,41, 2,5 Alt +%6,14. Bunlar **matematiksel senaryo**, gerçekleşecek kâr veya S2 önerisi değildir. Dört modelin tüm pazarları ve marjdan arındırılmış piyasa olasılıkları, rapor JSON'unda ayrı kaydedilir.

## Neden S2 çıkarmıyoruz?
1. Türkiye'deki ilk öncelikli oran kaynaklarımız olan **iddaa.com > Nesine > Bilyoner > Maçkolik** için bu maçın eşzamanlı tam karşı fiyatları doğrulanamadı.
2. Betano fiyatları bir üçüncü taraf sitesinden; KG/2,5 için fiyat çekim anları gösterilmedi ve T−60 fiyatı değil.
3. Model kaydı **erken shadow**, güncel skor kaynağı insan tarafından henüz nihai kabul görmedi, resmî 96 T−60 pilotuna dahil değil.
4. Dört modelin olasılık kalibrasyonu gerçekte kanıtlanmadı. Tek maçta yüzde puan avantajı ≠ bahis kârı.

**Sıradaki TEK kritik iş:** 6 Kasım günü maçın resmî TFF saatini tazele, gerçek kaynak sayfasından aynı anda bütün karşı oranları al ve gerçek T−60 onaylı kaynak zinciri varsa bunu pilot sistemine dahil et. Onay hâlâ yoksa şeffaf şekilde **UNVERIFIED** olarak bırak; bu erken piyasa karşılaştırmasını geriye dönük S2'ye yükseltme. Başka liglerde yeni model, yeni data toplama, veri batch yeniden testi açma.
