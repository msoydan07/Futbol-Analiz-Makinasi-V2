# Futbol 2.6.3 — 4.618 özel skor + ilk iddaa PDF + orandan bağımsız araştırma entegrasyonu

**Tarih:** 19 Kasım 2026  
**Dal:** `research/263-13-lig-22-havuz-20261113`  
**Durum:** **KOD BAĞLANTISI HAZIR; CANLI MAÇ ÖNÜ KABULÜ YOK**.  
**Geçerli kurallar:** D-ODDS-001 (iki PDF / tek sabah mühür), D-MARKET-006 (MARKET yalnız beşinci referans), D-MODEL-003 (ana M4 + 96 pilot + eski mühürler değişmez).

## Bu turda gerçekten eklenen kod

| Araştırma dosyası | İş |
|---|---|
| `experiments/263/private_4618_quad_forward_263.py` | Eski `forward_quad.py` dosyasından türetilmiş ayrı çalıştırıcı. `_legacy_joint`, `_b_lambdas`, mevcut `c1`, `canonical_c2_lambda`, `fit_c3`, `fit_m4` ve `predict_m4` matematiğini değiştirmez. 4.618 sabit SHA + sonuç boşluğu kontrolü üzerinden B/C2/C3/M4 araştırma tahmini üretir. Eski 96 kayıtlarına yazmaz. |
| `experiments/263/private_4618_empirical_baseline_263.py` | Yeni 4.618 araştırma kaynağından maç öncesi lig baz oranlarını (bahis fiyatı değil) hesaplar. |
| `experiments/263/private_4618_provider_bundle_263.py` | PDF'de seçili her lig için sezon sonuçlarını `football-data.co.uk` üzerinden bir kez indirmeyi dener; kaynak dosyası SHA ve gözlem saatini özel klasörde saklar. Hedef tarihten önce bitmiş fakat 4.618 dondurulmuş arşivinde olmayan lig maçı varsa yalnız o ligin analizini engeller. |
| `experiments/263/private_4618_pdf_session_263.py` | Orijinal PDF/kimlik/resmî fikstür ara denetimini ve dört model yapısını koruyarak yeni araştırma çalıştırıcısına ve lig temel oranı üreticisine bağlar. |
| `experiments/263/private_4618_iddaa_model_first_one_step_263.py` | Tek PDF → tek model/mühür → yalnız model verisine göre ana/alternatif/PAS → iddaa oranlarının ayrı beşinci referans tablosu → kaynak PDF raporu. |
| `experiments/263/private_4618_retry_guard_263.py` | Bağlantı koptuğunda **hiç model mührü yazılmamışsa** aynı PDF için eski başarısız klasörü koruyup yeni denemeye izin verir. Herhangi bir SHA tahmin varsa ikinci mühür üretimini engeller. |

**Değiştirilmeyen dosyalar:** `m4_integrated.py`, `forward_quad.py`, `forward_empirical_baseline_263.py`, `iddaa_pdf_session_263.py`, `iddaa_pdf_last_review_263.py`, eski tek-PDF araştırma girişleri, üretim iş akışları, SHA tahminler ve otomasyonlar.

## Özel veri ve yürütme

Kullanıcının onayladığı 4.618 araştırma kaydı SHA `3b13921daafab70aa121fe807fea0a74e0c72f0fc2381366b183f621edea762c`. Yeni özel **yalnız skor** projeksiyonu `54250bb6107250d0623b74ad9c56f90731f02d10dab3bf386deefb27aae487ea` (4.413 birebir eski skor satırı + 205 ek sonuç). `historical_results_original.csv` eski SHA `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.

**Hiçbir özel xG ham verisi veya 4.618 satır GitHub'a yüklenmedi.** Bu hat B/C2/C3/M4'ün mevcut skor temelli hesaplarını kullanır; xG katkısı kanıtlanmadan temel M4'e eklenmez.

Araştırma çalıştırma örneği (özel bilgisayarda):
```bash
PYTHONPATH=.:experiments/263 python experiments/263/private_4618_iddaa_model_first_one_step_263.py \
  --pdf "/private/iddaa_sabah.pdf" \
  --history "/private/263_4618_MATCHDAY_SCORES_RESEARCH_PRIVATE_20261119.csv" \
  --source-baseline "/private/historical_results_original.csv" \
  --out-dir "/private/263_morning_sessions"
```

Bu komut **canlı bahis onayı sağlamaz**. Resmî fikstür doğrulaması kendi mevcut adaptöründen gelir; tam resmî sonuç takvimini bağımsız olarak doğruladığımız anlamına gelmez. İddaa oranı yalnız kullanıcının gönderdiği PDF'den gelir; başka bahis şirketi çağrısı YOK. Kullanıcı ikinci PDF gönderdiğinde, değişmeyen `iddaa_pdf_last_review_263.py` önceki sabah SHA'sına bağlı yalnız futbol yorumu üretir; tercih ve yüzdeleri değiştiremez.

## Gerçek doğrulama kanıtı ve sınır

- **Başarılı yerel testler:** 4.618 özel dosyanın SHA / 4.413 korunması, 205 ek kayıt, bozuk skor, yeni tamamlanmış lig maçı, eksik/veri değiştirilmiş kaynak, sahte indirme ve internet kesintisinde mühürsüz tekrar deneme. Önceki araştırma kaynaklarıyla birlikte **46 yerel sentetik/gerçek-bütünlük senaryosu geçti** (kullanıcının çalışma alanında). Bu testler **yeni tam maç önü kodunun gerçek PDF üzerinde uçtan uca çalıştığını kanıtlamaz**.
- **GitHub'da yeni testler:** `test_private_4618_live_integration_contract_263.py` (13 sözleşme testi) ve `test_private_4618_retry_guard_263.py` (6 değişmezlik testi). CI iş akışı: `.github/workflows/263-private-4618-model-first-integration-ci.yml` (Python compile + import + kontrol). **GitHub Actions sonuç kaydı henüz ayrı doğrulanmadı; başarılı CI iddiası yok.**
- **İlk gerçek 10 lig iddaa PDF'si** ile `resmî fikstür → 4.618 skor + güncel provider witness → B/C2/C3/M4 → model-first SHA → piyasa beşinci referans → PDF raporu` çalıştırılmadı.
- **İlk 11 + ikinci iddaa PDF** ile değişmeyen ilk SHA'ya ek yorum kaydı gerçek maç özelinde ayrıca kabul edilmedi.
- **Kritik eksik:** En azından seçilen liglerde belirli aralıkta oynanmış tüm lig sonuçlarının federasyon/resmî lig kaynağından bağımsız ve tam kapsamlı tasdiki yok. `football-data.co.uk` yalnız **ikincil kaynak**; eksik haber vermemesi resmi takvim eksiksizliğinin matematiksel kanıtı değildir.
- **Kalibrasyon uyarısı:** Önceki 496 maç retrospektif model-first deneyinde 286 aday, 210 PAS; adayların ortalama yüzde tahmini 69,53, gerçekleşme oranı 62,59. Bu set bağımsız son holdout değil; mevcut araştırma kararının canlıya otomatik terfisini haklı çıkarmaz.

## Kesin denetim sonucu

**A** — Kullanıcıyla alınmış kararlar değişmedi.  
**B** — 4.618 özel veri / ilk iddaa PDF / model-first tahmin / piyasa karşılaştırması araştırma kodları **aynı hat üzerinde bağlandı**; mühürsüz güvenli tekrar deneme eklendi.  
**C** — Tam gerçek PDF, resmî kaynak, yeni karar modeli kalibrasyonu ve CI teyidiyle **CANLI KABUL YOK**.

**Sıradaki gerçek teknik kapı:** İlk kapsam ligi iddaa PDF'sini ve resmi fikstürü gerçek kaynaklarla aynı gün çalıştırıp SHA'lı raporu doğrulamak; seçili ligdeki tamamlanmış sonuçların eksiksizliğini resmî kaynakla ayrıca kontrol etmek. Ana M4 / eski mühürler / kaynaklar asla geriye dönük değiştirilmez.
