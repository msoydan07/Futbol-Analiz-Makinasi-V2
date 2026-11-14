# 625 kaynak HOLD - xG öncesi veri-kabul hazırlığı
14 Kasım 2026 | Sadece veri mühendisliği | M4 ve eski mühürler dokunulmadı

## Kesinleşen 625
| Sınıf | Sayı | Sonuç |
|---|---:|---|
| ENG3/ENG4 orijinal hatalı kaynak | 200 | 178 skor + 22 skor/tarih için düzeltme işaretçisi var; eskiler HOLD, yeni maç değil |
| ENG5 orijinal skor/tarih çelişkisi | 96 | Hâlâ HOLD; kullanıcının 96 mühürlü pilotundan tamamen farklı |
| Üst kaynak kullanım hakkı açık değil | 325 | Eğitimden dışarıda |
| Avusturya başka organizasyon | 3 | Lig kümesinden dışarıda |
| Bastia-Red Star oynanmamış 90 dakika FT | 1 | Sonuç etiketi olarak kabul edilmez |
| **Toplam** | **625** | Sınıflandırma kilitli |

## Deney öncesi veri kalitesi
- 9.460 kaynak işaretçisi, 4.617 eski ana maç ve 4.218 skor-olgu kalite kontrolü sonucu korunur.
- 4.218 araştırma skoru henüz maç önü özelliği ve model eğitim izni değildir.
- Kaynaklarda kesin tarihli gerçek maç-önü özellik görüntüsü sıfırdır. Sonradan girilen xG geçmiş tahminin girdisiymiş gibi kullanılmaz.
- Mevcut 96 SHA mühürlü pilot değiştirilmez; 39 önceki maç sonucu karşılaştırması tekrar yapılmaz.
- Testten önce tarih, gerçek kaynak kullanım hakkı ve aynı 4-model ortak örneklem şartı kontrol edilir. Skor ve xG sadece maç sonu hedeftir.
- 751 kaynak adayı kullanıcının kararına göre kapsam dışı, yeni pilot yok.

## Senin işin ve sınır
- Sıradaki kullanıcı işi: 1.855 maç için aynı kaynaktan ev/deplasman gerçekleşmiş xG ve maç URL'si.
- Mevcut xG dosyası değiştirilmedi. Hazır salt-okunur xG kontrolcüsüyle daha sonra kontrol edilecek.
- xG bitince eksik kaynak lisansı, 43 resmî teyit ve gerçek tarihli maç önü özellik kanıtı otomatik kapanmış sayılmaz; bunlar ayrıca görünür.
- Bu turda model eğitimi, değerlendirme, karşılaştırma, yeni mühür, kaynak yeniden indirme yapılmadı.
