# 2.6.3 — Güvenli veri yenileme (izole deney)

Bu deney üretim kodunu ve dondurulmuş 4.413 maçlık kabul verisini değiştirmez. Eski maçın herhangi bir alanının değişmesi reddedilir. Yeni satırlar sadece denetlenen 2026/27 on lig sonuçları olabilir.

**İki giriş biçimi:** Var olan haftalık GitHub veri hattının `historical_results.csv`, `historical_results_audit.json` ve `source_audit.csv` dosyaları tercih edilir. Alternatif kaynak, aynı sağlayıcıdan gelen on liglik sezon CSV setidir. İkisinde de eski 4.413 maç ve kimlik eşleşmesi kontrol edilir. Kaynak URL'si tek başına bağımsız doğrulama değildir.

### Haftalık veri paketi denetimi

```bash
python experiments/263/season_refresh_263.py \
  --base /path/to/frozen_4413.csv \
  --identity-index experiments/263/evidence/identity_index_263.json \
  --refreshed-history /path/to/historical_results.csv \
  --pipeline-audit /path/to/historical_results_audit.json \
  --source-audit /path/to/source_audit.csv \
  --as-of 2026-11-02 \
  --output /tmp/263_update
```

Üretilen `extended_history.csv` yalnız deneysel girdidir; `refresh_audit.json` değişmezlik, kapsam ve kaynak bilgilerini taşır. `--as-of` işlemin gerçek günüyle değiştirilmelidir ve gün dahil değildir.

Matematiksel önizleme için `updated_preview_263.py`, dondurulmuş kaynak ve yeni denetim çıktısını birlikte ister. Yeni veri geçmiş kabul/kalibrasyon raporuna otomatik dahil sayılmaz. **Bahis önerisi, EV, pilot veya gerçek maç kaydı üretilmez.**

### Test ve gerçek durum

Kaynakla beraber sunulan `test_refresh_and_preview_263.py` yerelde **20/20 geçti**. Eski haftalık veri paketi üzerinde **0 yeni maç** bulundu; bu bir güncellik kanıtı değildir. Kodun canlı yeni sonuçlarla ve GitHub Actions'ta uçtan uca kabulü ayrıca gereklidir. Tam kod ve testlerin yerel ZIP paketi ayrı tutulur. Ana Model B/C2/C3 matematiği değiştirilmedi.
