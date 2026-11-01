# 2.6.3 — §12–14 Karar hazırlığı: tek entegrasyon kaydı

**Kapsam:** Deney dalında salt-okunur offline karar hazırlığı. Matematik, fikstür, geçmiş model performansı, xG testleri, oran ve pilot üzerinde değişiklik yok.

## Entegre edilen akış

- `operational_report_263.py` artık kanonik C2 hesaplanmışsa `decision_preflight_263.evaluate_case` çağırır; örnekte C2 yoksa Model B/C3 birincil seçime dönüşmez.
- `section_acceptance_263.py` §12–14 için hem pazar olasılık bütünlüğünü hem A/B/C, EV ve öneri kilidini denetler.
- MS 1/X/2, çift şans, genel gol/KG ayrı; %75 yalnız İZLEME filtresi, güvenilirlik onayı değil. Aynı lig/sezondaki geçmiş gerçekleşme sıklığı yalnız açıklayıcı veri.
- İlk yarı korner kapsam dışı. İlk 11 henüz açıklanmamışsa analiz durmaz.
- Haftalık veri güncellemesi: **Salı, Europe/Istanbul**. Zamanlayıcının gerçekten çalıştığı iddia edilmiyor.

## Test kanıtı ve sınır

- Yeni karar modülünün 18 testi yerelde geçmiş 4.413 maç snapshotıyla geçti; 3 varsayımsal offline analiz raporu üretildi (önceki çalışma).
- Depoda koşabilen testler artık ek CSV istemeden `evidence/section_contract_sample_263.json` üzerinden **sentetik geçmiş satırları** kurar; mevcut 16 §1–17 kabul testi + 18 yeni karar testi = **34 yerel test geçti**. Bu kaynak biçimiyle CI henüz çalıştırılmadı.
- Sentetik testlerin amacı yazılım güvenliği ve kabul sözleşmesidir; tahmin başarısını yeniden ölçmek değildir.
- **A/B/C onayı, değer/EV önerisi, gerçek maç tahmini ve pilot kaydı üretilmez.** C2'nin düşük kapsaması ve bağımsız ileri model kanıtı hâlâ açıktır.
- Bu güncelleme `main` ve Model B'ye dokunmaz.

**Sonraki gerçek ihtiyaç:** Salı güncellemesinden gelen gerçek denetlenmiş verilerin ve kullanıcıdan gelen tek maçın mevcut analiz hattına bağlanmasının canlı kabulü. Fikstür tarama projesi ve eski tarihsel testlerin tekrarına dönülmez.
