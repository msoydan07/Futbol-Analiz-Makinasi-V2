# P1 | Kullanıcının yeni skor Excel'i: 7 eşleşmiş gerçek maç denetimi

**Tarih:** 21 Kasım 2026. **Dal:** `experiment/p1-market-intelligence-20261121`. **Kapsam:** Yalnız bağımsız, geriye dönük P0/P1 fiyat araştırması. Ana 2.6.3, M4/C3, v4 karar, aktif 10 lig ve bütün maç önü SHA mühürleri değişmedi.

## Girdi ve doğrulama
Kullanıcının daha önceki Footiqo Odds XLSX dosyası ile yeni Footiqo Scores XLSX dosyası; orijinal dosyalar **özel çalışma alanında**, kamu GitHub'a **yüklenmedi**.

- Oran XLSX SHA-256: `a7eb1b7c0fe220478a7853494a1fc80078daa29aeddafe5420f29d2b819ae595`; 25 satır, yedi tam fiyat.
- Yeni skor XLSX SHA-256: `25d040d1f7072c2a7fb89195d6dc1f7a46a0ee295d7ac6d3504a5ebf74fa13b8`; 7 satır.
- **Maç ID + tarih + sezon + lig + ev/deplasman isimleri birebir eşleşmiş 7 satır**. **18 oranlı maçın skoru yeni dosyada yok.**
- Skor XLSX'inde başlıkların bir kısmı Türkçeye çevrilmiş (`Ülke`, `Lig`, `Sezon`, `Ana SayfaEkip`); eşlemede bunlar doğrudan ilgili orijinal kolon adlarıyla karşılaştırıldı.
- **7/7 maç sonucu deplasman galibiyeti (FTR=A, MS2).** Bunun export filtresinden kaynaklandığı doğrulanmadı; ancak örneklem temsiliyetini açıkça tehdit ediyor. Bu 7 maçı kalibrasyon eğitimi, bağımsız model üstünlüğü veya 7/25 başarısı olarak yorumlama.

## Yedi maçlık salt betimsel P0–P1 değerlendirmesi

| Ölçüt | P0 | P1 |
|---|---:|---:|
| En yüksek 7 olay olasılığına göre ana tercih isabeti | 4/7 (%57,14) | 4/7 (%57,14) |
| 3 pazar makro Brier (düşük iyi) | 0,551744 | **0,543829** |
| 3 pazar makro log-loss (düşük iyi) | 0,805579 | **0,793943** |

- P0 ile P1 bu 7 maçın **7'sinde de aynı ana tercihi** seçti; isabetleri aynıdır.
- Gerçek MS: ev=0, beraberlik=0, deplasman=7. 2.5 Alt=5, Üst=2. KG Yok=5, Var=2.
- Brier hesabı 7 olayın bağımsız sayılmasıyla değil, üç karşılıklı dışlayıcı pazar grubunun makro ortalamasıdır.
- Bu örneklemde P1'in küçük hata avantajı **istatistiksel üstünlük değildir** ve daha önceki 535-maçlık OddsIntel uzlaşı fiyatları kohortu ile birleştirilmedi. Kaynağın kapanış fiyatları bağımsız as-of zaman sertifikası taşımaz.
- Rastgele kontrol edilen skor örnekleri: Nottingham–Leeds 0-1 (https://www.leedsunited.com/en/news/report-nottingham-forest-0-1-leeds-united); Crystal Palace–Manchester City 1-4 (https://www.cpfc.co.uk/match/2645209/men/premier-league/2026-27/crystal-palace-vs-manchester-city-2026-08-28/).

## Eksik kısım ve sonraki adım

**Eksik 18 maç:** Aynı Footiqo sayfasında, oranların tarih aralığı **21 Ağustos – 5 Eylül 2026** için, FTR/sonuç filtresi varsa kaldırılmış tam `Scores/Overview` Excel/CSV dosyasıyla tamamlanmalı. Eldeki yeni XLSX yalnızca 7 deplasman galibiyeti içeriyor. Aynı ID eşleştirme yöntemiyle, tam ve dengeli veri geldikten sonra 25 maçın tamamı değerlendirilebilir. Mevcut 7'lik sonuçla kalibrasyon parametresi öğrenilmedi.

**Özel kullanıcı raporu:** `P1_7_Eslesen_Mac_Detayli_Rapor_20261121.xlsx`; yalnız sohbet ortamında üretildi, GitHub'a ham oran veya maç verisi taşınmadı.
