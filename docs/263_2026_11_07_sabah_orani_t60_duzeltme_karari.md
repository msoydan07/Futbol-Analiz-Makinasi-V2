# Futbol 2.6.3 — 7 Kasım 2026 sabah oranı düzeltmesi

## Bağlayıcı kullanıcı kararı
Cuma, cumartesi, pazar maç SABAHI; Türkiye saati 05:00–12:59 arasında, kapsamımızdaki 10 lig için o günün tüm önceden belirlenmiş maçları analiz edilir. B, C2, C3, M4 tahminleri ve aynı analiz sabahındaki The Odds API/Pinnacle h2h MS1-X-2 oranları kayda alınır ve SHA ile mühürlenir. **Maçın başlamasına 60 dakika kalması BEKLENMEZ.** 20–90 dakika T−60 koşulu yanlıştı ve kaldırıldı.

## Uygulanan uygulama
- sabah_pinnacle_new100_bridge_263.py: Gün ve saat Türkiye saatiyle sabah olmalı; maç başlangıcına en az 2 dakika kalmalı; tahminin yaşı 10 dakikayı aşmamalı. T−60 üst/alt sınırı kaldırıldı. Akşamki maç için sabah 10:02'de analiz yapılmasına izin verilir.
- GitHub morning workflow, sabah tanımını kullanır. Tahmin ve PAS kararı önce SHA ile GitHub'a kaydedilir, sonra aynı sabah ve aynı GitHub koşusunda Pinnacle fiyatı bağlanarak ayrı SHA fiyat/karşılaştırma raporu ile mobil ekran kalıcı olarak kaydedilir. Böylece orijinal tahmin değişmeden sabah analiz+oran aynı koşuda korunur.
- Günlük lig başına yalnız tek toplu Pinnacle h2h çağrısı. Önce GitHub'a rezervasyon push edilir, ondan sonra API sorgulanır. Başarısız veya boş sonuç için aynı gün otomatik tekrar sorgu yok. Fiyat/maç adı ve ev-deplasman sırası, UTC kickoff, piyasa güncelliği ve kaynak SHA uyuşmazsa oran kullanılamaz.
- MS1-X-2 için destekli kalibre yüzde / no-vig piyasa yüzdesi araştırma farkı hesaplanır. Güncel doğrulanmış Pinnacle oranı yoksa açık PAS. Sabah fiyatı gün içinde güncellenmez; maç saatindeki oran gibi gösterilmez. KG ve alt-üst pazarlarının Pinnacle fiyatları henüz bu bağlantının kapsamında değil.
- Eksik B veya C2 yüzdesi uydurulmaz; C3 ve M4 hazır ve en az üç model gerekli.
- Eski 96, üç mühendislik kabul kaydı, yeni 100 ayrı kalır; hiçbir eski mühür geriye dönük değiştirilmez.

## Kanıt ve açık sınır
Önceki 7 Kasım 44 maçlık araştırmada 0 Pinnacle sorgusu vardı, fiyatlar geriye dönük eklenmedi. Yeni100 canlı API ile aynı sabah uçtan uca başarı ayrıca kanıtlanmalıdır; kaynak yoksa oran/matematik başarısı uydurulmaz. Kodun sabah hali sentetik offline testte doğrulandıktan sonra yalnız mühendislik kabulü denir.

Yeni100 GitHub akışı şu anda yalnız kullanıcı tarafından isimlendirilmiş yeni maç manifestiyle başlıyor. Bu düzeltme T−60 hatasını giderir; bütün 10 ligin maçlarını otomatik olarak manifest yapan tam zamanlayıcı henüz kanıtlanmamıştır. Resmî fikstür doğrulaması eksik maçlar listeden sessizce atılmaz; engeli açıklanır.

**Bu karar** 7 Kasım'daki eski T−60 odaklı yazılı entegrasyon raporunu geçersiz kılar; yeni çalışma düzeni sabah analiz+Pinnacle+SHA mühürdür.
