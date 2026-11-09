# 2.6.3 — Sabah SHA -> güvenilir maç sonu değerlendirmesi: teknik bağlantı

9 Kasım 2026 • deney dalı • `main`, M4 ve LITE değiştirilmedi.

## Kalıcı gerçeklik ve veri sınıfı
- Sabah fixtür kapısı ve B/C2/C3/M4 sonuçları geçmişte 8 Kasım'da 40 kayıt için çalıştı ve Git SHA ile kalıcı saklandı. Bu kayıtların içerikleri değiştirilmedi.
- Maç sonu `sabah_postmatch_new100_263.py` **yalnızca gerçek insan teyitli resmi sonuç JSON'larını** değerlendirir ve kaynak kabul dosyası olmadan 0 resmî sonuç gösterebilir. Bu kural **korunuyor**.
- Yeni `postmatch_csv_bridge_263.py`: 2026/27 sezonu için 10 ligin **ücretsiz** football-data.co.uk CSV'lerini salt okunur indirir; maç tarihini, takım kimliğini sadece daha önce doğrulanmış ad eşlemelerini kullanarak ve SHA ile eşler. Tam zaman sonucu yoksa, iki maç çakışırsa, skor-FTR çelişirse veya canlı kaynak ulaşılamazsa kaydı **bekletir**.
- 8 Kasım'ın önceden webden araştırılmış maç sonuçları ile harici CSV skoru aynıysa ikinci araştırma kanıt sınıfı `TWO_SOURCE_RESEARCH_CONCORDANT_NOT_OFFICIAL` olur. Aksi halde `WEB_REVIEW_CONFLICT`, skorlanmaz. Sadece CSV ile bulunan kayıt `CSV_ONLY_PROVISIONAL` statüsündedir.
- Dış CSV, federasyonun resmî sonucu değildir. Bu katman **0 bağımsız federasyon doğrulaması**, **0 insan teyidi** üretir. Resmî statü için mevcut ayrı resmî sonuç kaydı ve yetkili inceleme gereklidir.
- Model ve bahis pazarları aynı kalır. Oran API çağrısı ve Pinnacle kredisi **0**. Yanlış skor eğitim verisine girmez.

## Çalışma zinciri
1. Önceden mühürlü `forward_morning_263/YYYY-MM-DD/*.json` kayıtları (B/C2/C3/M4) ve kaydedilmiş sabah batch kimliği okunur.
2. Kaynak CSV'de açık `FTHG/FTAG/FTR` görülür, kimlik + tarih eşleşir, maç bitişinden en az 90 dakika geçmiş olur.
3. Yalnızca eşleşen tahminlerin MS, KG, 1.5/2.5/3.5 Alt-Üst Brier/log-loss ve isabeti **geçici araştırma** olarak hesaplanır.
4. GitHub `263-postmatch-csv-bridge-readonly.yml` yeni mühür veya dosya güncellemesinde otomatik devreye girer. Çıktı GitHub Actions artefaktıdır; hiçbir tahmin/sonuç/kalibrasyon dosyası overwrite yapılmaz.
5. İnsan tarafından resmî sayfada skor kontrol edilerek ayrı `sabah_postmatch_inputs` içine düzgün kanıt yazılırsa **mevcut** `263-sabah-new100-postmatch-readonly.yml` otomatik hesaplar. Resmî kanıt dosyası olmadan resmî pilot başarı sayısı arttırılmaz.

## 9 Kasım gerçek sistem çıktısı
- Kaydedilmiş 8 Kasım new100 SHA mührü: **40**.
- Bağımsız futbol sonuç CSV'si ve daha önce web üzerinden araştırılmış skorların karşılıklı aynı olduğu: **38**. Bu **federasyon teyidi** ve yeni `sabah_postmatch_inputs` resmî kabulü değildir.
- Bekleyen 2: **Estoril–Marítimo** (web araştırmasında ertelendi) ve **Çorum FK–Fenerbahçe** (dış CSV'de aynı gün/takım kimliğiyle sonuç bulunamadı). Eksik CSV kaydı tahminin yanlış olduğu anlamına gelmez.
- İki kaynak üzerinden bu 38 maç için ham M4 MS yön isabeti: **24/38**, MS Brier **0,513266**, KG yön **20/38**, 2,5 Alt/Üst yön **20/38**.
- Başarılı gerçek kaynak/kimlik/sınama koşusu: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42607309702
- **6 sentetik + gerçek SHA bağlama testi PASS**, 9 lig CSV'si indirildi (ENG2'nin o gün yeni100 mührü olmadığından kaynak sorgusu yapılmadı), güvenli dış yönlendirme kuralı uygulandı.
- Her gün yalnız bir defa GitHub'a `experiments/263/postmatch_refresh_requests/YYYY-MM-DD.json` adlı, **model veya odds çalıştırmayan** bir yenileme işareti yazılabilir. Bu işaret salt-okunur sonucu tekrar kontrol etmeye zorlar. 9 Kasım işaretinin giriş/Actions kabulü **gerçekten PASS**: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42607872712
- Günlük sonuç izlemesi için ayrıca ChatGPT `2.6.3 Maç Sonu Kontrolü` otomasyonu aktifleştirildi: 10:00 TSİ civarında kaynak kontrolü ve (GitHub yetkisi varsa) bu işareti ekleme, yalnız yeni sonuç/engel varsa bildirim. İzin yoksa başarı ilan etmez. Mevcut Cuma–Pazar analiz otomasyonu değiştirilmedi.
- GitHub `schedule` varsayılan dalda çalıştığı için, deney dalına doğrudan cron varmış gibi iddia edilmez. Ayrı ChatGPT otomasyonu üzerinden işaretleyici tercih edildi; bu otomasyonun **gelecekteki** GitHub yazma hakkı ilk gerçek ertesi gün çalışmasında ayrıca gözlenebilir.

## Son kullanım kararı
Mevcut M4 ana motoru **değişmedi**; B/C2/C3 yardımcı kalır. Artık günlük yeni maç önü tahminleri yazıldığında ve dış CSV'de güvenli eşleşme bulunduğunda skor ön değerlendirmesi otomatik çalışabilir. **Resmî insan/federasyon kabulü ayrı sonuç hattıdır** ve kaynaksız skorlarla doldurulmaz. Bu gerçek bir operasyonel ilerlemedir; bahis değeri veya %100 kaynak doğruluğu iddiası değildir.
