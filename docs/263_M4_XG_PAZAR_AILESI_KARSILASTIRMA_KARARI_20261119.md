# 2.6.3 — M4 ile M4+xG: pazar ailesine göre seçim kararı (araştırma)

**Tarih:** 19 Kasım 2026 • **Kapsam:** 2026/27 sezonu 10 ligde aynı 1.083 maç (7 Ağustos–8 Kasım) • **Durum:** Araştırma; mevcut M4, ana mühürler ve otomasyonlar değiştirilmedi.

## Asıl soru: Bir model MS'de, diğeri gol ve KG'de üstünse?

**Tek kazanan model zorunlu değil.** Modelin üstünlüğü karşılaştırılan aynı maçlar üzerinde, aynı zaman kesiti ve aynı olasılık hata ölçüsüyle, **pazar ailesi bazında** kanıtlanmışsa ayrı model seçilir:

| Pazar ailesi | Varsayımsal sonuç | Karar | İç tutarlılık şartı |
|---|---|---|---|
| MS (1 / X / 2) | M4 üstün | MS'nin **üç olasılığı** M4'ten | Sadece MS1'e bakıp 1/X/2'yi farklı kaynaklardan toplama; toplam 100% olmalı |
| 2.5 Alt / Üst | M4+xG üstün | **Her iki olasılık** M4+xG'den | Alt + Üst = 100% |
| KG Var / Yok | M4+xG üstün | **Her iki olasılık** M4+xG'den | Var + Yok = 100% |

Bu **varsayımsal** senaryo; gerçek sonuç aşağıdadır. Her ailenin sabit modeli, o gün hangi model daha yüksek yüzde verdi diye değil, tarih sıralı karşılaştırma ve kalibrasyon kanıtıyla belirlenir. Piyasa oranları (MARKET) **beşinci referanstır**; model seçimi, ana/alternatif/PAS ve mühür üzerinde etkisi yoktur. Fark önemsizse temel M4 korunur, xG verisi eksikse açıkça M4'e dönülür. 1.5/3.5 çizgileri bu tabloda test edilmedi ve 2.5 sonucuyla otomatik devredilmez.

Birden fazla aileden sonuç gösterilirse bunlar **farklı modellerin marjinal tahminleridir**; sanki tek bir tutarlı ortak gol dağılımıymış gibi sunulamaz. Aileler arası olası matematiksel çelişkiler ayrıca kontrol edilir. Tek maçta ana/alternatif tercih için tahmin güvenilirliği ve lig baz oranı kullanılır; sırf daha yüksek yüzde diye daha kolay 1.5 Üst seçilmez.

## Gerçek eski testin tekrar hesaplanan sonucu

Kaynak: `263_M4_TUTARLI_KALIBRASYON_MAC_MAC_20261119.csv`; dosya SHA256 `466dff472fc3bbac753033747f2667c077d127235ea55c265666e647b3028305`. Önceki `263_M4_XG_ELO_KAPSAMLI_MUHENDISLIK_KARARI_20261119.md` raporunun **zaten yaptığı** testi aynı maçlarda yeniden saydık. Toplam 1.083 çift tahmin, 69 ayrı gün; model katsayılarını yeniden eğitmedik. Brier düşükse daha doğru olasılık demektir.

**Ortak gol dağılımı kalibrasyonlu koşul (aynı kalibrasyon yaklaşımı, M4 vs M4+xG):**

| Pazar | M4 Brier | M4+xG Brier | Sonuç | Gün-kümesi %95 fark aralığı (xG − M4) |
|---|---:|---:|---|---|
| MS (1-X-2; bütün aile) | 0,197318 | 0,196632 | xG sayısal olarak biraz iyi, **kanıt kesin değil** | −0,001580 … +0,000341 |
| MS1 (tek sonuç için ikili tanı) | 0,220525 | 0,219740 | **fark kesin değil**; MS ailesini tek başına değiştirmez | −0,002292 … +0,000951 |
| 2.5 Alt/Üst | 0,242678 | 0,240067 | **xG lehine araştırma sinyali** | −0,004693 … −0,000656 |
| KG Var/Yok | 0,243176 | 0,242951 | **fark kesin değil** | −0,001682 … +0,001304 |

**Kalibrasyonsuz M4 ↔ M4+xG tekrar kontrolü:** MS 0,195593 ↔ 0,195645 (temel M4 az farkla iyi); 2.5 Alt/Üst 0,247734 ↔ 0,241070 (xG iyi); KG 0,245417 ↔ 0,243330 (xG sayısal iyi ama %95 günlük aralık sıfıra değiyor). Kalibrasyonlu ve kalibrasyonsuz karşılaştırmalar karıştırılarak sahte bir üstünlük ilan edilmedi.

**Zaman ayrımı:** Ağustos–Eylül 587 maç, Ekim–8 Kasım 496 maç. İki dönemde de 2.5 ailesi için xG Brier daha düşük. KG için kalibre xG Ağustos–Eylül'de temel M4'ten biraz kötü, Ekim–Kasım'da biraz iyi; bu nedenle KG otomatik geçişi için kanıt yetersiz. MS ailesi de açık kazanan vermedi.

### Bugün uygulanacak güvenli aile kararı

- **MS 1-X-2:** Mevcut M4 **korunur**; xG modeli ancak bütün MS ailesinde ve güvenilir sonraki tarihlerde üstünlük kanıtlandığında aday olur.
- **2.5 Alt/Üst:** M4+xG **araştırma favorisi**; fiyat bağımsızdır. Resmî/önceden yayımlanmış xG sürümü ve maç sabahı kaynak bütünlüğü henüz çözülmediğinden **canlı karar modülüne otomatik aktarılmaz**.
- **KG Var/Yok:** Mevcut M4 **korunur**; KG xG üstünlüğü henüz güvenilir değil. İleride B/C2/C3 gibi diğer adaylarla da aynı test yapılabilir.

Bu politika **yalnız M4 ↔ M4+xG** karşılaştırmasıdır; 242 maçlık önceki 4-model deneyinde KG için C3'ün düşük Brier verdiği ayrıca gözlenmiş, ancak C3 terfisi de bağımsız kanıt almamıştır.

## Son dürüst sınırlar

1. 1.083 maçlık 2026/27 dilimi birçok kez incelenmiş geçmiş dönemdir; **yeni kör ileri tahmin sınavı değildir**. %95 aralıkları geçmiş verideki rastlantısal belirsizliğe ilişkin olup tekrar kullanım yanlılığını ortadan kaldırmaz.
2. Kullanıcının xGEdge üzerinden elle doldurduğu geçmiş değerlerin **tahmin tarihinden önce hangi sürümde yayımlandığı** her maçta ispatlanmış değildir; tarihe göre yalnız geçmiş maçın xG'sini kullanma kuralına uymak, bu yayımlanma sorununu tek başına çözmez.
3. **M4'ün gerçek üretim kodu hâlâ xG kullanmıyor.** 4.618 maçlık kaynak, 1.083 eşleşmiş değerlendirme, yeni ortak matematik ve eski mühürler ayrı şeylerdir. Bu rapor bir araştırma kararıdır, sessiz üretim terfisi değildir.
4. Eski rapordaki `no_verified_quote => EV PAS` kuralı **artık yürürlükteki D-MARKET-006 ile çelişir**. Bu çalışmada yeni kilitli kural uygulanır: oran yalnız beşinci referans, ana/alternatif/PAS model ve veri kalitesinden belirlenir.

**Kaynak araştırma dosyası:** `263_M4_XG_AILE_BAZLI_TEST_20261119.json` • **Denetim kodu:** `m4_xg_aile_bazli_karsilastirma_20261119.py`. Özel maç bazlı xG verileri GitHub'a yüklenmemeli.