# 2.6.3 — Rakip gücü ve son 5 maçlık formun M4 gol hatasına etkisi

**11 Kasım 2026 · 10 lig · yalnız araştırma dalı · ana M4 değiştirilmedi**

## Somut araştırma bulgusu: rakip savunmasının etkisi fazla keskin olabilir

M4'ün kendi gelişim döneminde fit edilmiş deplasman savunma katsayısına göre:

| M4 rakip deplasman savunması | Maç | Ev sahibinin gerçekleşen − beklenen golü |
|---|---:|---:|
| Güçlü (log-savunma ≤ −0,08) | 228 | **+0,173 gol** |
| Orta | 207 | +0,045 gol |
| Zayıf (log-savunma ≥ +0,08) | 267 | **−0,247 gol** |

Güçlü − zayıf grup ev gol hatası farkı **+0,420 gol/maç**; 41 maç günü blok-bootstrap keşifsel %95 aralık **+0,247 ila +0,592**. **10 ligin 9'unda** fark aynı yönde, **İtalya'da ters**. Bu sonuç, M4'ün rakibin savunma farkını geliştirme maçlarında olduğundan keskin uyguluyor olabileceğini gösterir; nedensel, bağımsız ya da gerçek yeni maçta isabet kanıtı DEĞİLDİR. Güç sınıflaması haricî Elo değil, modelin zaten öğrenmiş olduğu savunma katsayısıdır.

| Lig | Güçlü − zayıf ev gol artığı (gol/maç) |
|---|---:|
| ENG1 | +1,008 |
| ENG2 | +0,822 |
| GER1 | +0,449 |
| ESP1 | +0,407 |
| ITA1 | −0,527 |
| FRA1 | +0,637 |
| NED1 | +0,755 |
| TUR1 | +0,622 |
| POR1 | +0,148 |
| BEL1 | +0,102 |

## Son beş maçlık form düzeltmesi işe yaradı mı?

**Hayır, KG Var ve 2.5 Üst genel başarısını artırmadı.** Ev sahibi ve deplasmanın son 5 maçtaki rakipten arındırılmaya çalışılmış gol artıklarını kullanan, önceden sabit 0,10 ve 0,20 etki adayı karşılaştırıldı.

Aynı 696 maç için aday − M4 Brier farkları (negatif iyileşme):

| Form katsayısı | KG Var Δ Brier | 2.5 Üst Δ Brier | MS Δ Brier |
|---|---:|---:|---:|
| 0,10 | **+0,000400** | **+0,000264** | −0,000932 |
| 0,20 | **+0,000994** | **+0,000833** | −0,001301 |

Her iki adayın küçük MS kazançlarının da, KG/Üst değişimlerinin de 41 günlük blok-bootstrap keşifsel belirsizlik aralıkları sıfırı kapsıyor. 0,10 adayında aralıklar KG **[−0,000454, +0,001154]**, Üst **[−0,001094, +0,001510]**, MS **[−0,002701, +0,000477]**.

**Mühendislik kararı: Son-5 form katsayıları M4'e EKLENMEYECEK.** Şimdi sabit bir form yüzdesi eklemek daha çok bilgi vermek yerine KG ve 2.5 Üst hesaplarını bozabilir.

## Kaynak, dürüst sınırlama ve güvenlik

- 4.617 maçlık sonuç arşivi ve eski 4.518 satır SHA ile kontrol edildi; 99 maç dosyası değişmedi.
- Eski M4 geliştirme tasarımındaki **2025/26 sezonunun önceden belirli 3 tarih kesiti × 10 lig = 30 fold**; 702 M4 baz gol kontrolü ve **696** eksiksiz ev/deplasman son-5 form eşleşmesi (6 yok). 2026/27 sonuçlarının tamamı dışlandı.
- Form yalnız söz konusu maçtan **önceki** 5 maçta, en fazla 90 gün geriye gidilerek hesaplandı. Aynı gün veya sonraki sonuçlar, hedef maç tahmini, eski mühürler kullanılamaz.
- Dikkat: Son 5 maçın beklentileri, daha önce kilitlenmiş fold M4'ünden geldi; o eski maçların bazıları fit sırasında kullanıldığı için form artığı tamamen dış örnek değildir. Sonuç gelişim dönemi keşifsel kanıttır, yeni sezonda kanıtlanmış tahmin doğruluğu değildir.
- Önceden tamamlanan 984 maçlık Dixon–Coles/bivariate denemesi veya 6–8 Kasım pilotu yeniden çalıştırılmadı.
- Ana deney dalı, üretim main, M4 kilidi, önceden mühürlü maçlar, kullanıcı yüzdeleri, odds, mobil ekranlar ve LITE korunmuştur.

## Kanıt ve sonuç

- [GitHub Actions — 9/9 başarılı, 10 lig, 702 maç, 696 form ve 9/10 yön tutarlılığı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42911939985)
- [Tekrarlanabilir salt araştırma kodu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/research/263-opponent-form-residual-20261111/research/opponent_goals/m4_opponent_form_diagnostic_263.py)
- Tam sonuç JSON: Actions içindeki **263-opponent-form-10-league-goal-error-no-model-change** artifact.

**Sonraki en değerli aday:** Deplasman savunması katsayılarının gereğinden fazla sertliğini araştırmak. Ancak bu 702 maçta gözlenen desene göre aynı maçlardan bir katsayı seçmek aşırı uyum riski taşır. Gücü yumuşatma fikri önce dondurulmuş bir hipotez olmalı; kabulü bağımsız, kronolojik yeni gerçek maç önü mühürleriyle verilmelidir. Gelişim verisini kendine başarı kanıtı saymayacağız.

**Bugünkü karar:** M4 aynen kalır. Son-5 form katsayıları reddedilir. Rakip savunması keskinliği en güçlü araştırma adayı olarak not edilir. Yeni pilot, otomatik bahis kararı veya kullanıcı ekranına yeni yüzde EKLENMEZ.
