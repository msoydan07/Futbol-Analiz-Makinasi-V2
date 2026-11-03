# xG kaynak paylaşımı — güvenlik kabul kaydı (3 Kasım 2026)

**Durum: YENİ HAM ARTIFACT YOLU KAPATILDI / ESKİ PUBLIC ARTIFACT HÂLÂ AÇIK / KAYNAK İZNİ ONAYLANMADI**

## Kanıtlanmış risk
Public `msoydan07/Futbol-Analiz-Makinasi-V2` deposundaki `feature/01-kimlikler` dalı `.github/workflows/understat-xg-pilot.yml` eski sürümde `data/understat_matches.csv`, `data/historical_verified_xg.csv` ve diğer kaynaklı maç düzeyi CSV'leri GitHub Actions artifact'e yüklemiştir. Run `41287280687`, artifact `13074948510` (`understat-xg-pilot`), 2026-11-03 itibarıyla hâlâ mevcut, beklenen son gün 2027-01-30. Kaynakta erişim olması yeniden dağıtım iznini kanıtlamaz.

## Uygulanan engeller
1. **Gerçek veri hattındaki iş akışı** `feature/01-kimlikler` üzerinde değiştirildi. Otomatik `push` tetikleyicisi kaldırıldı; yalnız manuel tetikleme tanımı tutuldu. `XG_SOURCE_PERMISSION_CONFIRMED=true` repository değişkeni mevcut değilse **veri çekmeden önce hata veriyor**. Bu değişkenin varlığı hukuken bağımsız izin kanıtı değildir; kullanıcı açık kaynak iznini teyit etmeden ayarlanmamalı.
2. `understat-xg-pilot` artık `actions/upload-artifact` ile **yalnız** `data/xg_public_aggregate_safe.json` yükler ve 7 gün tutar. Ham xG/satır URL'leri, eşleşme CSV'si, kaynak isimleri veya teşhis CSV'si artifact'e yüklenmez. `build_xg_public_summary_safe.py` sabit bir **pozitif alan listesi** kullanarak yalnız 5 lig x 2 sezon için sayıları ve toplamları verir. Sürpriz alanlar kaynak JSON'dan kopyalanmaz.
3. `.gitignore`, generated kaynak xG satırlarının yanlışlıkla GitHub commit'ine dahil edilmesine karşı ek bir önlemdir; önceki commitleri/artifact'leri geri almaz.
4. Bu koruma `feature/01-kimlikler` ve `experiment/263-toplu-karsilastirma` dallarında aynı dosyalarla bulunur; **main, C3/M4, pilot ve Avrupa mühürlü kayıtlar değişmedi.**
5. 7 yalnız sentetik sızıntı-kontrol testi yerelde başarılı. Geçmişte toplanmış xG artifact'in yalnız iki **agrega raporu** ile exporter doğrulaması: 2183 kaynak, 2155 eşleşmiş, 28 eşleşmeyen, 10 lig-sezon. Yeni sağlayıcı toplama/backtest yapılmadı.

## Eski artifact açık iş
- **Silinmedi.** GitHub Actions artifact silmesi geri alınamaz. Ayrıca izinli ve erişim kontrollü özel, kalıcı yedek bulunup bulunmadığı doğrulanmadı. Kullanıcının açık onayı ve güvenli kopya olmadan silme yapılmayacak.
- GitHub mevcut artifact: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41287280687
- Bundan sonraki tek operasyon: (1) kaynağın saklama/yayım izni netleşsin, (2) araştırma hakkı varsa arşiv özel depoda saklansın ve SHA doğrulansın, (3) public artifact GitHub arayüzünden silinsin, (4) tekrar sorgulanıp silme doğrulansın. GitHub resmi kılavuz: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/remove-workflow-artifacts
- `main` içindeki diğer xG işlemleri manuel tetiklemeyle hâlâ kaynak verisi alabilir; incelediğimiz upload listelerinde **ham xG** bulunmadı, fakat kullanım izni tamamlanana kadar manuel xG işleri başlatılmamalı.

## Sonraki aşama
Kaynak kullanma ve özel saklama izni doğrulanmadan **yeni gerçek xG snapshot veya M4+xG testi çalıştırılmayacak**. 289 geçmiş xG uygunluk adayındaki tarihsel sürüm belirsizliği aynen sürüyor. 100 maçlık B/C2/C3/M4 yeni yerel lig pilotu ve 3 Kasım UEFA M0/M0+Elo kayıtları etkilenmez.

**KAPANIŞ:** Yeni ham-xG Actions paylaşımı önlendi; eski public artifact hâlâ açık ve ayrı bir silme/koruma işlemi gerektiriyor.
