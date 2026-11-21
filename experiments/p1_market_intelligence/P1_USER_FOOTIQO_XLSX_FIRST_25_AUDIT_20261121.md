# P1 — Kullanıcı Footiqo Excel aktarımı: ilk 25 maç veri kabul denetimi

**Tarih:** 2026-11-21. **Kapsam:** Sadece P1 bağımsız araştırma; ana 2.6.3 M4/C3, v4, orijinal PDF ve SHA mühürleri değiştirilmedi.

## Girdi — yalnız özel çalışma ortamında

İki kullanıcı kaynaklı, **manuel dışa aktarılmış XLSX** dosyası incelendi. Ham XLSX, kaynak oranlar, maç bazlı yüzdeler ve maç sonuçları **bu kamu GitHub deposuna aktarılmadı**.

- `Database - Odds - England Premier League - CS.xlsx`: **25 fiyat satırı**, 2026-08-21–2026-09-05; SHA-256 `a7eb1b7c0fe220478a7853494a1fc80078daa29aeddafe5420f29d2b819ae595`.
- `Database - Scores - England Premier League - CS.xlsx`: **25 skor satırı**, 2026-10-25–2026-11-08; SHA-256 `a8b17c3e36514bc65da6c2cf6b0deca03eab2d56d234d431be5faede80d6ed03`.
- Aynı `id` ile **0**, aynı tarih + ev sahibi + deplasman ile **0** eşleşme. Bu nedenle bu iki dosyayla gerçek maç sonucu karşılaştırması **yapılamadı**. Brier, log-loss, isabet ve kalibrasyon için herhangi bir rakam üretilmedi.

## Fiyata dayalı betimsel kontrol

25 oran satırının tamamı MS1/MSX/MS2, 2.5 Alt/Üst, KG Var/Yok için **yedi pozitif ondalık fiyat** içeriyor; 25/25 hesaplanabildi. Ayrı ayrı marj-normalize P0 ve ters-Poisson P1 araştırma modeli kaynak kodunun matematiksel algoritmasıyla yerelde hesaplandı.

- P0/P1 ana tercihi aynı: **23/25**.
- Ana tercih farklı: **2/25** (Sunderland–Fulham; Newcastle–Liverpool). Bu uyuşmazlık doğruluk üstünlüğü kanıtı değildir.
- Ortalama kitap marjı: MS **%3.063**, O/U 2.5 **%3.805**, KG **%5.240**.
- P1–P0 en büyük pazar uyum sapması: **3.987 yüzde puanı** (ortalama maksimum sapma **2.275 puan**).
- Tüm 25 satırda model çıktısının alınması, **tek şirketin gerçek fiyat zamanı kanıtı** veya kalibrasyon başarısı değildir.

## Sonraki gereken kesin girdi

Gönderilmiş **Odds** dosyasına karşılık, Footiqo **Scores/Overview** sayfasından **21 Ağustos – 5 Eylül 2026** dönemine ait, aynı `id` değerlerini içeren maç skorları manuel Excel/CSV dışa aktarımı isteniyor. Alternatif olarak Odds ve Scores dosyaları **aynı tarih aralığına** filtrelenerek çift halinde alınabilir. İki dosya yeniden geldiğinde otomatik eşleşme kontrol edilecek; maç önü kapanış fiyatlarının gerçek yakalanma zamanı sağlayıcı beyanıdır, bağımsız sertifika değildir.

Kullanıcının karşılaştırma çalışma dosyası yalnız özel ChatGPT oturumunda üretildi; GitHub'a kopyalanmadı. Footiqo kaynak atfı: https://footiqo.com/database/ ; kullanım şartları: https://footiqo.com/dataset-licence/ .

**Karar:** Sonuç dosyası yanlış tarih aralığında olduğu için P1'e hiçbir yeni 25 maçlık sonuç kalibrasyonu eklenmedi. Ana model ve geçmiş mühürlerde değişiklik yok.
