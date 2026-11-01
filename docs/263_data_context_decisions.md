# 2.6.3 — Veri ve futbol bağlamı mühendislik kararları

**Tarih:** 2026-11-01. **Kapsam:** yalnız izole `experiment/263-toplu-karsilastirma` deney dalı. Ana üretim modeli, maç tahmini ve kabul protokolü değiştirilmedi.

## Döngü kontrolü

GitHub'da `identity.py`, `team_name_resolver.py`, resmî lig fikstürü sorgu modülleri ve geçmiş veri denetimleri zaten bulunmaktadır. Bu işte aynı araçlar yeniden yazılmadı ve ağdan yeni maç/transfer/sakatlık haberi toplanmadı. Önceki C0-C5, xG, Elo, ilk yarı ve korner performans deneyleri **tekrarlanmadı**.

## Gerçek eksik ve çözüm

`integrated_offline_report.py` önce yalnız sabit 17 bölüm durum listesi ve matematik olasılıklarını sunuyordu. Bir vakadaki verinin ne kadar güncel olabileceğini ölçen, ev/deplasman bağlam örneklemini ve **kullanılabilir vs. eksik vs. karantina** istatistiğini açıkça gösteren rapor yoktu.

Yeni `data_context_263.py`, mevcut iki sezonlu CSV üzerinde **hedef tarih hariç**, yalnız o tarihten eski sonuçlardan aşağıdakileri hesaplar:

- Lig özelinde güncel ve önceki sezon maç sayısı; aynı kulübün ev/deplasman sahası örneklemi.
- Son gözlenen lig/iki takım maçının tarihi ve hedef tarihle farkı; bu fark **eksik maçın kanıtı değildir**.
- Gol, ilk yarı, korner, şut ve *ana CSV içindeki* xG alanları için kullanılabilir kayıt sayıları.
- CSV'de adı geçen kaynak sağlayıcılarının alan adları; bunlar doğrulanmış ikinci kaynak değildir.
- Resmî fikstür, resmî ilk 11, sakatlık/ceza, taktik ve harici onaylı xG alanları **NOT_CHECKED / NOT_CONNECTED** olarak kalır.
- C2'nin dört iç/deplasman örneği altındaki bağlam uyarısı ve referans gerektiren alanlar.

`integrated_offline_report.py`, bu çıktıyı matematik ve kalite sonuçlarına ekler. Olasılık, model katsayısı, pazar kararı, resmî maç durumu veya önerilebilirlik değişmez.

## Dondurulmuş geçmiş veri üzerinde doğrulama

- CSV SHA-256: `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
- **4.413 geçmiş maç**, **10 lig**, **2025/26 ve 2026/27**. Dosyadaki en yeni sonuç **2026-10-29**.
- Dosyadaki tarihsel maçların kaynak referansları football-data.co.uk alan adına işaret ediyor. Resmî maç/ilk 11 kontrolü yapılmadı.
- Ana tarihsel CSV'de eşleşmiş xG alanı **yoktur**; daha önce ayrı oluşturulmuş doğrulanmış xG deney verisi bu iş kapsamında bağlanmadı veya silinmedi.
- 2026/27 İtalya verisinde bir şut satırının mantıksal denetimi başarısızdır. Bu satırın **şut alanı** kullanılabilir sayıdan çıkarılır; gol alanları bundan etkilenmez.
- On ligin her biri için 2026-10-30 kesimli salt-okunur veri bağlamı üretildi. ENG1 vakasıyla veri→matematik→kalite→rapor zinciri **bir kez smoke** olarak çalıştı; gelecekteki gerçek fikstür doğrulanmadı ve performans testi yapılmadı.
- **47 yerel yazılım/bütünlük testi başarılı**: daha önce var olan 33 + 12 veri bağlamı + 2 birleşik rapor testi. Bu sonuç model kalibrasyonu veya yeni sezon öngörü başarısı kanıtı değildir.

## Kapalı kalan alanlar

1. Hedef tarihe kadar oynanan **tüm** maçların CSV'ye girdiği, resmî sonuç fikstürüyle henüz bağımsız karşılaştırılmadı. Uzun takvim boşlukları otomatik 'veri bayat' sayılmamalı.
2. Kulüp/federasyonun resmî kadro ve ceza bilgileri ayrı canlı/önceden alınmış kanıtlara dayanmalıdır; geçmiş CSV'den türetilemez.
3. Farklı sağlayıcılardan xG doğrudan birleştirilmez; maç kimliği + sağlayıcı + tarih üzerinden doğrulanmış bağlayıcı gerektirir.
4. Takım kimliği mevcut registry üzerinden kontrol edilecektir; bu katman tek başına `Registry` yerine geçmez.
5. Ana çalışan Model B, oran/EV, gerçek maç kaydı ve pilot işlerine dokunulmadı.

**Sıradaki tek iş:** eldeki kimlik ve resmî kaynak modüllerini yeniden yazmadan, doğrulanabilir kaynak gözlemlerini analiz paketine nasıl gireceğimizi güvenli bir *girdi sözleşmesi* ile belirlemek. Kodlanmamış veya kaynağı doğrulanmamış futbol bağlamını matematik faktörü olarak eklememek.
