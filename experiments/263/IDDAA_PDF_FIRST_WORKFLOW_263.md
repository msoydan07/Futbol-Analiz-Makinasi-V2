# Futbol 2.6.3 — Tek İddaa PDF → dört model → oranlı rapor

**Durum (11 Kasım 2026):** PDF-FIRST karar entegrasyonu deney dalına eklendi, **48/48 çevrimdışı GitHub testi başarılı**. İlk kapsam ligi PDF'siyle gerçek canlı resmî fikstür ve model uçtan uca kabulü henüz yapılmadı.

**Son başarılı test:** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43056590227

## Kesinleşen kullanıcı iş akışı

1. Kullanıcı İddaa.com'da yalnız o günün 10 kapsam liginden istediği ligleri filtreleyip **Chrome Yazdır → PDF olarak kaydet** ile tek PDF gönderir. Kullanıcıdan maçları tek tek yazması, iki ayrı bahis marketi seçmesi veya ikinci bir oran sitesinden teyit etmesi istenmez.
2. Resmî İddaa PDF'si tek maç/odds kaynağı olarak **MS 1/X/2, KG Var/Yok, 2.5 Alt/Üst** olmak üzere yalnız yedi fiyatı içerir; 1.5 ve 3.5 marketleri rapora alınmaz. Metin, 14 PDF hücresinin yerinde kaldığı kontrol edilerek okunur, eksik fiyat kayıp marketin karşılaştırmasını etkiler.
3. Takım isimleri SHA-korumalı mevcut **215 takım** siciline bağlanır. Bilinmeyen veya kısaltılmış ad yüzünden başka maç durdurulmaz. Kapsam dışı kupa, U19 ve kadın ligleri ana 10 ligin skor modellerine karışmaz.
4. Lig/federasyon/kulübün **mevcut resmî fixture adapteri, maç başına bir çağrı** yapılır. Tek çağrı ev-deplasman, gün, saat ve henüz başlamamış maç kontrolünü yapar. Maçlarla ilgisiz başka odds kaynağına erişilmez. Bu sürüm lig başına tek HTTP çağrısı değil, **maç başına tek adapter çağrısı** uygular.
5. Tek seferde **mevcut B/C2/C3/M4** modelleri kabul edilmiş tarihsel verilerle çalışır. Tahmin SHA kilitlenir. Ardından **aynı geçmiş sonuç kesiminden as-of ampirik piyasa temel oranları** ayrı SHA ile hemen kaydedilir. Eski 96 pilot, ana M4 katsayıları, lig kapsamı veya LITE/basketbol depoları değiştirilmez.
6. Özgün kullanıcı PDF'si **yerel olarak bir kez tekrar okunup byte SHA ile** giriş JSON'una bağlanır (bu başka bahis kaynağından tekrar araştırma değildir). PDF zamanı < tahmin zamanı < karar zamanı < resmî maç başlama zamanı koşulu korunur. 24 saatten eski fiyat sadece arşivdir, değer seçiminde kullanılamaz.
7. **Donmuş Ağustos–Eylül kalibrasyonuyla aynı önceki değer karar formülü** kullanılmaya devam eder. Model desteği, pozitif geçmiş Brier skill, olasılık/temel oran farkı, marjsız piyasa farkı ve EV şartları geçerse **koşullu ana aday** ve ayrı aileden **koşullu alternatif** sunulur; geçmiyorsa **PAS**. PDF fiyatı kesinlikle canlı/T-60 fiyatı diye adlandırılmaz: `ARCHIVED_PDF_PRE_FORECAST`.
8. Siyah-beyaz, büyük okunaklı metinli, her maç çerçeveli PDF'de yedi oran + M4 ham %, piyasa marjsız %, fark ve imzalı **kalibre koşullu aday/alternatif/PAS** görüntülenir. Eski kullanıcı talimatına uygun 1.5/3.5 hiçbir satırda yoktur. Modül, sahte bir `frozen_policy_verified` boolean alanından tercih çıkarmaz.

## Uygulanan kodlar

- `iddaa_pdf_team_alias_preflight_263.py` — takım adları ve UUID
- `iddaa_pdf_bulletin_263.py` — kullanıcının gerçek Android/Chrome PDF sütunları ve SHA
- `iddaa_pdf_session_263.py` — tek resmi fixture denetimi; per-match dört model; modelden hemen sonra ampirik baseline SHA
- `iddaa_pdf_first_quote_263.py` — gerçek orijinal PDF SHA, fiyatın tahminden önce olması, sadece 7 market, 24h bayat fiyat PAS
- `four_model_value_policy_263.py` — **geriye uyumlu opsiyonel PDF-FIRST giriş**, eski normal karar formülünü veya varsayılan odds akışını değiştirmez
- `iddaa_pdf_value_bridge_263.py` — donmuş geliştirme kalibrasyonunu PDF-first SHA zinciriyle bağlar; tek satır sorununda diğer maçlar devam eder
- `iddaa_pdf_report_263.py` — sadece mühürlü karar/kalibrasyon verisinden siyah-beyaz, telefon okunur PDF
- **Tek komut:** `iddaa_pdf_one_step_263.py` — kullanıcı PDF'sinden çıktı PDF'sine tek oturum; dosyalar yerel, GitHub'a otomatik yükleme yok

## Tek komut: teknik çalıştırma

```bash
PYTHONPATH=.:experiments/263 python experiments/263/iddaa_pdf_one_step_263.py \
  --pdf "/path/to/user-iddaa.pdf" \
  --history data/results_only_263/2026-11-10_completed_4617_scores_only.csv \
  --source-baseline m4_quad_base/historical_results.csv \
  --source-acceptance data/results_only_263/4617_research_input_provenance.json \
  --m4-lock experiments/263/m4_lock.json \
  --dev-lock experiments/263/forward_dev_calibration_lock_263.json \
  --out-dir experiments/263/iddaa_pdf_sessions_263
```

Ön koşullar: mevcut `numpy`/`scipy`/`PyMuPDF`/`reportlab`; 4413 maçlık değişmez `m4_quad_base/historical_results.csv` (SHA `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`) GitHub sabah workflow'sunda olduğu gibi orijinal araştırma artifact'inden alınır. 4617'lik sonuç seti **research-only** veri kabul düzeyini aşmış gibi gösterilemez. User PDF'si GitHub repo içine otomatik gönderilmez.

Üretilenler: `bulletin.json`, `source_session.json`, `calibrated_session.json`, orijinal `iddaa_original_user.pdf`, ayrı SHA mühürlü dört model/baseline kayıtları, `futbol_263_iddaa_oranli_rapor.pdf`. Aynı PDF SHA ile oturum klasörü üzerine yazılmaz.

## Denetim / açık sınırlar

- **48/48 offline** test: PDF kolon/boşluk, alias, tek resmî adapter simülasyonu, SHA'lı tahmin ve empirical baseline bağlantısı, yanlış saat/isim, 24h fiyat, diğer bookmaker çağrısı yapmama, eski değer politika geriye uyumluluk, yasak 1.5/3.5, PAS veya koşullu ana tercih, gerçek PDF üretimi ve tek-komut bütünlük. https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43056590227
- Kullanıcının ilk 11 Kasım **3 sayfalık gerçek örnek PDF'si** on lig dışından 30 maç içeriyor; 28 satırın fiyat hücresi uygun biçimde okunuyor, 2 satır eksik sütun nedeniyle ayrı tutuluyor. Bu, gerçek kapsam ligi isimlerini onaylayan bir test değildir.
- 8 Kasım Pinnacle kayıtlarında (İddaa değil) 86 kulüp adı örneğiyle harici 20 isim farkı çözülmüş, 86/86 test edilmiştir; **İddaa özel adları için garanti** sayılamaz.
- **Kalan tek kabul:** 10 kapsam liginden maç içeren ilk gerçek İddaa PDF'sinde aynı toplu akışı canlı federasyon/lig adapteri, kabul edilmiş as-of veri, gerçek B/C2/C3/M4 ve PDF çıktısıyla bir kez uçtan uca sınamak. Bu aşamaya kadar canlıda yüzde yüz çalışıyor veya bahis avantajı kanıtlandı iddiası yoktur. Model ve oran fiyatı değişebilir; adaylar yalnız araştırma amaçlı koşulludur.

## Durum defteri

**Bitti:** PDF-first gerçek kaynak SHA bağlama, eski kalibre matematik kararı, 7 market, tek CLI girişi, Unicode PDF ve 48/48 araştırma testi.

**Açık:** İlk gerçek on lig İddaa PDF'siyle canlı saha kabulü. Yeni 96 pilot başlatmak, ikinci bahis fiyatı teyit etmek, eski M4'e test edilmemiş katsayı eklemek veya mevcut mühürleri değiştirmek YASAK.
