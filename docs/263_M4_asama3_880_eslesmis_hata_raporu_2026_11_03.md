# M4 AŞAMA 3 — 880 maçta C3–M4 eşleşmiş hata analizi
**Tarih:** 2026-11-03 · **Durum:** RETROSPECTIVE_EXPLORATORY / REGRESSION_8_OF_8_PASSED / NO_PROMOTION

## Yöntem ve değişmezler
- Orijinal 4.413 satırlık kaynak, SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`, GitHub Actions 41251343847 / artifact 13061725424, dosya paketinden okundu ve aynı hash doğrulandı.
- Dondurulmuş matematik: `exp_263_batch.py` C3 Ridge=6; `m4_integrated.py` M4 yarı-ömür=360 gün, ortak Ridge=4, saha Ridge=48. Aynı matematik işlevleriyle tek bir yerel tarihsel teşhis gerçekleştirildi; **hiçbir ayar değiştirilmedi**, bir yeni seçim yapılmadı.
- Hedef 2026/27'nin 880 maçı; her hedef için yalnız `match_date < target_date` eğitimine izin verildi, aynı gün sonuçları yasak. Tüm çıktılar bu sefer tek tek kaydedildi.
- Eski 2026/27 zaten daha önce gözlenmiş olduğundan yalnız **hipotez geliştirmeye** uygundur; bağımsız ileri dönem son test değildir.

## Kanıt: 8/8 eski rapora eşitlik
Eski `M4_RETROSPEKTIF_DORTLU_KARSILASTIRMA_2026-11-02.md` ile **8 sabit regresyon kontrolü** geçti:
C3 tahmin 873; M4 tahmin 880; ortak 873; ortak C3 1X2 log-loss 0,9971; ortak M4 log-loss 0,9993; tüm M4 log-loss 1,0012; M4 %80+ güven sayısı 24; bu grubun isabeti 15/24.

| Aynı 873 maçta | C3 | M4 |
|---|---:|---:|
| 1X2 log-loss | 0,997131 | 0,999336 |
| 1X2 Brier | 0,594649 | 0,595900 |
| 1X2 isabet | 450 / 873 (%51,55) | 449 / 873 (%51,43) |
| KG Var/Yok log-loss | 0,682632 | 0,685210 |
| 2,5 Alt/Üst log-loss | 0,685175 | 0,690650 |

**C3 eksi M4 log-loss:** −0,002205; 1000 tarih-blok bootstrap %95 [−0,00663; +0,00205] → **üstünlük kanıtlanmadı**. Bootstrap tohumu/tekrar sayısı eski rapordan farklı; sayısal sınırlar çok yakın, test hükmü aynı.

## Asıl yeni teşhis
Pozitif fark M4 lehinedir.

| Eşleşmiş alt grup | N | C3 − M4 1X2 log-loss | Açıklama |
|---|---:|---:|---|
| En az bir takımın 2025/26 aynı lig geçmişi yok | 268 | **−0,008804** | M4 kaybı daha belirgin; tarih-blok 5000 bootstrap %95 [−0,02049; +0,00299] → **kesin değil** |
| İki takımın da 2025/26 aynı lig geçmişi var | 605 | **+0,000718** | Çok küçük avantaj; bootstrap %95 [−0,00363; +0,00522] |
| Cari sezon iç/dış saha bağlamında bir tarafın <4 maçı var | 768 | −0,00256 | Az veri hipotezi |
| İki tarafın da cari saha bağlamında >=4 maçı var | 105 | +0,00041 | Fark çok küçük |
| Gerçek sonucu beraberlik çıkanlar | 209 | −0,01408 | **Sonuçtan sonra tanımlanan grup**, maç öncesi seçim kuralı olamaz |
| M4 en yüksek 1X2 güveni %80 veya üzeri (ortak) | 18 | −0,03402 | Küçük ve seçilmiş grup |
| M4 ve C3 farklı 1X2 favorisi seçmiş | 48 | −0,00872 | Diğer **825/873 (%94,5)** maçta tercih aynı |

- 880 M4 tahmininin 24'ünde en yüksek sonuç olasılığı **>%80**, ortalama güven %84,10; doğru sayısı **15/24 (%62,5)**. Ortak 873 maçta bu eşiği M4 18, C3 8 kez geçti. Küçük örneklem.
- Ortak 873 maçta ortalama beraberlik olasılığı C3 %23,944, M4 %23,648; gerçek beraberlik oranı %23,940. Salt ortalama tek başına düzgün kalibrasyon değildir.
- 2026/27 en az bir takımın bir önceki sezonda aynı lig geçmişinin olmaması **272/880 hedefte** geçerliydi; bunun **268'i** iki model ortak tahmin verdiği 873 kapsamına giriyor. 272 ile 268 çelişki değil, farklı payda.
- Yeni takım göstergesi ile düşük toplam saha geçmişi benzer maçların çoğunu işaretliyor. Birbirinden bağımsız iki kanıt olarak sayma.

### Lige göre aynı 873 maçın farkı
| Lig | N | C3 − M4 |
|---|---:|---:|
| BEL1 | 80 | −0,00540 |
| ENG1 | 80 | −0,00665 |
| ENG2 | 144 | −0,00955 |
| ESP1 | 98 | −0,00109 |
| FRA1 | 72 | +0,00117 |
| GER1 | 60 | +0,00771 |
| ITA1 | 90 | +0,00521 |
| NED1 | 87 | +0,00612 |
| POR1 | 81 | +0,00287 |
| TUR1 | 81 | −0,01555 |

**Uyarı:** Lig/ay/güven/gerçek sonuç kırılımları keşifsel çoklu karşılaştırma içerir. Nedensel etki veya genellenebilir üstünlük olarak yorumlanamaz.

## Mühendislik kararı
**AŞAMA 3 TAMAMLANDI.** C3–M4 eski sonuçları yeniden üretildi ve maç bazlı hata profili oluşturuldu.
- M4 için en kuvvetli yeni deney hipotezi: **yeni gelen takım / düşük geçmişli bağlamlarda daha fazla düzenlileştirme veya uygun geçmiş aktarımı** fayda sağlayabilir mi? Bu henüz doğrulanmamış öneridir.
- 2024/25 araştırma havuzu eklenerek **ek geçmiş var/yok**, **zaman ağırlığı var/yok**, **takıma özel saha parametresi var/yok** aynı hedef maçlarda ayrı karşılaştırılacak.
- Aday/parametre listesi ve veri kesimleri **testten önce yazılarak kilitlenecek**. 2026/27'nin görülen sonuçları üzerinden ayar avcılığına girilmeyecek.
- Son başarı ancak maç önü mühürlenmiş yeni gerçek maçlarla sınanabilir; B/C2/C3/M4 ana modelleri, M4 kilidi, 100 maç pilotu ve Galatasaray UEFA T−60 kaydı **değişmedi**.

## Tek defalık offline kanıt paketi
Tek batch çalışmasının tam maç-bazlı olasılık CSV'si, ayrıntılı JSON'u ve çalıştırılan teşhis Python kodu bu sohbet için oluşturulan `M4_Asama3_Tek_Toplu_Hata_Analizi_2026_11_03.zip` paketinde ayrıca korunmuştur. Paket içinde eski 4.413 satırın hash-doğrulanmış çalışma kopyası da vardır. Bu belge **özet**; ZIP içeriği otomatik GitHub'a yüklenmedi, ana veri dizinine karıştırılmadı.
