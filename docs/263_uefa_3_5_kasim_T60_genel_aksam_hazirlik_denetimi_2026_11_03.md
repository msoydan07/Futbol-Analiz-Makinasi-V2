# Futbol Maç Analiz Makinası 2.6.3 — 3–5 Kasım UEFA T−60 GENEL AKŞAM HAZIRLIK DENETİMİ

**Kontrol tarihi:** 3 Kasım 2026, TSİ 11.09–11.16 civarı.  
**Karar:** **GÖLGE T−60 KAYIT ALTYAPISI KOŞULLU HAZIR.** Akşam kullanılabilirlik için matematik/kimlik ve **GitHub canlı dış kaynak erişimi**, **deney dalına gerçek push** doğrulandı. **Gerçek ilk 11 doğrulaması ve gerçek tahmin kilitleme halen sadece maç önü penceresinde gerçekleştirilebilir.** Sonraki tarihli maçlarda canlı veri yeniden kontrol edilmeli.

## Kaynaklar ve bağımsız kanıt

| Konu | Bulgular | Kanıt |
|---|---|---|
| 17 UEFA maçı ve T−60 oturumları | 3/4/5 Kasım için 6 oturum: 6+6 ŞL ve 5 AL, güncel resmî UEFA fikstürleriyle uyumlu | https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/ ; https://www.uefa.com/uefaeuropaleague/news/02a8-2174cafa5bb6-82bbc20c9b92-1000--2026-27-europa-league-all-the-league-phase-fixtures-and-results/ |
| 17 maç 6 oturum kaynak/modül | Dondurulmuş, gerçek arşivlerle *yazma olmadan* başarılı altı oturumun tamamının provası; M0 ve deneysel M0+Elo | https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41597623905 |
| 9 canlı lig CSV kaynağı | **9/9 HTTP kaynak erişimi ve skor şema/alias kontrolü OK**. Eski **812 maç değişmedi**, çözümsüz kulüp adı 0; son lig skoru her ligde 2026-11-01 | https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41601413770 (artifact 13214841610) |
| beyondELO canlı rating | GitHub runner'dan GET başarılı; **34/34** mevcut kulüp eşleşti. 2026-11-03 board SHA daha önceki sağlam snapshot ile aynı. Kaynak kontrol zamanı 2026-11-03 08:11:22–36 UTC | Aynı run 41601413770 |
| GitHub Actions'in uzak branch'e yazması | **GERÇEK KAYIT OLMADAN** bot hesabı deney dalına harmless QA dosyası push etti. Commit **82e4bfe68984d3f09e3b7351925b52cb8395146b**, run **41601982358 SUCCESS** | https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41601982358 |
| main ve pilot | main SHA **11cdb67ba1935f183f454f1286b9350d2d8840d7** değişmedi; kayıt kontrolünde t60_requests/, t60_locked/, t60_lock_reports/ yok. 100 maç pilot etkilenmedi | GitHub branch ve recursive tree read |

## BULUNUP DÜZELTİLEN İKİ GERÇEK HATA

**1. Eski T−60 raporlarının sonraki oturumu bloke etmesi.**  
Önceki yayın workflow'u, `t60_lock_reports/*.json` içinden **yalnız bir rapor olması** şartını arıyordu. İlk slot kaydedildikten sonra ikinci (23:00) slot gelince ilk+ikinci rapor sayısı 2 olur, geçerli tahminin GitHub'a push edilmesi engellenirdi. Artık workflow'u tetikleyen **o anki request'in slot_key** raporunu iki ayrı onay noktasında seçiyor; mevcut önceki slot raporlarını yanlışlıkla hata saymıyor. İşlenen dosyaların sadece ilgili slotun alt klasöründen çıkmasını da doğruluyor.  
İlgili düzeltme: `.github/workflows/263-uefa-t60-shadow-lock-on-request.yml`, commit `873f2c7e01ca1644812da0b6ab51ddb14f79c7b2`; çoklu rapor hedefleme regressyon kontrolü run 41601982358.

**2. Gerçek oluşturma saati yerine erken giriş saatinin kayıt olarak yazılması.**  
`uefa_t60_shadow_lock_263.py` başlangıç anını hesap kaydı zamanı gibi yazıyordu, oysa sonrasında dokuz lig + Elo çekimi yapılmıştı. Artık **canlı kaynaklar ve hesaplama tamamlandıktan sonraki gerçek UTC kilit zamanı** yazılıyor; SHA yeni zamanla yeniden üretiliyor. Tüm gerçek yeni kayıtlar KO öncesi kontrol ediliyor, prova `write=False` olduğunda tarihsel benzetim bozulmuyor. Kaynak Elo gözlem zamanı da GET işleminden sonraki gerçek an. Commit `1238e5950918f9427113279d370f9be3a4567d63`.

## Akşam hâlâ dikkat edilmesi gerekenler

1. **Maç günü veri yenilemesi:** Öğlen erişim OK olması, 19:45/22:00 veya 4–5 Kasım'da aynı kalacağını garanti etmez. Gerçek workflow kaynakları yeniden çekecek; kaynak koparsa/güncel skor değişmişse güvenli biçimde duracak. Bugün görünür problem YOK.
2. **Resmî UEFA sayfası ve ilk 11:** Her slotta resmî tekil sayfa kullanıcı/yardımcı web tarafından tekrar görülmeli, URL ve gerçek UTC kontrolü yazılmalı. GitHub CI UEFA sayfasını bağımsız fetch ederek doğrulayamıyor; URL iddiası tek başına resmî veri doğrulaması değildir. İlk 11 yoksa `NOT_CONFIRMED`, **engelleyici değil** ve oyuncu uydurulmayacak. Kadro bilgisi gol λ'sında deneysel katsayıya dönüşmeyecek.
3. **Gerçek tahmin kilidi henüz hiç yaşanmadı:** Botun *zararsız yazma izni* onaylı; fakat gerçek T60 isteği üzerine tüm GitHub Actions veri yenileme→iki model→record SHA→commit zinciri henüz bir maçta çalışmadı. Başarılı CI + gerçek commit SHA görmeden "tahmin kaydedildi" söylenemez.
4. **Zaman ve kuyruk:** T−60 hedef, kodun geçerli penceresi **T−75 ile T−15**. İşlemler kuyrukta kalıp pencereyi kaçırırsa geçmişe dönük kayıt YOK. Uygulama kendi başına bir maç seçmiyor, ilgili slot için **tek yeni JSON isteği** gerekiyor. Deneysel zamanlanmış ChatGPT görevi etkin ancak sistem `next_run_time` vermedi; görevin kesin çalışacağını varsaymayın. Kullanıcının 19:45/22:00'de sohbete dönmesi pratik yedek.
5. **Model sınırları:** Şimdiki iki kol **M0 gol-only** ve **M0+Elo keşif modeli**. Uygulanan matematik denetlendi fakat canlı performans/kalibrasyon henüz kanıtlanmadı. xG, oyuncu etki katsayısı, oran/EV ve tam 2.6.3 piyasa karar katmanı burada devrede değil. Üretim motorları B/C2/C3/M4'e geçilmedi. **Yerel 100 maç pilotu = 0 etkilenme.**
6. **Kapsam:** Bu deneme yalnız **3–5 Kasım 17 maçlık 6 oturum**; otomatik tüm Avrupa fikstürüne genelleştirilmiş kalıcı üretim sistemi değildir. İngiltere Championship bu UEFA 17'li 9 üst-lig kulüp kapsamına girmiyor.

## 6 slot / Türkiye saatine göre

| Gün | T−60 | KO | Maç sayısı |
|---|---:|---:|---:|
| 3 Kasım | 19.45 | 20.45 | 1 |
| 3 Kasım | 22.00 | 23.00 | 5 |
| 4 Kasım | 19.45 | 20.45 | 1 |
| 4 Kasım | 22.00 | 23.00 | 5 |
| 5 Kasım | 19.45 | 20.45 | 2 |
| 5 Kasım | 22.00 | 23.00 | 3 |

**Kesin bitiş kararı:** Veri ve kimlik açısından bugün görünen kritik arıza yok. İki yapısal hata düzeltildi. Uzak GitHub bot push hakkı gerçekten test edildi. **Akşam gölge T−60 kayıt denenebilir**, ama resmî ilk 11, kaynak güncelliği ve gerçek tahmin commit'i için **koşullu** kabul devam eder. Yeni kaynak/kod değişikliği yoksa tekrar toplu prova çalıştırılmayacak; gerçek iş maç saatindeki kaynak kontrolü ve kilit olacak.
