# M4 Aşama 5 — xG uygunluk ve tekrar-deney engeli (2026-11-03)

Durum: **ÖN ENVANTER TAMAMLANDI; M4+xG ETKİ TESTİ BAŞLATILMADI.** Bu rapor yalnız mevcut GitHub kayıtlarıyla salt-okunur denetimdir.

## Doğrulanmış mevcut kanıt
- 2026-11-01 `verified-xg` Actions run 41292163144 başarılı; artifact 13077519072 (`verified-xg-audit`), sha256 ee447873ec8d822760c42b934f000e800af04741d75a7c666c9953b4cca35ebc; artifact 2027-01-30'a kadar saklanıyor.
- Mevcut doküman `docs/263_xg_sali_guncelleme_dongu_karari_2026-11-01.md`: 2.155 verified xG satırı, 1.549 eşleşmiş gol-Poisson / xG-Poisson karşılaştırması; ortalama xG lehine log-loss farkı +0.003576, 2026/27 290 maçta -0.010615; blok bootstrap %95 [-0.006465, +0.013838]. Üstünlük kanıtlanmadı.
- Bu sonuç **M4+xG karşılaştırması değildir**. Aynı 1.549 maçlık Poisson testini tekrar etmeyin.
- `collect_understat_xg.py` kapsamı ENG1, GER1, ESP1, ITA1, FRA1; sezonlar 2025/26 ve 2026/27. Diğer beş lig ENG2, NED1, TUR1, POR1, BEL1 için bu doğrulanmış Understat hattı kapsam sunmuyor.
- `build_verified_xg_history.py` yalnız MATCHED satırlarını fixture ID, lig/sezon, skor, tarih ve xG geçerliliği denetimiyle kabul ediyor. `experiments/263/verified_xg_context_263.py` tahminde sadece hedef tarihten eski kayıtları betimsel okuyor; lambda ve model seçimini değiştirmiyor.
- Artifact raporları ham `historical_verified_xg.csv` içermiyor. GitHub deposunda lig/sezon/maç bazlı **güncel doğrulanmış xG CSV'si mevcut olduğu teyit edilemedi**. 2.155 sayısı önceki deney çıktısıdır; bugün erişilebilir ham veri sayısı olarak yazılmamalı.

## Kapsam matrisi (gerçek satır sayısı henüz bilinmiyor)
| Lig | 2025/26 | 2026/27 | Kaynak / durum |
|---|---|---|---|
| ENG1 | sayım bekliyor | sayım bekliyor | Understat doğrulanmış hat |
| GER1 | sayım bekliyor | sayım bekliyor | Understat doğrulanmış hat |
| ESP1 | sayım bekliyor | sayım bekliyor | Understat doğrulanmış hat |
| ITA1 | sayım bekliyor | sayım bekliyor | Understat doğrulanmış hat |
| FRA1 | sayım bekliyor | sayım bekliyor | Understat doğrulanmış hat |
| ENG2 | doğrulanmadı | doğrulanmadı | Alternatif kaynak lisansı/kapsamı bekliyor |
| NED1 | doğrulanmadı | doğrulanmadı | Alternatif kaynak lisansı/kapsamı bekliyor |
| TUR1 | doğrulanmadı | doğrulanmadı | Alternatif kaynak lisansı/kapsamı bekliyor |
| POR1 | doğrulanmadı | doğrulanmadı | Alternatif kaynak lisansı/kapsamı bekliyor |
| BEL1 | doğrulanmadı | doğrulanmadı | Alternatif kaynak lisansı/kapsamı bekliyor |

## Tek sonraki işlem / kabul kapısı
1. Önceki artifact raporlarının tam lig/sezon kırılımını ve ham verinin **izinli, özel** çalışma alanında yeniden üretilebilirliğini doğrula. Artifact tek başına maç bazlı xG dosyası değildir.
2. Fixture bazında kaynak URL'si, ev/deplasman yönü, maç tarihi, xG geçerliliği ve as-of yayın zamanı kontrolü; karantina ve eksik kayıtları ayrı say.
3. Ancak yeterli ortak maç ve kronolojik veri kanıtlanırsa, kilitli C3 ve M4'e karşı **tek önkayıtlı M4+xG araştırma deneyi** tasarla. Gol-Poisson/xG-Poisson testini tekrarlama; 2026/27 daha önce görüldü, bağımsız final değildir.
4. Main, canlı C3/M4, pilot tahmin kayıtları ve eski 4.413 maçlık veri **değişmez**. Ham xG'yi public GitHub'a koyma. Lisans/as-of belirsizse dur, başarı iddiasında bulunma.
