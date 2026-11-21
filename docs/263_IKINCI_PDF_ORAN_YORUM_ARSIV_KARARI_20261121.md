# D-SECOND-ARCHIVE-001 — İkinci PDF oran farkı ve yorumu kalıcı arşivi

**Karar:** 21 Kasım 2026 · **Kapsam:** 2.6.3 kapsamındaki bütün 10 lig, kullanıcının gönderdiği ikinci iddaa PDF'si.  
**Kullanıcı isteği:** İkinci PDF'den sonraki oran değişimleri ve asistanın maç önü futbol yorumları, ileride tekrar karşılaştırmak üzere **mutlaka kaydedilecek**. Bu, D-ODDS-001 ve D-OPER-006'nın zorunlu **kayıt** uzantısıdır.

## İki aşamalı veri sözleşmesi
1. **Sabah (değişmez):** Maç kimliği, tarih/KO, model SHA, karar SHA, MS/KG/2.5 ana tercih, alternatif ve kalibre model olasılıkları.
2. **İkinci iddaa PDF'si (eklenen gözlem):** Kullanıcının ikinci PDF SHA256 parmak izi, ilk PDF SHA256 parmak izi, ilk ve son **yedi** fiyat, ilgili pazarların marj arındırılmış ilk ve son yüzdeleri, ana fiyat farkı, sabit model olasılığına göre yeni piyasa farkı, karşılaştırma zamanı.
3. **Futbol yorumu:** Aynı raporda kullanıcıya gösterilen **tam asistan yorum metni** ve varsa kaynaklı XI/sakatlık/rotasyon iddialarının kaynak atıfları. Doğrulanmamış iddia ayrıca işaretlenir; fiyat hareketinin nedeni kesinmiş gibi kaydedilmez.
4. **Sonuç (gelecekte):** Maç bitince farklı ve sonradan eklenen bir değerlendirmede orijinal tahmin/ikinci fiyat/yorumla eşleştirilebilir. **Maç sonu bilgisi, geçmiş yorum dosyasına geri yazılmaz.**

## Kalıcı dosya düzeni ve işlem
- **Kanonik araştırma deposu:** `experiments/263/second_pdf_commentary_archive_263/YYYY-MM-DD/LEAGUE_HOME_AWAY.json`. Her maça **bir değişmez dosya**.
- **Üretim kodu:** `experiments/263/second_pdf_commentary_archive_263.py::append_review_archive`; `iddaa_pdf_last_review_263.py::process` her gerçek ikinci PDF kabulünde çağırır.
- Aynı PDF / aynı SHA / aynı yorum tekrar gelirse içerik eşitliğinden dolayı **idempotent**. Aynı maç için farklı oran/yorumla mevcut dosyayı üzerine yazmaya çalışırsa **REDDER**.
- Orijinal kullanıcı PDF baytları, şifreler, iddaa hesap bilgileri ve ham kişisel kaynaklar GitHub'a **yüklenmez**. Kaynaklar PDF SHA256 ile izlenir, kullanıcı dosyaları özel çalışma alanında kalır.
- Güncel çalışma kodunun ürettiği yeni arşiv dosyası önce **yerel çalışma kopyasına yazılır**. **GitHub'a kalıcı yüklenme ayrı commit ile doğrulanmalıdır**; yalnız yerel dosya oluşması uzakta kayıt iddiasına yetmez.
- İkinci PDF sonrası model yeniden hesaplanmaz; ana SHA kararları ve kullanıcıya sunulan D-OPER-006 dört simetrik kutulu tekli PDF değişmez.
- İkinci PDF gözleminin GitHub'a kickoff **öncesinde** commit edildiği kanıt yoksa kayıt `preko_git_seal` olarak etiketlenemez.

## İlk dört örnek / bugünkü iş
21 Kasım 2026, 15.30 Türkiye maçları:
- ENG1 Manchester City – Fulham
- ENG2 Southampton – Derby County
- ENG2 Millwall – Queens Park Rangers
- ENG2 Norwich City – Cardiff City

Bu dört dosya, kullanıcının **maç başlamadan önce bu sohbet üzerinden gönderdiği** ilk/ikinci PDF'lerden ve asistanın **önceden oluşturduğu onaylı tekli raporlarından** sonradan içeri alınmıştır. **GitHub arşiv commit işlemi kickoff sonrası yapıldığı için ikinci PDF kaynakları geçmişe dönük yeniden mühürlenmiş sayılmaz**. Gerçek kaynak dosya SHA, dondurulmuş özgün forecast/decision SHA ve raporda gösterilen yorum metni kayıtlarda yer alır. Oyuncu/ilk 11 kaynak iddiaları bu arşivleme işleminde bağımsız yeniden doğrulanmamıştır.

## Durum
- **A Karar:** Kullanıcı açık onayı alındı.
- **B Uygulama:** Dört örnek GitHub araştırma dalına commit edildi; append-only modül ve tekrarlı giriş güvenlik testi eklendi; ikinci PDF rotasına bağlandı.
- **C Tam otomasyon:** Yeni ikinci PDF'nin yerel arşive yazılması için modül testi PASS; uzak Git commit zincirini de içeren gerçek gün uçtan uca kabul henüz ayrıca kanıtlanmış değil. Bu alan tamamlandı denmez.

**Dönüşüm öncesi ve sonrası sayısal maç tahminleri/sabah SHA mühürleri değişmedi.**
