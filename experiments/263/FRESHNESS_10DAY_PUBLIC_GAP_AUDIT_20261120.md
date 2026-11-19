# 20 Kasım 2026 — 10-günlük kaynak tazeliği: güvenli lig arası kanıt kapısı

## Problem / karar
- Ana `forward_quad.py` geçmiş lig maçının üstünden 10 **takvim günü** geçtiğinde `stale_history_refresh_required` ile her tahmini kesiyordu. Ancak milli maç arası 10+ gün **yeni maç olmadığı** anlamına gelebilir.
- Karar: Varsayılan **10 gün korunur**. Yalnız **11–21 gün** aralığında önceden SHA-kilidi ve kimlik doğrulaması yapılmış 2026/27 kabul geçmişine yeni çekilmiş kaynakla eşleştirilen **tüm güncel-sonuç kapsamı** kanıtlanırsa araştırma tahmini devam edebilir.
- Kaynak: football-data.co.uk /mmz4281/2627/{lig}.csv güncel sezon kamuya açık **ikincil kaynak**, resmî federasyon attesti değildir. Bağımsız ve taze **resmî adlandırılmış fikstür kapısı** değişmez.
- Kural: sağlayıcı tamamlanmış maç sayısı kabul edilmiş cari sezon toplamından az olamaz; en son tamamlanmış kaynak tarihi kabul geçmişiyle aynı olmalıdır; son 21 gündeki tüm kabul edilmiş maçlar tarih+kanonik ev/deplasman kimliği+skor bazında kaynakla **tam ve iki yönlü** eşleşmelidir. Kaynaktaki tek bir yeni tamamlanmış maç, tek bir uyuşmayan skor / kimlik / tarih veya eksik veri = **BLOCKED_NO_FORECAST**.
- Sağlayıcı sonuç CSV'sinde gelecek karşılaşmalar her zaman yer almadığından, bu belgeler bir **fikstür takvimi** değil; gelecek maçı ancak ayrı resmî fikstür doğrulayıcısı kanıtlayabilir. Kaynak HTTP/sertifika/indirme hatası, başka alan adına yönlendirme ve 21 günden uzun ara = **BLOCK**.
- Kaynak dosyası yeniden GitHub'a yazılmaz; xG, oran, eski SHA-mühürler ve B/C2/C3/M4 matematiği değiştirilmedi. Hafızadaki geçici kanıt yeni tahmin JSON'unun kaynak-durumu içine eklenir.

## Gerçek 20 Kasım (TSİ) public-source salt-okunur kontrol

`data/results_only_263/2026-11-10_completed_4617_scores_only.csv` SHA:
`637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89`.

| Lig | Arşiv son maç | 20 Kasım fark | Güncel sağlayıcı son maç | Yakın tarihli doğrulanan eşleşme |
|---|---|---:|---|---:|
| BEL1 | 2026-11-08 | 12 | 2026-11-08 | 27 |
| ENG1 | 2026-11-08 | 12 | 2026-11-08 | 35 |
| ENG2 | 2026-11-07 | 13 | 2026-11-07 | 60 |
| ESP1 | 2026-11-08 | 12 | 2026-11-08 | 36 |
| FRA1 | 2026-11-08 | 12 | 2026-11-08 | 32 |
| GER1 | 2026-11-08 | 12 | 2026-11-08 | 29 |
| ITA1 | 2026-11-08 | 12 | 2026-11-08 | 46 |
| NED1 | 2026-11-08 | 12 | 2026-11-08 | 32 |
| POR1 | 2026-11-08 | 12 | 2026-11-08 | 27 |
| TUR1 | 2026-11-08 | 12 | 2026-11-08 | 31 |

**10/10:** Kamuya açık sonuç dosyasında kabul arşivinden sonra oynanıp sonuçlanmış maç bulunamadı; kayıtlar arasında yakın tarihli skor uyuşmazlığı da görülmedi. Resmî federasyonlardan 10 ligin tamamına **ayrıca doğrudan doğrulama yapıldığını iddia etmiyoruz**.

## Test kanıtı
- 8 sentetik fail-closed testi: 8/8 geçti; kaynak kısa/eksikse, maç skoru uyuşmazsa, yeni maç varsa, 21 gün aşılırsa, geleceğe sızma varsa engel.
- 10 ligin canlı kamuya açık sezon kaynakları salt-okunur kontrol edildi: 10/10 bounded research gap kaydı.
- Gerçek 4.617 SHA arşivi + aynı sabit 4.413 temel + mevcut B/C2/C3/M4 formülleriyle, **yalnızca geçici dizine** bir sentetik maç fixture gate'i kurularak dört modelin pipeline'i çalıştırıldı. B,C2,C3,M4 dört model de AVAILABLE; gap kaydı kaydedildi; kaynak değişmedi; eski SHA mühür değişmedi; resmî fikstür gibi sunulmadı ve pilot sayısına eklenmedi.
- GitHub Actions: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44623883897
- Sonuç: **20 Kasım ana deneysel tahmin yolu için 10 gün engeli güvenli bounded istisnayla ele alındı.** Bu, otomatik gerçek maç mühürlemesinin, resmî fikstür kaynaklarının, bahis oranlarının, kârlılığın veya tam canlı zincirin doğrulandığı anlamına gelmez.

## Sonraki tetikleme
Kullanıcının maç günü adlandırılmış maç/PDF talebi ve resmî fixture kapısı doğrulandığında yeni sonuç indirmeyi ayrı **salt-okunur** tazelik kaydıyla kontrol et. Kaynakta yeni sonuç görürse, kabul arşivini otomatik değiştirme; yeni maçları doğrulamak için veri yenileme işini açıkça raporla. Asla 10 günlük limiti körlemesine yükseltme.
