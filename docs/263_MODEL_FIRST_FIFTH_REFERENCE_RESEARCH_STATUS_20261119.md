# 2.6.3 — Model önce, oran yalnız beşinci referans (19 Kasım 2026)

**Kaynak karar:** [D-MARKET-006](263_KARAR_DEFTERI_TEK_GECERLI_KAYNAK.md). Bu belge yeni bir bahis politikası veya model terfisi değildir; önceden alınan kararın araştırma kodundaki gerçekleşme durumu kaydıdır.

## Kesin davranış
- Sabah **ilk iddaa PDF** ile aynı maçın B/C2/C3/M4 matematiksel tahminleri hesaplanır; bu hesaplar piyasa fiyatlarını **hiç girdi olarak almaz**.
- Eylül 2026 seçimiyle önceden donmuş, **Ağustos'ta öğrenilmiş M4 ortak Poisson kalibrasyonu** MS, KG, 2.5 için model-içi araştırma referansıdır. Bu durum B/C2/C3'ün başka bir gün kanıtla üstün gelemeyeceği anlamına gelmez.
- Model olasılığı, ligdeki tarihsel sıklık ve diğer mevcut modellerin desteğiyle **ana tercih / en çok bir farklı aile alternatifi / gerekçeli PAS** üretilir; model/kimlik/SHA eksikse **TEKNİK ENGEL** döner.
- İddaa PDF fiyatları **yalnız MARKET/beşinci referans** olarak modelden ayrı SHA'ya bağlanır. Piyasa yüzdeleri, farklar ve fiyat hareketi ana tercihi, yüzdeyi veya model PAS kararını değiştiremez.
- İlk 11 sonrası **ikinci iddaa PDF** yalnız fiyat değişimini ve kaynaklı futbol açıklamasını ayrı kaydeder; yeni model hesabı veya ikinci mühür yoktur.

## GitHub'da yazılı ve ayrı duran araştırma yolu

1. `experiments/263/model_first_decision_263.py` — saf model seçimi; fiyat argümanı yok; SHA, tarih, baseline, M4 ve kalibrasyon kontrolü; `market_reference` ayrı fonksiyon.
2. `experiments/263/model_first_selection_lock_263.json` — Ağustos 2026 ortak Poisson kalibrasyonu, Eylül aile modeli seçimi ve önceden sabitlenmiş deneysel eşikler.
3. `experiments/263/model_first_iddaa_bridge_263.py` — orijinal PDF byte SHA + resmî fikstür ile mühürlenmiş model tahmini/baseline'ı eşleştirir. İddaa marjsız piyasası yalnız ayrı karşılaştırma SHA'sıdır.
4. `experiments/263/iddaa_pdf_model_first_one_step_263.py` — eski oranla tercih yapan girişi **silmeden**, yeni bağımsız PDF-first yolu. Ayrı oturum dizininde çalışır. İkinci PDF yorum modülü sabah imzasını aynı şekilde tüketebilir.
5. `experiments/263/iddaa_pdf_report_263.py` — yeni araştırma alanı varsa, model tercihini bağımsız gösterir; tarihsel eski raporları değiştirmez.
6. `experiments/263/test_model_first_decision_263.py` (16 sentetik kontrol), `test_model_first_iddaa_bridge_263.py` (5 entegrasyon sözleşmesi) ve `.github/workflows/263-model-first-odds-independent-ci.yml`.

**Doğrulama sınırı:** 16 karar birimi **yerel ortamda** geçti. 5 PDF köprü testi GitHub araştırma dalında yazıldı; **GitHub Actions'ın başarı sonucu bu kayıt oluşturulurken bağımsız teyit edilmedi**. Gerçek iddaa PDF'si/lig maçıyla saha kabulü de henüz yapılmadı. Eski fiyat-odaklı `four_model_value_policy_263.py` hâlâ var ve eski rotada kullanılabilir: yeni rotanın varlığı eski iş akışını sihirli biçimde değiştirmez.

## 496 maçlık geçmiş örneklem — araştırma uyarısı

Önceki B/C2/C3/M4 tahminlerini salt-okunur yeniden oynatma (2026-10-01 — 2026-11-08, 10 lig):

| Denetim | Sonuç |
|---|---:|
| Uyumlu, M4'ü bulunan maç | 496 |
| İlk ana aday | 286 |
| Model koşullarıyla PAS | 210 |
| Ana adayların ortalama hesaplanmış olasılığı | %69,53 |
| Ana aday gerçekleşme oranı | %62,59 |

**Yorum:** Pazar seçimi sonrası olasılıkların güvenilirliği yeterli değil. Bu yaklaşık **6,94 yüzde puanlık fazla güven** ne kadarının örnekleme gürültüsü olduğu bağımsız veride görülmelidir. Bu eski tarihler ve karşılaştırma sonuçları daha önce farklı deneylerde incelendi; **yeni kör test, yeni pilot veya kâr kanıtı değildir**. Özellikle 2.5 Alt adaylarının performansı şüphelidir; sonuç görerek sonradan eşik ayarı yapmak yerine üretime terfi BLOKE edilmiştir.

## Maç sabahı hazır bulunma engelleri — değişmedi
- **P0:** Mevcut sabah akışı 4.413/4.617 eski sonuç kaynaklarını pinliyor; özel ve kabul edilmiş 4.618 maçlık as-of veri bağlantısı, kaynak/vintage/onay kontrolüyle henüz canlıya taşınmadı. Özel ham xG GitHub'a yüklenmeyecek.
- **P0:** `MAX_DATA_AGE_DAYS=10` millî maç arası gibi takvim boşluklarında false-stale engeli verebilir. Resmî bitmiş maç kontrolüyle güncellik düzeltilecek, kontrol bütünüyle kaldırılmayacak.
- **P0:** Gerçek kapsam ligi kullanıcının ilk iddaa PDF'si -> resmî fikstür -> tek matematik mührü -> model-only karar -> beşinci piyasa referansı -> telefon PDF'si -> 2. PDF yorum eki tam zinciri henüz saha onayına sahip değil.
- **P1:** Yeni model-içi seçim kuralı 496 maçta olasılık açısından fazla güven verdi; geçmiş tek dönemli tuning yerine zamanlı yeni kanıtla kalibrasyon kabul edilmeli.
- **P1:** Eski operasyon `experiment/263-toplu-karsilastirma` dalı ve otomasyonları bu yeni research model-first yoluna geçirilmedi. Bu, bilinçli geri uyumluluk ve güvenlik sınırıdır.

**Durum:** (A) Karar kilitli, (B) Araştırma kodu GitHub'da, (C) Gerçek maç günü kabulü **YOK**. Ana M4, 2.6.3 canlı model, eski 96 pilot, mühürlü maç tahminleri ve otomasyonlar değişmedi.
