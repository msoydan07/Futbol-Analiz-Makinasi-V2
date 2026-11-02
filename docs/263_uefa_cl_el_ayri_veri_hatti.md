2.6.3 -- Ayrı UEFA Şampiyonlar / Avrupa Ligi veri hattı (2 Kasım 2026)

Amaç: 10 yerel ligi hiç değiştirmeden UEFA_CL ve UEFA_EL için bağımsız kaynak aday hattı oluşturmak. Mevcut 10 ligin identity.LEAGUES, season_refresh_263, Salı 10.37 güncellemesi, C2/B/C3/M4, ana dal ve pilot kayıtları değişmedi.

Gerçek resmi UEFA maç sayfası örnekleri:
Champions: https://www.uefa.com/uefachampionsleague/match/2049614--galatasaray-vs-stuttgart/
Europa: https://www.uefa.com/uefaeuropaleague/match/2050116--celtic-vs-besiktas/

İlk uygulanan adım: yeni experiments/263/europe/uefa_stage_263.py sadece kullanıcı/operatör tarafından verilen matches listesini STAGED aday olarak denetler. URL'nin UEFA resmi alan adı ve turnuva/maç ID biçimini kontrol eder. İnternetten sayfayı okumaz; URL doğru görünmesi içerik doğrulaması DEĞİLDİR. UEFA match ID'si ertelemede aynı kalır, iki farklı ayağın ayrı match ID'si olmalı. Takımların yerel lig kimlikleri otomatik eşleştirilmez. Maç başlangıcı UTC offset ile zorunludur, CET/CEST otomatik tahmin edilmez. Skoru olmayan eski maç için 0-0 uydurulmaz. Sonucu bildirilen maç da bağımsız UEFA teyidi olmadan eğitim verisi sayılmaz.

Dosya yalnız data/europe_staged_263/*.json içine yazılabilir. Genel tarihsel maçlar, 10 lig veri güncellemesi, model parametreleri, A/B/C sınıfları, bahse dair kararlar ve 100 maç pilotu bundan etkilenmez.

Sonraki aşamalar:
1) Gerçek UEFA sayfası üzerinden bağımsız maç ve sonuç doğrulaması; yalnız istenen maç için 7 günlük pencere.
2) UEFA adlarını mevcut canonical takım ID ile resmî kaynak üzerinden eşleştirmek; mevcut 10 lig dışı takımları ayrı incelemek.
3) İki turnuvanın geçmiş maçlarını kaynaklarıyla toplamak; ülkeler arası takım gücü kıyasını yeni geçmiş dönemlerle kronolojik doğrulamak.
4) Dört model UEFA'da doğrulanmadan aynı lig varsayımıyla tahmin üretmemek. Sonra 17 bölüm/oran/A-B-C entegrasyonunu kabul etmek.

DURUM: Güvenli veri aday hat taslağı; doğrudan canlı UEFA fikstürü toplayan otomasyon ve geçerli Avrupa tahminleri henüz kurulu değil.
