# 2.6.3 — Ücretsiz toplu oran araştırması (6 Kasım 2026)

## Kullanıcı kararı
- Ücretli OddsPapi iddaa yetkisi satın alınmayacak.
- Kullanıcıdan cumartesi/pazar çok sayıda maça ait oranları tek tek yazması istenmeyecek.
- Oran doğrulanmasa dahi B/C2/C3/M4 matematik, S1 açıklayıcı analiz ve SHA mühürü çalışacak; oran gerektiren S2/value **PAS** kalacak.
- Daha önce kaydedilmiş 6 Kasım maç tahminleri veya fiyat kararları geriye dönük değiştirilmeyecek.

## Belirlenen ücretsiz aday
[The Odds API](https://the-odds-api.com/) adlı farklı servis (not: `theoddsapi.com` değildir) 6 Kasım 2026 resmî sayfasına göre **500 kredi/ay ücretsiz**, bütün sporlar ve çoğu bookmaker; resmî lig listesi kapsamımızdaki **10 ligin tamamını** içeriyor.

Resmî kaynaklar:
- https://the-odds-api.com/
- https://the-odds-api.com/sports-odds-data/sports-apis
- https://the-odds-api.com/liveapi/guides/v4/index.html
- https://the-odds-api.com/sports-odds-data/betting-markets.html

Bir istek, bir ligdeki mevcut bütün maçların `h2h` ve `totals` pazarlarını Avrupa bölgesinde döndürür; sağlayıcının kredi modeli `pazar sayısı × bölge sayısı`. Bir tam 10-lig tarama = üst sınır **20 kredi** (10 lig × 2 pazar × 1 bölge). Cuma-cumartesi-pazar **günde tek tarama** dört haftada yaklaşık **240 kredi** tüketir; bu aralık model denemeleri, eksik pazardan dolayı fazladan sorgular veya ekstra taramaları kapsamaz. API kredisinin kalan miktarı mümkün olduğunda raporda tutulur; program kaçak tekrar sorgusu yapmaz.

## GitHub deneysel hazırlık
- `experiments/263/free_bulk_odds_263.py`: API secret `THE_ODDS_API_KEY` ile **sadece gerektiğinde** 10-lig toplu ve ön maç ilanlı kaynağı okuyan ayrı araştırma bağlantısı.
- `experiments/263/test_free_bulk_odds_263.py`: 10 lig/kredi/belirsiz pazar/bozuk oran/eski zaman/gizli anahtar negatif testleri.
- Bu aşamada **gerçek API anahtarı bağlanmadı**, gerçek fiyat görülmedi, görev otomatik çalıştırılmadı; kodun sentetik testinden canlı veri güvenilirliği veya kapsam tamlığı sonucu çıkarılamaz.
- Cuma 09:00 otomasyonu mevcut kalır. Bir sonraki adım: kullanıcı ücretsiz API hesabını seçip key'i GitHub Secrets > Actions > `THE_ODDS_API_KEY` olarak ekler. Anahtarı sohbete, dosyaya veya loglara yazmayın. Önce bir gerçek toplu örnekle lig/pazar/fiyat tazeliğini denetleyin; sonra haftada 3 gün sabah toplu koleksiyon ekleyin.

## Kritik ayrım: iddaa fiyatı değildir
Bu kaynaktaki bookmaker fiyatları (ör. AB bookmakerları) iddaa/Nesine/Bilyoner/Maçkolik'te alınabilen fiyatlar değildir. Bu nedenle ilk aşamada `FOREIGN_BOOKMAKER_MARKET_RESEARCH_ONLY` sınıfındadır. Resmî bahis değerli seçim/ana S2 onayı, Türk bahis pazarında uygulanabilir fiyat veya iddaa EV olarak gösterilmez. Aynı bookmaker ve aynı zamanlı karşı seçimleri tutarlı olduğunda yalnız piyasa referansı hesaplanabilir. Lig başına maçlar gelebilir ama gol toplamı/1.5/3.5 ve KG her kaynakta bulunmayabilir.

## Veri etiği
[football-data.co.uk](https://football-data.co.uk/) ücretsiz hafta sonu fikstür ve oran CSV'si de yayımlar fakat sayfasında otomatik bot/scraper/AI kullanımı için kısıtlar belirtiyor. İzin alınmadan bu siteyi otomatik çekme yolu olarak sisteme bağlamıyoruz. 
