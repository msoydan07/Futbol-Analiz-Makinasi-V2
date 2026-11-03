# xG kaynak paylaşımı — güvenlik kabul kaydı (3 Kasım 2026)

**Durum: YENİ HAM ARTIFACT YOLU KAPATILDI / 18 ESKİ PUBLIC ARTIFACT 18/18 SİLİNDİ VE DOĞRULANDI / KAYNAK İZNİ ONAYLANMADI**

## Kanıtlanmış risk
Public `msoydan07/Futbol-Analiz-Makinasi-V2` deposundaki `feature/01-kimlikler` dalı `.github/workflows/understat-xg-pilot.yml` eski sürümde `data/understat_matches.csv`, `data/historical_verified_xg.csv` ve diğer kaynaklı maç düzeyi CSV'leri GitHub Actions artifact'e yüklemiştir. Run `41287280687`, artifact `13074948510` (`understat-xg-pilot`), 2026-11-03 itibarıyla hâlâ mevcut, beklenen son gün 2027-01-30. Kaynakta erişim olması yeniden dağıtım iznini kanıtlamaz.

## Uygulanan engeller
1. **Gerçek veri hattındaki iş akışı** `feature/01-kimlikler` üzerinde değiştirildi. Otomatik `push` tetikleyicisi kaldırıldı; yalnız manuel tetikleme tanımı tutuldu. `XG_SOURCE_PERMISSION_CONFIRMED=true` repository değişkeni mevcut değilse **veri çekmeden önce hata veriyor**. Bu değişkenin varlığı hukuken bağımsız izin kanıtı değildir; kullanıcı açık kaynak iznini teyit etmeden ayarlanmamalı.
2. `understat-xg-pilot` artık `actions/upload-artifact` ile **yalnız** `data/xg_public_aggregate_safe.json` yükler ve 7 gün tutar. Ham xG/satır URL'leri, eşleşme CSV'si, kaynak isimleri veya teşhis CSV'si artifact'e yüklenmez. `build_xg_public_summary_safe.py` sabit bir **pozitif alan listesi** kullanarak yalnız 5 lig x 2 sezon için sayıları ve toplamları verir. Sürpriz alanlar kaynak JSON'dan kopyalanmaz.
3. `.gitignore`, generated kaynak xG satırlarının yanlışlıkla GitHub commit'ine dahil edilmesine karşı ek bir önlemdir; önceki commitleri/artifact'leri geri almaz.
4. Bu koruma `feature/01-kimlikler` ve `experiment/263-toplu-karsilastirma` dallarında aynı dosyalarla bulunur; **main, C3/M4, pilot ve Avrupa mühürlü kayıtlar değişmedi.**
5. 7 yalnız sentetik sızıntı-kontrol testi yerelde başarılı. Geçmişte toplanmış xG artifact'in yalnız iki **agrega raporu** ile exporter doğrulaması: 2183 kaynak, 2155 eşleşmiş, 28 eşleşmeyen, 10 lig-sezon. Yeni sağlayıcı toplama/backtest yapılmadı.


## EK KANIT — 603 GitHub Actions çalışmasındaki 18 eski Understat paketi
3 Kasım 2026 tarihinde GitHub Actions geçmişinin 603 kaydı üzerinden `Understat xG kaynak ve eslesme piloti` adlı bütün **18 çalışmanın** artifact listesi ve ZIP dosya içi isimleri denetlendi. **18/18** artifact `understat_matches.csv` ham maç düzeyi Understat CSV içeriyor; **8/18** `historical_verified_xg.csv`; **14/18** `understat_xg_match_audit.csv` içeriyor. Hem başarılı hem hata veren çalışmalarda `if: always()` nedeniyle ham paket yaratılmış. Hepsi incelendiğinde `expired=false` durumundaydı.

| GitHub Actions run | Artifact ID | Ham Understat CSV |
|---:|---:|---|
| 41287280687 | 13074948510 | EVET |
| 41286983963 | 13075718244 | EVET |
| 41286723326 | 13075243767 | EVET |
| 41253655400 | 13062471987 | EVET |
| 41253416576 | 13062660850 | EVET |
| 41253154628 | 13061822391 | EVET |
| 41232858196 | 13054995409 | EVET |
| 41232670049 | 13054725747 | EVET |
| 41232016656 | 13053863596 | EVET |
| 41231332656 | 13053792841 | EVET |
| 41231326346 | 13053926883 | EVET |
| 41231267215 | 13053349126 | EVET |
| 41228495924 | 13052368606 | EVET |
| 41188440789 | 13037334050 | EVET |
| 41187868494 | 13037068906 | EVET |
| 41187334142 | 13036399839 | EVET |
| 41186809429 | 13037825135 | EVET |
| 41186244123 | 13035894311 | EVET |

**Kapsam:** Bu sayılar adı belirtilen `understat-xg-pilot` workflow'unun taranan artifact'leri içindir; tüm olası geçmiş workflow varyantlarının içeriği aynı şekilde doğrulanmış sayılamaz. Arşiv ZIP'leri bu rapora eklenmedi ve başka bir public artefakta yeniden yüklenmedi.

**Temizleme birimi tek dosya değil 18 artifact'tir.** Önce gerekli/izinli araştırma sürümünün erişim-kısıtlı ve kalıcı yedeği doğrulanmalı, ardından GitHub'da bu 18 artifact ayrı ayrı kaldırılmalı; en sonunda bütün run ID'leri yeniden sorgulanarak `artifacts: []` teyit edilmeli. Bu turn'de silme yapılmadı; silme GitHub UI veya yazma yetkili artifact API gerektirir. Başarısız Actions koşularının da paket bırakabildiği artık ayrıca kanıtlanmıştır.

## Eski artifact açık iş
- **Silinmedi.** GitHub Actions artifact silmesi geri alınamaz. Ayrıca izinli ve erişim kontrollü özel, kalıcı yedek bulunup bulunmadığı doğrulanmadı. Kullanıcının açık onayı ve güvenli kopya olmadan silme yapılmayacak.
- GitHub mevcut artifact: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41287280687
- Bundan sonraki tek operasyon: (1) kaynağın saklama/yayım izni netleşsin, (2) araştırma hakkı varsa arşiv özel depoda saklansın ve SHA doğrulansın, (3) public artifact GitHub arayüzünden silinsin, (4) tekrar sorgulanıp silme doğrulansın. GitHub resmi kılavuz: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/remove-workflow-artifacts
- `main` içindeki diğer xG işlemleri manuel tetiklemeyle hâlâ kaynak verisi alabilir; incelediğimiz upload listelerinde **ham xG** bulunmadı, fakat kullanım izni tamamlanana kadar manuel xG işleri başlatılmamalı.

## Sonraki aşama
Kaynak kullanma ve özel saklama izni doğrulanmadan **yeni gerçek xG snapshot veya M4+xG testi çalıştırılmayacak**. 289 geçmiş xG uygunluk adayındaki tarihsel sürüm belirsizliği aynen sürüyor. 100 maçlık B/C2/C3/M4 yeni yerel lig pilotu ve 3 Kasım UEFA M0/M0+Elo kayıtları etkilenmez.

**KAPANIŞ:** Yeni ham-xG Actions paylaşımı önlendi; eski public artifact hâlâ açık ve ayrı bir silme/koruma işlemi gerektiriyor.


## 3 Kasım 2026 — KESİN GÜVENLİK KAPANIŞI (önceki plan artık tamamlandı)

- Eski içerik listesi yalnız **silme öncesi tarihsel durumu** gösterir. Önceki açık risk notları artık güncel değildir.
- Önce **18 ZIP'i** birleştiren, her orijinal dosyanın SHA-256'sını içeren özel arşiv kullanıcıya ait ChatGPT dosya kütüphanesinde `Futbol-Analiz-Makinasi/ozel-xg-arsiv/M4_xG_18_legacy_artifacts_PRIVATE_BACKUP_20261103.zip` konumuna yüklendi. ZIP: 5.712.072 bayt, SHA-256 `bb786c4e84e240f6a8479cff264688de7c08f2c09be3ae944a29436a6a887189`. Kütüphaneden yeniden indirilip SHA karşılaştırması bire bir doğrulandı. Bu, bağımsız Understat lisansı veya tarihsel as-of kanıtı değildir.
- GitHub Actions [41718421285](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41718421285) **SUCCESS**: Önce 18 arşivin ID+run+adını kontrol etti, yalnız allowlist'teki 18 eski arşivi sildi, sonra her run'ın artifact listesinin boş olduğunu doğruladı.
- Aynı 18 run, bundan sonra GitHub GitHub connector üzerinden **ayrı salt-okunur sorgulamayla** yeniden denetlendi: **18/18 run artifact sayısı sıfır**. GitHub Actions koşu geçmişi ve eski model kodu silinmedi.
- Yalnız bir defa çalışan silme workflow dosyası, işlem sonrası araştırma dalından kaldırıldı; gelecekte yanlışlıkla yeniden tetiklenemez.
- `feature/01-kimlikler` ve `experiment/263-toplu-karsilastirma` üzerinde ham xG artifact yüklemesi durduruldu; sağlayıcı erişimi izinsiz otomatik başlamıyor. Main üzerindeki ayrı xG manuel analiz workflow'larında sağlayıcı kullanım izni hâlâ ayrıca denetlenmeli; izin netleşene kadar çalıştırılmayacak.
- Yeni xG testi, yeniden veri toplama, hiperparametre ayarı veya M4 terfisi **yapılmadı**. 100 maç yerel-lig pilotu ve Avrupa gölge kayıtları değişmedi.

**Güvenlik kararı:** Eski arşivlerin public yeniden dağıtım yüzeyi azaltıldı; verinin özel araştırma kopyası korundu. Bu, geçmişteki olası indirmeleri geri alamaz ve kaynak lisansını onaylamaz. xG modelini geliştirmeye devam etmek için as-of ve kaynak hakkı ayrı bir kabul koşulu olmaya devam eder.
