# Futbol Analiz Makinası 2.6.3 — Rakip Savunma Ağırlığı Toplu Matematik Araştırması

**11 Kasım 2026 | On lig | Araştırma dalı, üretim değişikliği yok.**

## Tek cümlelik mühendislik kararı

**M4'ün rakip savunmasını fazla sert uygulama ihtimali desteklendi, ancak henüz bağımsız yeni maçta kanıtlanmadı.** İki taraflı savunma etkisini %80'e indiren **yalnız araştırma adayı**, on lig ortalamasında KG Var ve 2.5 Üst için en iyi sayısal sonucu verdi. **Ana M4, kullanıcı yüzdeleri, mevcut market/pick kararı, tüm eski mühürler ve 99 tamamlanmış maç arşivi korunur.**

## Deneyin matematiği

Dondurulmuş M4'ün home λ log-katkısı: ev takımının kendi hücumu + **rakip deplasman ortak savunması + rakip deplasman savunma sapması** ve diğer ev avantajı/başlangıç terimleri. Away λ'da ev sahibinin ortak savunması + evdeki savunma sapması bulunur.

Deneyde dört yeni ağırlık yöntemini **M4'ün orijinal fit edilmiş katsayılarının üstüne yalnız hesaplama sırasında** uyguladık; asıl öğrenme ve katsayılar değiştirilmedi:
- Deplasman savunmasının ev sahibinin golüne etkisini **%90** veya **%80** bırakma; deplasmanın beklenen golünü olduğu gibi tutma.
- Her iki takımın rakip savunma etkisini simetrik **%90** veya **%80** bırakma.

Örneğin deplasman rakibinin ev golündeki log-savunma toplamı `D_away` ise yeni ev golü: `lambda_home_shadow = lambda_home_M4 * exp((w-1) * D_away)`. Simetrik versiyon, ev savunmasının deplasman golündeki etkisine aynı çarpanı uygular. Girdi aralığı dışında çıkan maç ortak örneklemden çıkarılacaktı; bu testte **çıkarılan 0 maç**.

## Veri ve kabul sınırı

- SHA ile kontrol edilen sonuç havuzu **4.617**, orijinal dosya **4.518**, tek normal süresi tamamlanmayan maç tahmin eğitimi dışı. Orijinal 99 sonucun kontrolü yeniden açılmadı.
- Tam **702 aynı maç**, 10 lig × 2025/26 sezonunda önceden kilitlenmiş üç tarih kesiti = 30 fit; **41 maç günü**. Her fold M4'ü sadece önceki tarihli bitmiş sonuçlarla eğitti.
- Sonraki sezon **2026/27 sonuçları sıfır**, geçmiş 6–8 Kasım SHA pilotları **sıfır**. Bunların hiçbiri tekrar tahmin edilmedi.
- Dikkat: Bu tarihler M4'ün orijinal geliştirme sezonudur. Daha önce burada görülen savunma yanlılığından yola çıkıldığı için **deney keşifseldir, yeni bağımsız isabet kanıtı değildir**. Gün bloklu aralıklar bu seçilim sorununu düzeltmez.

## Beş seçenek — 702 aynı maçtaki Brier hata farkları

**Aday − mevcut M4; negatif daha iyi.**

| Seçenek | KG Var Δ Brier | 2.5 Üst Δ Brier | MS Δ Brier |
|---|---:|---:|---:|
| M4 orijinal | 0 | 0 | 0 |
| Deplasman savunması %90 | −0,000584 | −0,000687 | −0,000517 |
| Deplasman savunması %80 | −0,001115 | −0,001276 | −0,000842 |
| Her iki takımın savunması %90 | −0,001127 | −0,001431 | −0,000523 |
| **Her iki takımın savunması %80** | **−0,002131** | **−0,002689** | −0,000734 |

İki taraflı %80: KG Brier **0,254318 → 0,252187**; 2.5 Üst Brier **0,256786 → 0,254098**. Göreli Brier azalması yaklaşık KG **%0,84**, 2.5 Üst **%1,05**. Bunlar **tahmin isabet yüzdesi artışı değildir**.

MS için küçük Brier azalması var; fakat gün bloklu keşifsel %95 belirsizlik aralığı **[−0,002129, +0,000736]** sıfırı içeriyor. KG Var aralığı **[−0,003477, −0,000841]**, 2.5 Üst **[−0,004096, −0,001498]**; geliştirme dönemi içinde sıfırı içermiyor ama **bağımsız yeni dönem kanıtı sayılamaz**.

Daha önceki rakip savunma grupları arasındaki ev sahibi gol artığı farkı **+0,420 gol → +0,281 gol** oldu. Hatanın tamamen ortadan kalktığı iddia edilmiyor.

## Lig bazında %80 simetrik aday farkı

| Lig | KG Δ Brier | 2.5 Üst Δ Brier | MS Δ Brier |
|---|---:|---:|---:|
| ENG1 | −0,004163 | −0,006013 | −0,001915 |
| ENG2 | −0,002090 | −0,003470 | −0,002327 |
| GER1 | −0,004247 | −0,003007 | +0,002271 |
| ESP1 | −0,001066 | −0,004109 | −0,005509 |
| ITA1 | −0,000117 | −0,000759 | +0,003916 |
| FRA1 | **+0,001484** | −0,001766 | +0,001816 |
| NED1 | **+0,000402** | −0,001461 | −0,007114 |
| TUR1 | −0,007862 | −0,004145 | +0,003051 |
| POR1 | −0,007180 | −0,001610 | +0,002696 |
| BEL1 | **+0,003224** | **+0,000981** | −0,002383 |

**KG iyileşen lig 7/10, 2.5 Üst iyileşen lig 9/10, MS iyileşen lig 5/10.** Lig düzeyinde yaklaşık 57–115 maç; bunlar kesin lig-özel terfi kararı için yeterli kabul edilmez. Belçika'da KG ve Üst ikisi de kötüleşiyor; her lige koşulsuz aynı ağırlık uygulanamaz.

## GitHub testi ve korunmuş sistem

- [Gerçek GitHub Actions karşılaştırması ve **8/8 başarılı güvenlik testi**](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42973980325)
- [Bağımsız, salt araştırma kodu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-opponent-defence-shrinkage-20261111/research/opponent_goals/m4_opponent_defence_shrinkage_263.py)
- Tam, tek karşılaştırma JSON: Actions artifact `263-opponent-defence-weight-90-80-kg-o25-ms-devonly-no-promotion`.
- Dondurulmuş M4 ve m4_lock, ana dal `main`, aktif `experiment/263-toplu-karsilastirma`, tüm eski SHA mühürleri, 4.518/4.617 sonuç, oranlar, telefon arayüzü ve basketbol/LITE: **değişmedi**.

## Son mühendislik kararı — güvenilir olmayan kazancı üretime taşımıyoruz

1. **%80 simetrik savunma, tek sabit araştırma adayı** olarak not edilsin; diğer dört araştırma sonucu tekrar denenmesin. Bu bir model terfisi / farklı sürüm ilanı değil. Kullanıcının sabah maç tahminlerinde **hiçbir yüzdesi değişmiyor**.
2. Kesin kabul için **genuinely future pregame SHA-locked matches** ile ilk baştan aynı model, aynı maç ve sabit %80 gölge aday karşılaştırılmalı. Sabit gün veya 80 maç kotası peşinde yeni pilot açılmasın; mevcut maç önü ve maç sonu çalışma hattı kullanılabilir. Gölge hesap ayrı SHA ile kayıtlanmadıkça geçmiş maçtan sanki mühürlü tahminmiş gibi türetilmemeli.
3. Önceki 99 maçın skor arşivi ve 2026/27 sezonunu bu geliştirme kodunda seçilecek katsayılara uydurmak için kullanmıyoruz. **Bu bölümdeki mühendislik kararı: deney tamam, üretim M4 korunuyor, bağımsız kanıt gerekiyor.**
