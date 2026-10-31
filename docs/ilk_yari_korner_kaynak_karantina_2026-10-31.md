# İlk yarı korner kaynağı — bağımsız gerçeklik doğrulaması zorunlu (2026-10-31)

## Tespit
- Kaynak içi toplama denetimi: 10 lig, 889 satır, 0 korner toplama uyuşmazlığı.
- Tarih/takım/FT korner ön eşleşmesi: 206; eşleşmeyen 683.
- Zorunlu skor denetimi eklendiğinde: 0 tam eşleşme, 206 kaynak skor sütunu tanınmaması; `ft_home`/`ft_away` adları artifact içinden teyit edildi ve kodda düzeltildi, **henüz yeniden ölçülmedi**.
- Artifact'teki eşleşmeyen örneklerde GER1 64/64, ESP1 100/100, FRA1 75/75, POR1 82/82 eşleşmiyor. Bu örüntü salt isim alias problemi olarak kabul edilemez.
- Kaynak örnekleri: ENG1 2026-08-22 Hull–Man Utd; TUR1 2026-08-14 Galatasaray–Çorum; GER1 2026-08-28 FC Bayern München–VfB Stuttgart. Örneklerin gerçek resmî lig fikstürü ve sonuçlarıyla ayrı karşılaştırılması şarttır.

## GÜVENLİK KARARI
**open-matchday kaynağı bağımsız gerçek maç/sonuç doğrulaması yapılıncaya kadar KARANTİNADA.** Kaynak içi 1H+2H=FT eşitliği, gerçeklik kanıtı değildir. Mevcut 206 ön eşleşme de kesin onay sayılmaz.

## Sonraki tek adım
1. Her ligden örnek maçları resmî lig/kulüp fikstürü ve mevcut Football-Data kayıtlarıyla karşılaştır; tarih, ev/deplasman, skor, maç statüsü.
2. Kaynak satırlarının bağımsız maçlara göre eşleşme oranını ve farkların nedenlerini raporla: isim alias, tarih, fikstür, skor, korner, kaynakta gerçek olmayan maç, veri yok.
3. İlgili kaynak satırlarının kökeni, yöntem, kullanım şartları ve gerçek zamanlı güncelleme güvenilirliğini değerlendir.
4. Sadece doğrulanmış kaynaklar için ayrı kabul mekanizması tasarla; ana tarihsel tabloyu veya tahmin motorunu değiştirme.
5. Aynı denetimi yeni workflow çalışması gerektirmeden mümkün olduğunca eldeki artifact üzerinden yap.

## Referans
GitHub Actions run 41190971505, artifact 13038483844.
