# 751 maç adayı — özel bilgisayarda veri kasası

**14 Kasım 2026; son maç kesim günü 13 Kasım 2026.** Sadece veri; model, matematik, M4, mühürler ve manuel xG dosyası değişmez.

## Neden bu yol?

[Football Charts'ın 9 Kasım 2026'da güncellenen şartları](https://www.football-charts.com/terms) ücretsiz API için **kişisel kullanım, araştırma, öğrenme ve özel projelere izin verir**. Ham API dosyalarını veya bunların büyük parçalarını başkalarına dataset olarak dağıtmak/yayımlamak ise yasaktır; bundan ayrı, kullanıcının kendi özel araştırması ve türetilmiş sonuçları mümkündür. Başkalarının kullandığı bir bot, web sitesi veya servis için Commercial plan gereklidir. Bu bir hukuki görüş değildir.

Herkese açık GitHub'da **yalnız açık kaynak kodu** kalır, **özel maç sonuçları değil**.

## Araç

[build_751_PRIVATE_LOCAL_ONLY_score_vault_20261114.py](./build_751_PRIVATE_LOCAL_ONLY_score_vault_20261114.py) adlı kodu **kullanıcının kendi Windows bilgisayarında**, ilgili araştırma dalından indirdikten sonra çalıştırmak mümkündür.

Tek seferde en fazla **9 ücretsiz API sonucu isteği** yapar:
- Beş güncel lig: ENG5 190, ESP2 141, ITA2 110, FRA2 108, DNK1 84 = **633**.
- Diğer dört ligde önceden var olan 176 sonucu **tarih–kanonik takım–FT** ile eşler; üstlerine yazmaz. Ek kaynak adayları SCO1 33, CHE1 21, GRE1 34, AUT1 30 = **118**.
- Toplam tam **751** sonuçlu kaynak adayı oluşmazsa; eski maçın skoru uyuşmazsa; tarih/kulüp/sonuç hatalıysa **hiçbir dosya yazmaz**.
- Ham kaynak dosyası **kesinlikle GitHub deposunun içine yazılmaz**; yalnız bilgisayarın kullanıcı ev dizinine yazılır.

**Özel klasör:** Windows'ta %USERPROFILE%\Futbol-Analiz-Ozel-Veri

Özel JSONL dosyası: 2026-27_to_2026-11-13_source_scores_QUARANTINE_PRIVATE.jsonl

Küçük doğrulama/özet dosyası: 2026-27_to_2026-11-13_source_scores_QUARANTINE_PRIVATE_SUMMARY.json

## Bilgisayar başında nasıl çalıştırılır?

Python 3.10+ yüklü ve GitHub araştırma dalındaki depo bilgisayarda açıkken, **depo kökünde PowerShell** aç:

~~~powershell
py experiments/263/league_expansion/build_751_PRIVATE_LOCAL_ONLY_score_vault_20261114.py --self-test
py experiments/263/league_expansion/build_751_PRIVATE_LOCAL_ONLY_score_vault_20261114.py --build-private
~~~

İlk komut **internete çıkmaz**; veri toplamaz, yalnız güvenlik kurallarını test eder. İkinci komut **sen çalıştırdığında** internette en fazla dokuz kişisel araştırma isteği yapar. Zaten dosya varsa **yeniden istemez veya üzerine yazmaz**. Siteye istek limiti/erişim hatası olursa ve 751 sayısı tam çıkmazsa **eksik dosya üretmez**.

**Önemli:** Bu komutları bu sohbetten çalıştırıp kullanıcının bilgisayarına gizlice dosya indirildiği iddia edilemez. GitHub Actions'ta sadece **offline test** yapılır. Canlı özel veri, kullanıcı kendi bilgisayarında komutu çalıştırana kadar oluşturulmuş değildir.

## Hangi verileri hâlâ kullanmıyoruz?

- 751 adayı **bağımsız resmî maç doğrulaması** tamamlanmadan eğitim amaçlı kullanmıyoruz. Kaynak tek başına federasyon kanıtı değildir; 0–0 yanlış tamamlanmış, ertelenmiş, hükmen veya terk edilmiş olaylar çıkabilir.
- Ham dosyayı **ChatGPT'ye / GitHub'a / paylaşılan bir klasöre / başkasına yüklemiyoruz**. Kendi bilgisayarında kişisel araştırmaya ayrılmalı.
- Bu sadece **maç skorlarıdır, xG değildir**. 1.855 maçlık manuel xG giriş dosyası ayrıca kalır.
- Maç bitiş skoru **o maçın maç öncesinde bilinen özellik değeri değildir**. Gerçek maç önü yayın zamanını kanıtlamadan matematik/model eğitimine geçmeyiz.
- Ana 4.617 sonuç, araştırmadaki 4.843 kaynak satırı, 200 eski hatalı skor/tarih düzeltmesi ve 96 mühürlü pilot aynen kalır.

## Kalite denetimi ve yetki sınırı

[Offline GitHub Actions PASS](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43636085241) — 9 liglik kapsam, 633+118 toplamı, eski maç çakışması kontrolü, kişisel dizin zorlaması ve FT uyuşmazlığında durma testi geçti.

**Bu test 751 özel maçın gerçekten kullanıcının bilgisayarına indirildiğini göstermez.** Sadece kodun test edildiğini gösterir. Kayıtların son bağımsız doğrulama ve kaynak hakları ayrı veri işi olarak devam eder.

### Ertesi gün xG girerken görsel kaynak uyarısı

Bazı xG sitelerinde **Projected xG (maç önü tahmini)** ile **Produced xG (maç sonrasında üretilen)** aynı sayfada görünür. Örneğin [31 Ekim 2026 Cambuur–Go Ahead Eagles](https://xg-edge.com/eredivisie/sc-cambuur-vs-go-ahead-eagles-2026-10-31) için üretilen gerçek xG **1,83 / 0,63**; maç önü tahmini **1,77 / 1,45**. LibreOffice'e sadece **Produced / maç sonrası gerçekleşen xG** girilmeli; eski xG sütununa dokunulmamalı. xG'nin olmadığı maçta boş bırakılmalı, sıfır uydurulmamalı.
