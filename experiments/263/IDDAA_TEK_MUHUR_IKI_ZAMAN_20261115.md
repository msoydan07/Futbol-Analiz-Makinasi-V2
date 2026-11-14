# 2.6.3 - Tek sabah mührü, maç önünde tek ek kontrol

**15 Kasım 2026 kullanıcı kararı:** Önceki iki-mühür fikri iptal. Tek SHA-kilitli matematik tahmini sabah üretilir; ikinci PDF yeniden tahmin/mühür oluşturmaz.

## Uygulanmış basit akış

1. **12.00:** Kullanıcı 10 aktif lig için iddaa.com PDF'sini gönderir. Mevcut iddaa_pdf_one_step_263.py ile ilk matematik raporu ve tek sabah tahmin mührü hazırlanır. Aynı PDF SHA tekrar gelirse eski rapor döner; model tekrar çalışmaz.
2. **Maça yaklaşık 60 dakika kala:** Başlamamış bütün maçların ilk 11 bilgileri topluca araştırılır. Kaynağı doğrulanamayan bilgi risk diye uydurulmaz.
3. **Maça 45-20 dakika kala:** Kullanıcı ikinci iddaa PDF'sini gönderir. Yeni iddaa_pdf_last_review_263.py sabahın **aynı tamamlanmış oturumunu** okur; aynı maçlar için MS 1/X/2, KG Var/Yok, 2.5 Alt/Üst sabah/son fiyatlarını ve marjsız farkı çıkarır.
4. **Maç önünde:** Her maç için aynı sabah model olasılıkları ve varsa somut kaynaklı, **sayısal olmayan** kadro yorumu tek telefona uygun son PDF + özet tabloya yazılır. Bu model tekrar hesaplama değildir.

## Değişmeyen kurallar

- İlk tahmin SHA, M4/B/C2/C3, ilk sabah oranları ve eski pilotlar kilitli. İkinci bir tahmin mührü veya yeni pilot oluşturulmaz.
- İkinci rapor sabah oturumuna bağlı yalnız bir defa yazılır. Aynı ikinci PDF tekrar gelirse eski rapor döner; farklı ikinci PDF eski raporu değiştiremez.
- Kadro/oyuncu verisi, tam maç kimliği, kaynak URL ve UTC zamanla kaydedilir. **Kod kaynak sitesini kendisi ziyaret etmiyor**: Kaynak iddiası ayrıca gerçek incelemeyle kontrol edilmedikçe bağımsız doğrulanmış sayılmaz.
- Sabah bilinen sakatlık, yeni haber gibi sunulmaz. Yeni bilgi iddiası için sabah kaynak zaman kanıtı gerekir. Kanıt yoksa yorum yok.
- Oran hareketi asla oyuncu eksikliği nedeni olarak otomatik ilan edilmez, M4 olasılığı değiştirilmez. Gerçek 11 gelmeden yorum uydurulmaz.
- Son kontrol maç başladıysa iptal; yanlış/tekrarlanan kimlikli maçlar ayrı engellenir; diğer aynı-saatli maçlar kontrol edilmeye devam eder.
- İki/üç maçı zorla seçme yok; PAS geçerli. Tam PDF'ler yerel oturumda kalır, herkese açık GitHub'a otomatik gönderilmez.

## Tek komut: son kontrol

PYTHONPATH=experiments/263 python experiments/263/iddaa_pdf_last_review_263.py --morning-dir /private/first-pdf-session --second-iddaa-pdf /private/iddaa-second.pdf --lineups-json /private/reviewed-lineups.json

lineups-json isteğe bağlıdır. İlk 11 kaynağı gerçekten incelenmediyse dosya uydurulmaz; sistem oran güncellemesini ve KADRO KANITI YOK durumunu gösterir.

## Mühendislik kabulü

- Beş maç aynı saatte, yanlış takım, çift PDF satırı, son dakika ve maç sonrası engel, kaynak yetersizliği, SHA değişikliği, PDF oluşturma/üzerine yazmama durumları **sentetik offline GitHub CI'da** sınanır.
- Henüz **iki gerçek iddaa PDF'si ve gerçek 11 kaynaklarıyla uçtan uca saha kabulü yapılmadı**. İlk gerçek maç gününde bu tek kez doğrulanacak; bundan sonra eski testlerin etrafında dönülmeyecek.
- Ana 2.6.3 üretim sistemi, 10 aktif + 12 araştırma ligi, xG bekleme ve ana M4 kilidi değişmedi.
