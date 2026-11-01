# 2.6.3 Döngü kontrolü — xG ve Salı güncelleme kararı

## Kilitli kullanıcı kararı
- **Veri yenileme günü her Salı, Türkiye saat dilimi (Europe/Istanbul).** Önceki Çarşamba ifadesi artık kullanılmaz.
- Bu commit **GitHub Actions cron kurmaz veya çalıştırmaz**. Salı, operasyondaki güncelleme hedefidir; zamanlayıcının canlı çalıştığı ayrıca doğrulanmadıkça otomatik yenilendi denmez.
- Aynı fikstür kaynaklarını arama, matematik karşılaştırmalarını veya xG deneyini yeniden başlatma yok.

## Daha önce tamamlanmış gerçek xG deneyi
- GitHub Actions workflow run **41292163144**: job `verified-xg`, başarılı; artifact **13077519072**, 2026-11-01.
- Artifakt: `historical_verified_xg_report.json` = **2155** kayıt; `paired_xg_poisson_report.json` = **1549** eşleştirilmiş karşılaştırma (5 lig).
- xG lehine ortalama logloss farkı +0.003576 ancak 2026/27, 290 maçta **-0.010615**; blok-bootstrap %95 logloss fark aralığı **[-0.006465, +0.013838]**.
- **Karar aynı:** xG modelini sessizce kanonik C2, C3 veya mevcut B yerine geçirme. Bağımsız ileri doğrulama ve lisans koşulları olmadan bahis sinyali üretme.
- Bu artifakt **rapor içerir, ham `historical_verified_xg.csv` içermez**. xG kaydı bu çalışma sırasında mevcut sayılmaz.

## Kapatılan tek yeni boşluk
- `verified_xg_context_263.py`, mevcut `build_verified_xg_history.py` ile üretilmiş **ayrıca sağlanacak** doğrulanmış xG CSV ve eski kabul raporunu 4.413 maçlık değişmez tarihsel kayıtla fixture ID / lig / sezon / tarih / takım / skor düzeyinde doğrular. Bu **dosya içi bütünlük kanıtıdır**, Understat'ın bugün yeniden canlı kontrol edildiği anlamına gelmez.
- `operational_report_263.py` çağrısına `--verified-xg PATH --xg-audit PATH` isteğe bağlı parametreleri eklenir. **İkisi birlikte gerekli**. Yoksa açıkça `AUDITED_XG_FILE_NOT_PROVIDED` çıkar.
- Kullanılabilir kayıtlardan yalnızca `match_date < target_date` olanlar alınır. Ev için son beş iç saha, deplasman için son beş dış saha xG atılan/yenen **betimsel** istatistiklerini verir.
- xG, λ ve model seçimini **değiştirmez**; eski model performansları yeniden hesaplanmaz; pilot, oran/EV veya gerçek tahmin kaydı başlamaz.
- İzin belirsizliği nedeniyle gerçek ham xG CSV **public GitHub'a yüklenmez**; yalnız kod ve sentetik testler paylaşılır.

## Önemli sınır
- Salı günü güncelleme için var olan haftalık veri hattı çıktısına (`historical_results.csv`, `historical_results_audit.json`, `source_audit.csv`) ihtiyaç var. Canlı veri bağlantısı yeni kanıt olmadan `ACTIVE` diye etiketlenmez.
- İleride gerçek bir maç istendiğinde maçkolik isimleri ayrı on-demand kimlik/doğrulama katmanında incelenir; bu offline rapor kendi başına maçın varlığını onaylamaz.
