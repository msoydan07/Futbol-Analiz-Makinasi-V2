# M4 Aşama 5 — xG lig/sezon sayımı, kanıt kaydı (2026-11-03)

**Kapsam:** Eski başarılı iş akışının salt-okunur logları; yeni veri indirilmedi, model deneyi çalıştırılmadı.

## Kanıt
- GitHub Actions run: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41292163144
- Job ID: 124805449236; 2026-11-01 09:13–09:15 UTC, SUCCESS.
- `audit_understat_xg.py` çıktısı: source_rows=2183; historical_eligible=2156; matched_unique=2155; reviewed_date_overrides_applied=11.
- `build_verified_xg_history.py`: verified_xg_rows=2155; historical_rows=4413; rejected_by_status UNMATCHED=28.
- 2.155 / 2.183 = %98,72 **kaynak satırı eşleşmesi**, tüm ligler için xG kapsaması değildir.

| Lig | 2025/26 | 2026/27 | Toplam |
|---|---:|---:|---:|
| ENG1 | 380 | 80 | 460 |
| ESP1 | 380 | 99 | 479 |
| FRA1 | 306 | 71 | 377 |
| GER1 | 306 | 63 | 369 |
| ITA1 | 380 | 90 | 470 |
| **Toplam** | **1752** | **403** | **2155** |

Diğer beş lig ENG2/NED1/TUR1/POR1/BEL1 bu Understat deneyinin kapsamı dışındadır; 0 gerçek xG olduğu iddia edilmez.

## Yöntem ve sınır
- `paired_xg_poisson_report.json` 1549 eşleşik tahmin: ENG1=337, ESP1=345, FRA1=271, GER1=254, ITA1=342. Bu **M4+xG deneyi değildir**.
- Kaynak xG satırlarının tarihsel kimlik ve skor eşleşmesi geçmiş logda doğrulandı. Ham `historical_verified_xg.csv` eski artifact'te **yok**. Bugün lig/sezon sayımı logdan yapıldı; yeniden üretilmiş CSV değildir.
- 28 UNMATCHED satır karantinadadır. 11 tarih istisnası uygulandı; kaynak zaman damgası ve xG sürüm değişiklikleri için ayrı as-of denetimi gerekir.
- Kaynak lisansı izin vermedikçe ham xG public GitHub'a yazılmaz.

## Tek sonraki adım
- M4+xG adayını değerlendirmeden önce aynı eski xG satırlarının **özel/izinli ortamda yeniden üretilebilirliği**, gerçek maç yayın zamanı/as-of ve 873 ortak C3/M4 kohortuyla kesişim sayısı denetlenmeli.
- Yalnızca yeterli kesişim varsa tek önkayıtlı araştırma deneyi; eski Poisson testi tekrarlanmaz.
- Main, kilitli C3/M4, 100 maç pilotu ve 4413 maç arşivi değişmez.
