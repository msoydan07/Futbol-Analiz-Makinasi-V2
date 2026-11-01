# Futbol Maç Analiz Makinası 2.6.3 — 17 bölüm uyum denetimi

**1 Kasım 2026, yalnız matematik + kalite katmanı:** Bu dosya bir kabul / tamamlandı sertifikası değildir. Önceden kilitlenmiş 4.413 maçlık geçmiş dosya, 880 maçlık daha önce incelenmiş retrospektif kohort ve 14 yazılım testi esas alınmıştır. Çalışan ana motor değiştirilmedi, pilot ve gerçek maç kayıtları yapılmadı.

| Şablon | Güncel teknik durum | Kesin sınırlama / sonraki işlem |
|---|---|---|
| 1. Ana görev | KISMİ | 1X2, gol ve KG matematiksel çıkıyor; güvenilir en olası tercih için kalibrasyon yok |
| 2. Güncel veri / kaynak | KISMİ | Eski CSV snapshot var; canlı doğrulama ve son veri tazeliği bu akışta yok |
| 3. Maç önü bütünlük | BEKLİYOR | Fikstür saati, resmî doğrulama, ilk 11 kontrolü ayrı |
| 4. Takım formu / rakip kalitesi | KISMİ | C3 rakip güçlerini öğrenir; son maç formu kalibrasyonu/yorumlama eksik |
| 5. Kadro / taktik / koşullar | BEKLİYOR | Doğrulanmış kadro/kritik haber akışı henüz 2.6.3 raporuna bağlanmadı |
| 6. İstatistiksel model | KISMİ | C2 k5/w0.5 yazıldı; C2 sadece 105/880 maçta ölçüldü; C3 614 maçta retrospektif olumlu |
| 7. Elo | AYRI TUTULDU | Eski Elo harmanı ileri dönem kontrolünde fayda göstermedi, otomatik dahil değil |
| 8. MS 1X2 | KISMİ | Ortak skor matrisinden hesap var; kanıtlanmış/kalibre edilmiş seçim yok |
| 9. Gol / KG | KISMİ | Aynı skor matrisinden tutarlı rakam var; C2 veri yetersiz, güvenli seçime terfi yok |
| 10. İlk yarı / doğru skor | KISMİ | İlk yarı MS geçmişte olumlu; İY Üst referansı geçmedi; skor adayları istatistiksel kesinlik değil |
| 11. Korner | KISMİ | Ayrı sayım modeli hesaplandı ancak lig referansından kötü; lig frekansı yalnız kıyas, öneri değil |
| 12. En olası tercihler | BEKLİYOR | Yüksek ham model yüzdesi tek başına güvenilirlik değildir; otomatik seçim kapalı |
| 13. Matematiksel değer | SONRA | Oran/EV veri hattı ve değer eşiği şimdilik gündem dışı |
| 14. Güven / risk | KISMİ | Pazar bazlı kanıt etiketleri, karantina ve λ±10% sezgisel duyarlılığı hazır; gerçek güven aralığı değil |
| 15. Sonuç sunumu | KISMİ | Makine okunur JSON ve insan okunur offline kalite raporu hazır; gerçek çoklu/tek maç final şablonu henüz bitmedi |
| 16. Ön kayıt / sonuç denetimi | SONRA | Kullanıcı talebiyle sistem kurulumu bitene kadar beklemede; mevcut eski deney dalı kodları kullanılmıyor |
| 17. 25 maçlık pilot | SONRA | Başlatılmadı |

**Kesin karar:** C2 ve C3 ayrı kalacak. C3/İY MS olumlu retrospektif adaydır, entegre edilmez. İY Üst ve maç sonu korner için takım temelli sayım modeli lige üstünlük gösteremedi. Resmî fikstür, canlı oyuncu/kadro, xG doğrulama ve istatistiksel kalibrasyon ana analizde eksik. Henüz 2.6.3'e **TAM UYUMLU** denemez.

**Bir sonraki tek iş:** Veri → matematik → pazar kalite kapısı → 2.6.3 tek/çoklu maç offline analiz raporu zincirini birleştirip, bütün bölümlerin eksik/veri durumunu dürüstçe gösterecek **birleşik offline analiz raporunu** tamamlamak. Ondan sonra toplu uçtan uca yazılım testi; gerçek maçlar, pilot ve oranlar sonra.