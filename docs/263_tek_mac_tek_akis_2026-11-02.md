# 2.6.3 — Tek maç, mevcut resmî kontrol ve matematik bağlantısı

**Tarih:** 2 Kasım 2026. **Kapsam:** deney dalı; mevcut `main` ve Model B korunuyor.

## DÖNGÜ KONTROLÜ

- Yeni model **yok**; xG/C2/C3 performans testleri **tekrarlanmadı**.
- Yeni fikstür listesi, otomatik tarama, adaptör veya Modül 0 **yok**.
- `on_demand_context_263.prepare_named_match()` mevcut `analyze_named_match_gate.run()` işlevini kullanıyor; kullanıcı tek maç ismini Maçkolik yazımıyla veriyor.
- Bu çağrı gerçek bir resmî kaynaktan teyit döndürmedikçe matematik çalıştırıcısı **çalışmıyor**. Haricî, kullanıcıdan gelen `verified:true` JSON'unu kabul etmiyoruz.
- Resmî takım kimlikleri, gözden geçirilmiş 215 takımlı ad dizininin kimlikleriyle **bire bir** aynı olmalı. Ev/deplasman/tarih eşleşmezse fail-closed.
- İlk 11'in henüz yayınlanmamış olması **engelleyici değil**. Olasılıkları doğrulanmamış haberlerle değiştirmek **yasak**.
- Güncelleme kararı **Salı, Türkiye saati**. Otomatik Salı zamanlayıcısı bu çalışmada etkinleştirilmedi.

## İki güvenli veri modu

**`FROZEN`:** Önceden dondurulan 4.413 maçın SHA-256'sı doğrulanır; mevcut Model B ve kanonik C2/C3 karşılaştırma raporu ve mevcut 17-bölüm **offline** uygunluk kontrolü **aynen** çalışır. Maç kimliğinin resmen kontrol edilmiş olması, offline matematik raporunu otomatik onaylı canlı tahmine dönüştürmez. `request_status.json` açıkça böyle yazar.

**`STAGED`:** `season_refresh_263.py` ile oluşturulmuş `extended_history.csv` + `refresh_audit.json` ve ayrıca orijinal dondurulmuş CSV gerekir. Mevcut `updated_preview_263.preview()` kullanılır. Eski satırlar ve SHA-256 yeniden karşılaştırılır; yeni veri sağlayıcı dosyaları bağımsız teyit edilmemiş olarak kalır. **17-bölümün eski kabul raporu bu dosyaya taşınmaz.** Model onayı/bahis önerisi/pilot kesinlikle yok.

### Salı sonrasında tek maç akışı (kurulu kaynak dosyaları olduğunda)

```bash
# Repo kökünden; önkoşul: halihazırdaki kimlik hattının oluşturduğu
# data/match_registry.json, 215-team index/aliases, mevcut resmî source adapter.
PYTHONPATH=.:experiments/263 python experiments/263/requested_match_runner_263.py \
  --league TUR1 --home 'Galatasaray' --away 'Konyaspor' \
  --registry data/match_registry.json \
  --index experiments/263/evidence/identity_index_263.json \
  --aliases data/team_aliases_reviewed.csv \
  --history /path/to/extended_history.csv \
  --base /path/to/frozen_4413.csv \
  --refresh-audit /path/to/refresh_audit.json \
  --out /tmp/requested_match_263
```

Bu yalnız **kullanıcının seçtiği** maç için resmî sorgu yapar; kendiliğinden maç bulmaz. `--base`/`--refresh-audit` olmadan, `--history` dondurulmuş CSV ve `--evidence experiments/263/evidence/acceptance_263.json` kullanılır.

## Çıktı ve onay sınırı

- Resmî sorgu başarısız: `request_status.json` → `OFFICIAL_FIXTURE_NOT_VERIFIED`; **model hesaplanmaz**.
- Başarılı resmî sorgu + dondurulmuş veri: `OFFICIAL_FIXTURE_CHECKED_FROZEN_MATH_PREVIEW_ONLY`; mevcut 17 bölümlük offline rapor ve kabul kanıtı ayrıca çıkar.
- Başarılı resmî sorgu + Salı dosyası: `OFFICIAL_FIXTURE_CHECKED_STAGED_MATH_PREVIEW_ONLY`; yalnız güncellenmiş matematik önizlemesi çıkar; bağımsız model onayı **yok**.
- `live_analysis_accepted=false`, `A_B_C_approved=false`, `recommendations=[]`, `odds_EV=null`, `pilot_recorded=false` tüm modlarda sabit.
- Mevcut 4.413 maç 29 Ekim 2026'da bitiyor. Bu çalışmada Salı günü için yeni maç sonucu toplanmadı ve canlı resmî sorgu çalıştırılamadı.

## Test kanıtı ve açık tek engel

`python -m unittest -q test_requested_match_runner_263.py` ile **11 yeni entegrasyon güvenlik testi** geçti. Testte resmî teyit **sentetik ve enjekte edilmiş test yanıtıdır**; gerçek bir federasyon kanıtı değildir. Bir gerçek maçın tam, doğrulanmış 17-bölüm analizinin kabul edildiği **iddia edilmez**.

**Kalan somut iş:** Salı günü verileri alındığında mevcut `data/match_registry.json` ve denetim çıktılarıyla **tek gerçek kullanıcı maçı** üzerinden resmî teyit, güncel veri ve kaynak zamanı doğrulanmalı. Güncel dosyanın yeni sonuçları bağımsız kabul edilene kadar live readiness/kalibrasyon/EV/pilot açılmayacak. Bir sonraki bağımsız ileri dönem model testi eski 614/1549 maç sonuçlarını yeniden skorlama değildir.
