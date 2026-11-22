# 22 Kasım 2026 — Kullanıcı PDF fikstürü / resmî lookup ayrımı ve model fallback'i

## Kullanıcının doğru uyarısı
- Kullanıcı 8 ligden 25 maçın orijinal iddaa PDF'lerini gönderdi. Tek maç veya küme resmi fikstür lookup başarısızsa bunu **ana modelin matematik üretememesi** diye raporlamak yanlıştı.
- Gözlenen gerçek durum: Standart `analyze_named_match_gate.py` 25 girişin 16'sını resmi eşleştirme/isim kontrolünde reddetti; M4/C3'e **girmemişti**. O kapı çıkışı `OFFICIAL_FIXTURE_GATE_BLOCKED`, hesaplama hatası değildir.
- Kullanıcı PDF'si maç/lig/saat ve görünen iddaa oranları için kaynak delilidir, ama ayrı federasyon kaynağının doğrulama sonucunu otomatik doğrulamaz.

## İzole araştırma çözümü
- `nov22_eight_pdf_model_first_from_user_bulletin.py`: İlk PDF'deki maç/başlama saatlerini kullanarak **resmi kapıyı doğru biçimde 'verified' diye taklit etmeden**, ayrı kaynak türü `USER_IDDAA_PDF_TRANSCRIPTION_NOT_OFFICIAL_FEDERATION_PROOF` ile geçmişin SHA-checked 4617 skoru, takımların kayıtlı ID'si, tazelik denetimi ve mevcut B/C2/C3/M4 fitleri, M4-MS ve C3-2025/26 v4 kalibrasyonuyla araştırma tahmini hesaplar.
- Maç başlangıcından önce hesaplama şartı korunur; geçmiş mühürler ve üretim akışı değiştirilmez, resmi yeni sabah SHA'sı üretilmez.
- Üç kesin isim karşılığı orijinal 215 kulüp kaydında kontrol edilip sadece PDF araştırma betiğinde eşlendi:
  - Racing Santander → R. Racing Club (LaLiga kanonik kayıt)
  - AC Milan → Milan (Lega Serie A kanonik kayıt)
  - Standard Liege → Standard de Liège (Pro League kanonik kayıt)
- Önceki resmî kapıyı geçen dokuz maçın yüzde sonuçları yeni hesapla **10 ondalığa kadar aynı** kaldı. Üretim modeli formüllerine dokunulmadı.

## Tek bir toplu çalışma kanıtı
- 8 PDF, 25 maç, **25/25 M4/C3 matematiksel araştırma tahmini**, **24/25 P0 tam**, **1 iddaa'da yayımlanmayan MS1 (Twente–Willem II)**.
- Betimsel iki bağımsız lider uyumu: **5 UYUMLU, 8 YUZDELER_UZAK, 11 FARKLI, 1 ORAN_EKSIK**.
- Tek GitHub çalışma kaydı: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/45012926414
- Tek kaynak makine verisi: GitHub Actions `nov22-eight-PDF-fixtures-no-official-source-research` artifakt JSON.
- Kullanıcıya sunulan V3 PDF: `22_Kasim_2026_25_Mac_3_Makine_V3_PDF_Kaynakli_Arastirma.pdf` (sohbet çalışma dosyası, depoya PDF baytları yüklenmedi).

## Gelecek işlem ilkesi
- **Sistem fikstür lookup sorunu ile model matematik sorunu ayıracak.**
- PDF'li, resmi fixture eşleştirilememiş maç için güvenli seçenek: yalnız `ARAŞTIRMA / PDF-LİSTE KAYNAKLI` etiketli bağımsız model ve P0 hesapları sun; böyle bir çıktıyı `resmî ilk-PDF mührü`, `resmî fixture doğrulandı`, `başarı kanıtlandı` diye göstermeyeceksin.
- Canlı/kanonik maç önü SHA ve haftalık başarı kohortuna kayıt yalnız mevcut ayrı resmî fixture + PDF SHA zinciri koşullarını gerçekten geçtiğinde yapılabilir. User-supplied PDF'den otomatik SHA doğrulanmış federation fixture iddiası **üretilmez**.
- Test içeriğindeki maçların bültende olması onların sonuçlarının veya bahis getirilerinin doğrulandığı anlamına gelmez.
- Bu karar dosyası **izole araştırma dalında** tutulur; onaylı üretim dalındaki eşik ve mühür akışı kendiliğinden gevşetilmedi.
