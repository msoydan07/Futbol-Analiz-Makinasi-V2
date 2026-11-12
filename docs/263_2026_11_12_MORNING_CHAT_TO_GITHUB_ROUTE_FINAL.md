# Futbol 2.6.3 — Sabah sohbet komutu → GitHub gerçek analiz hattı

12 Kasım 2026. Mevcut 2.6.3 deney dalı için tek komutluk güvenli on-demand çalışma düzeni. Main, M4, B/C2/C3, 4617 sonuç ve eski 40 SHA değiştirilmez.

## Denetim sonucu
- 8 Kasım yeni100 gerçek GitHub runs 42469245388 ve 42469487639 SUCCESS. Eski sistemde named GitHub istek → 10 lig resmî canlı named gate → B/C2/C3/M4 → append-only SHA → telefon Markdown ve PDF artefaktı çalışmış.
- 10 lig salt-okunur resmî preflight ve mevcut manuel seçim köprüsü zaten yazılıydı. Eksik olan, ChatGPT'nin bir talebi bu köprüye bağlayacağı kalıcı preflight kanıtı ve güvenli bütün-aday seçim planıydı.
- Eski GitHub Actions preflight raporu yalnız kısa süreli ZIP artefaktındaydı. Yeni workflow düzenlemesi yalnız user-request push'u için preflight_<runId>.json, .md ve _candidates_not_sealed.json dosyalarını experiments/263/sabah_preflight_results/YYYY-MM-DD/ dizinine sadece EKLER. Fikstür kaydını yeni pilot zannetmez.

## Talep geldiğinde tek akış
1. Kullanıcı aynı gün Bugünün maçlarını getir / Bugünün maçlarını analiz et dediğinde ChatGPT/GitHub bağlantısı bugün için yeni, tek bir experiments/263/sabah_preflight_requests/NAME.json dosyası oluşturup push eder. İçerik schema 263_TEN_LEAGUE_PREFLIGHT_REQUEST_V1 ve day_turkey TSİ bugünün tarihi. Talep yoksa kullanıcı adına hiçbir pilot başlatılmaz.
2. Mevcut 263-sabah-10lig-fixture-preflight.yml iş akışı bütün 10 resmî lig kaynağını kapsam sınırlamalarıyla birer kez inceler, başlangıç saati ve takım kimlikli adayları çıkarır, 0 oran ve 0 pilot ile kalıcı GitHub preflight raporu yazar. Başarılı workflow run ve rapor commit edilmeden pilot isteği yapılamaz.
3. Sabit planlayıcı sabah_chat_turn_router_263.py yalnız gerçekten bugünkü komut, 10 dakika içinde canlı alınmış kaynak adayları, resmî saat, kanonik takım ID ve mevcut SHA kimliklerini kabul eder. Başlamış veya GitHub kayıt süresine 20 dakika bile kalmamış maç yeni tahmine girmez. Dondurulmuş 100 kap dolarsa yeni pilot açmaz, sessizce maç atlamaz.
4. Plan güvenliyse ChatGPT/GitHub bağlantısı ayrı ikinci yeni sabah_requests/NAME.json dosyasını GitHub'a göndermelidir. GitHub Actions GITHUB_TOKEN ile yapılan bir push başka bir iş akışını otomatik tetiklemeyebilir: bu ikinci push asistanın GitHub bağlantısı üzerinden yapılmalıdır. Kod tek başına ChatGPT mesajını dinlemez ve git push yaptığını iddia etmez.
5. Mevcut 263-sabah-new100-on-request.yml iş akışı ikinci isteği canlı resmî named-match kapısından yeniden geçirir, dört model + SHA + cep telefonu Markdown/PDF + varsa tek seferlik lig Pinnacle analizi yapar. GitHub run, commit receipt ve PDF artefaktları gerçek başarıyla teyit edilmeden analiz tamamlandı denmez.
6. Arşive alınmış 8 Kasım 39 sonuç ve bir ertelenme yeniden araştırılmaz. Yeni sonuçlar önceki tek-seferlik maç-sonu kabul sözleşmesine göre bir kez arşivlenir.

## Sınırlar
- Bu aşama yeni günlük gerçek futbol maçı olmadığı gün pilot veya bahis fiyatı çağrısı yapmaz. Tüm kaynaklar için %100 fikstür kapsaması garanti edilmez, engeller açık gösterilir.
- new100 mevcut 100 mühürlük sınırlı pilot grubudur: 8 Kasım'daki 40 mühür kayıtlı, 60 kapasite kalmıştır. Sınır dolarsa otomatik yeni pilot açılmaz; sürdürülebilir read-only günlük analize ayrıca karar gerekir.
- Gerçek İddaa Chrome PDF saha kabulü ayrıca maç günü yapılacak; önceki sentetik PDF testi bunu yerine geçmez.
- GitHub'taki modül ChatGPT arka plan webhook'u değildir. Kullanıcı açık komut verdiğinde asistan GitHub eylemlerini gerçekten çağırmazsa bağlıymış gibi raporlayamaz; sonuçları kullanıcıya kendiliğinden ChatGPT dosyası olarak teslim ettiğini de iddia edemez.
