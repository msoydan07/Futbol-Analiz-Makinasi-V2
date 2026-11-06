# 2.6.3 — Sabah rejimi uygulama sözleşmesi ve değişiklik haritası (2026-11-07)

Durum: **DENETİM / UYGULAMA BEKLİYOR**. Bu belge kodun sabah rejimine geçirildiği veya kabul testinin geçtiği anlamına gelmez. Ana dal, mevcut tahminler, 96 kohortu ve kalibrasyon kilidi değiştirilmez.

## Okunarak doğrulanan mevcut engeller
- `.github/workflows/263-quad-forward-on-request.yml`: yalnız yeni `quad_requests/*.json` eklemelerinde çalışır; en fazla 12 maçlık manifest; T−60 iş akışı ve Pinnacle aynı-job adımı sürüyor.
- `experiments/263/run_quad_requested_batch.py`: istek başına en fazla 12 maç; aynı fikstür için önceden mühürlü kaydı koruyor; resmî fikstür kapısı mevcut.
- `experiments/263/pinnacle_forward_join_263.py`: `20 <= minutes_to_ko <= 90` ve en fazla 10 dakikalık tahmin-fiyat yaşı; sabah için doğrudan kullanılamaz. Kalıcı gün/lig snapshot cache yok.
- `experiments/263/free_bulk_odds_263.py`: lig başına tek h2h/Pinnacle çağrısını destekleyen temel fonksiyon mevcut, ancak kalıcı, yarış koşullarına dayanıklı günlük sorgu kilidi ayrıca gerekiyor.
- `experiments/263/four_model_value_policy_263.py`: B/C2/C3/M4 ayrı; karar için DEV-kilitli M4/C3 kullanımı ve PAS/alternatif mantığı mevcut. Formüllere, DEV kilidine dokunulmayacak.
- `experiments/263/quad_user_report_263.py`: mevcut tekli ve çoklu rapor üretimi var; sabah/rotasyon/bağımsız Pinnacle görünümü için salt-okunur uyarlama gerekiyor.

## Dondurulacak yeni şemalar
1. `SABAH_TOPLU_V1`: TSİ günü, analiz UTC kesimi, resmî fixture id, model ve forecast SHA, 96-eski / yeni-100 ayrı cohort id, engel ve veri tazeliği.
2. `SABAH_PINNACLE_SNAPSHOT_V1`: (TSİ günü, lig, pinnacle, h2h, sürüm) benzersiz anahtar; API isteğinden **önce** dayanıklı rezervasyon, atomik/append-only sonuç, hata durumunda da tekrar-deneme politikası; gözlem/market UTC, event id, ev-deplasman, kickoff, H/D/A, SHA, kota header.
3. `ROTASYON_BILGI_V1`: her takım geçmiş 7/gelecek 10 gün; doğrulanmış kaynak ve UTC; dört niteliksel risk statüsü; model olasılıklarına etki etmez.
4. `TOPLU_RAPOR_V1` ve `TEKLI_RAPOR_V1`: aynı mühürlü forecast ve karar SHA'sını okur; telefon özeti + tam 17 bölüm; açarken API/model yeniden çağrılmaz.
5. `POSTMATCH_SCORE_V1`: tahmine dokunmadan ayrı sonuç dosyası; aynı N üzerinde B/C2/C3/M4/Pinnacle 1X2 Brier ve log-loss; KG/gol yalnız modellerde; PAS, kapsama ve eksikler.

## Birlikte hazırlanacak dosya grupları
- Yeni sabah batch giriş noktası ve GitHub workflow: 12-maç sınırını sabahın tüm maçları için güvenli batch parçalama ile ele al; kickoff öncesi commit doğrulaması; aynı maçın ikinci yazımını engelle.
- Fikstür ve rotasyon bilgi katmanı: mevcut resmî adaptörleri yeniden kullan; doğrulanamayanı açıkça bloke et.
- Pinnacle günlük lig cache/lock: önce offline sahte API ile tek çağrı, eşzamanlı istek, ikinci istek 0 kredi, 401/403/429, eski fiyat ve yanlış event testleri.
- Karar ve rapor adaptörleri: kalibrasyon kilidini değiştirmeden salt-okunur mobil çıktı.
- Sonuç eşleştirici: önceden mühürlü kayıtları salt-okunur değerlendir.
- Tek offline kabul matrisi ve tek rapor: geçişin bütün bileşenleri tamamlanınca; eski 24 testin kör tekrarı yok.

## Kabul ön koşulları
- Eski dört mühürlü kayıt ve 96 adaylık sabit kohort için hiçbir overwrite yok.
- `main` değişmez. Canlı API kredisi offline kabul için harcanmaz.
- 7–8 Kasım maçları geçmişe dönük sabah tahmini sayılmaz; ilk canlı yeni sabah pilotu ancak resmî doğrulama, kod ve test tamamlandıktan sonra.
- Yeni sabah sistemi doğrulanmadan T−60 otomasyonları kapatılmaz.
- Yeşil CI sonucu bahis başarısı olarak yorumlanmaz.

Sıradaki eylem: Bu haritayı temel alarak tüm kod değişikliklerini birlikte hazırlamak ve **bir** offline kabul testi çalıştırmak.