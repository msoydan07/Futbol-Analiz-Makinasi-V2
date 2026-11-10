# 2.6.3 — Rakip gücü × KG Var × 2.5 Üst matematik kontrolü
**Tarih:** 10 Kasım 2026. **Özgün M4, dev kilidi ve SHA mühürleri değiştirilmedi.**

## Sonuç — mevcut M4 matematiği doğru, yeni katsayı entegrasyonu yok

M4 zaten dört ayrı rakip bileşeni dikkate alır:
- Ev sahibinin gol beklentisinde rakibin ortak **savunma** ve **deplasman savunma** katkısı;
- Deplasmanın gol beklentisinde rakibin ortak **hücum** ve **deplasman hücum** katkısı;
- Hem ev sahibinin kendi ev hücum/savunma terimleri hem de iki lig intercepti ayrıca vardır.
- Modelin Poisson varsayımı altında `KG Var = (1 − exp(−λ_ev)) × (1 − exp(−λ_dep))`.
- `2.5 Üst = 1 − exp(−(λ_ev+λ_dep)) × (1 + λ_ev + λ_dep + (λ_ev+λ_dep)²/2)`.
- İki pazar **beklenen gol çiftinden** üretildiği için KG/Üst'ün kendine özgü rakip-taktik-kovaryans parametresi **yoktur**.

Bu hesapların doğru olduğuna ilişkin *matematik kimliği* karşılaştırması yapıldı; yeni bir gerçek maçın doğruluk artışı / üstün model ispatı değildir. Önceden bitirilmiş **984 maçlık Dixon–Coles/bivariate retrospektif araştırma tekrarlanmadı.**

## 4.617 kabul edilmiş sonuç arşivinden 10 ligde model-diagnostik karşılaştırma

Her ligde **aynı ev sahibi** tutuldu. Karşısına minimum 8 deplasman kaydı olan, M4'ün kendi `deplasman savunması` katsayısına göre daha dirençli ile daha az dirençli olan iki rakip kondu. Bu iki rakip maçları **gerçek fikstür değildir** ve karşılaştırma **tahmin önerisi değildir**. Çıktılar yalnız sabit M4'te olası parametre duyarlılığını tarif eder.

| Lig | Ev gol beklentisindeki değişim (gol) | KG Var farkı (yüzde puan) | 2.5 Üst farkı (yüzde puan) | 99 yeni skorun payı |
|---|---:|---:|---:|---:|
| ENG1 | +1,110 | +13,14 | +16,95 | 10 |
| ENG2 | +0,906 | +13,18 | +7,09 | 15 |
| GER1 | +1,413 | +17,49 | +25,04 | 9 |
| ESP1 | +0,669 | +3,01 | −5,98 | 10 |
| ITA1 | +1,049 | +2,22 | +4,17 | 10 |
| FRA1 | +0,830 | +7,28 | −9,14 | 9 |
| NED1 | +1,540 | −8,74 | +12,20 | 9 |
| TUR1 | +1,195 | −21,07 | +2,88 | 9 |
| POR1 | +1,213 | +3,13 | +10,72 | 8 |
| BEL1 | +1,271 | +4,48 | +14,72 | 10 |

*Önemli:* Takımları lig tablosundaki gücüne göre değil, M4'ün mevcut **deplasman savunma terimine göre** karşılaştırıyoruz. Dolayısıyla rakibi değiştirince **hem savunma hem hücum** yeteneği değişiyor. Bu yüzden KG ve 2.5 Üst farklı yönlere gidebiliyor. Bu rakamlar M4'ün mevcut eğitim örneklerindeki duyarlılıklarıdır, bahis değeri / model üstünlüğü / maç olasılıkları değillerdir.

## Test / kanıt
- [Gerçek 4.617 veri ve on ligde M4 maç-önü tarih kesiti + rakip dekompozisyonu + KG/Üst analitik formül testi: **5/5 SUCCESS**](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42901011806)
- [Tekrar üretilebilir, sonuç değiştirmeyen kod](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-opponent-goal-market-diagnostic-20261110/research/opponent_goals/m4_opponent_market_4617_readonly.py).
- Gerçek tarih ve kaynak SHA kontrolleri: 4.518 özgün `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`; 4.617 yeni `637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89`; M4 motor SHA `eac755e54086738f40d7f30a514b2c9bb789b2c428ffef4ee70bb2fd2b49bc45`. Değiştirilmedi.

## Mühendislik kararı ve tek sonraki iş

1. **Rakip etkisi eksik diye yeni rakip gücü çarpanı ekleme.** M4 rakip kimliği ve deplasman/ev etkisini zaten ayrı modeller. Hesaplanacak yeni bir parametre ancak ayrı ve gerçekte bilgi taşıyan olay veri kanıtı varsa (ör. kullanım hakkı uygun pres/game-state) geliştirilebilir.
2. **KG/2.5 Üst'e sabit ek/eksi yüzde veya 'rakip zayıf = KG daha yüksek' kuralı uygulanmasın.** Duyarlılık sonuca ters etki edebilir; aynı hatayla iki pazar birden bozulur.
3. Yeni tamamlanmış **farklı tarihli gerçek SHA-mühürlü maçlar** geldikçe önceden belirlenmiş KG/2.5 Üst kalibrasyon ve Brier karşılaştırması yapılmalı. Sadece bu yeni kanıtla eski M4 bağımsız Poisson yeterli mi, ortak skor/tempo etkisi için *kanıtlı* alternatif gerekiyor mu karar verilmeli. Eski 984 / 46 pilotlar yeniden analiz edilmesin.
4. Bugünkü araştırma dalındaki bu test üretim değişikliği değildir; ana `main`, aktif deney `experiment/263-toplu-karsilastirma`, LITE ve eski SHA sonuçlarının hepsi korunur.
