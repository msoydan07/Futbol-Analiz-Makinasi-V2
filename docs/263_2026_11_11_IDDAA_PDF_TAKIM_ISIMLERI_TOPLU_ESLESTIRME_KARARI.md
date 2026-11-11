# 2.6.3 — Kullanıcı İddaa PDF'si için takım isimleri: tek seferlik ön kontrol (11 Kasım 2026)

## İstek ve karar

Kullanıcı bir gün 10 kapsam liginden örneğin 5 lig seçip iddaa.com resmî bülteninden PDF gönderecek. **İddaa PDF'si kullanıcı tarafı fikstür/fiyat kaynağı**, bağımsız **tek lig/federasyon/kulüp fikstür kontrolü** ile aynı maçta buluşacak. Aynı oranı üçüncü bir siteden tekrar kontrol etmeyiz. Takım ismi farklı yazılıyor diye bütün ligleri veya günün diğer maçlarını tekrar araştırmayız.

## Denetim: risk gerçektir

- `experiments/263/evidence/identity_index_263.json` içinde **215 takım**, **370 orijinal alias**, 2026–27 için **10 lig** bulundu; lig içi normalleştirilmiş alias çakışması **0**.
- **İddaa kaynak kanıtı olarak karıştırılmaması gereken test:** 8 Kasım 2026'da arşivlenmiş **9 lig, 43 maç, 86 gerçek Pinnacle/The Odds API takım adı kullanımı**; mevcut aliaslarla **66/86** otomatik eşleşiyordu, **20/86** ayrı yazılış yüzünden eşleşmiyordu.
- Örnek: `Besiktas JK` ↔ kayıtlı `BEŞİKTAŞ A.Ş.`, `Genclerbirligi SK` ↔ `GENÇLERBİRLİĞİ`, `Brighton and Hove Albion` ↔ `Brighton & Hove Albion`, `Inter Milan` ↔ `Inter`, `AC Milan` ↔ `Milan`, `Çaykur Rizespor` ↔ `ÇAYKUR RİZESPOR A.Ş.`. **Bunlar geçmiş Pinnacle veri etiketleridir; iddaa bunları kullanıyor iddiası yoktur.**
- Kullanıcının 11 Kasım iddaa.com örnek PDF'si **millî takım/kupa/alt lig** içeriyor; bu belge 10 ligdeki farklı iddaa takım etiketlerinin kapsamını kanıtlamıyor. PDF'de kısaltılmış `...` / `…` takım adı olabiliyor.

## Aktif deney dalına konan çözüm

`experiments/263/iddaa_pdf_team_alias_preflight_263.py` yeni, **ek modül**: var olan imzalı takım kayıtlarını ASLA değiştirmeden, 20 **kanıtlı haricî** isim farkını ilgili kayıtlı lig üyesi UUID'sine bağlıyor. Yalnız tam/deterministik isim normalizasyonu ve pinlenmiş açık alias; **fuzzy tahmin, sessiz takım birleştirme veya otomatik isim uydurma yok**.

- `index_registry`: SHA-korumalı 215 takım dizini ve 10 lig üyeliğini okur, alias çakışmasında fail closed.
- `resolve_label`: PDF'deki tek ismi lig içinde çözer; kısaltılmış/hiç tanınmayan isim tek maça **`SINGLE_ROW_NAME_REVIEW`** verir.
- `match_pdf_row`: ev/deplasman aynı sırada ve **aynı gün+başlama saatiyle** yalnız **tek bir önceden resmî kaynaktan toplanmış maç** bulunursa fiyatları o maçla eşler. Aynı isim ve saatle çoklu/ters/şüpheli eşleşme güvenli atlanır. Bu modül resmî siteye yeni web sorgusu veya API oran çağrısı YAPMAZ.
- `preflight_batch`: bir sorunlu satır yüzünden kalan maçları durdurmaz. Gerçek fiyatlar, M4, B/C2/C3, eski SHA'lar, 99 skor arşivi değişmedi.

## Kanıt

[Gerçek GitHub Action **43049571989** — 7/7 test başarılı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43049571989). Bütün 86 kayıtlı haricî isim testte **86/86 eşleşti**; ters ev/deplasman, hatalı saat, yinelenmiş resmî maç, kısaltılmış isim ve yalnız tek maç bloklama test edildi.

## Dürüst sınır: gerçek PDF entegrasyonunun aşaması

- **İsim eşleştirme modülü test edilip deney dalına eklendi; fakat iddaa PDF'den satır çıkarıp bu modüle otomatik bağlayan üretim giriş noktası henüz tamamlanmadı.** Bir sonraki gerçek 10 lig seçili PDF ile etiketlerin içeriği görüldüğünde tek toplu kabul yapılacak.
- Geçmiş Pinnacle etiketleri **iddaa'da 100% kapsama garantisi değildir**; yeni/yabancı sponsor/ek/kısaltma biçimi ilk kez görülebilir. Sadece okunamayan/şüpheli maçın PDF satırı için açıklama gerekir, bütün analiz tekrar edilmeyecek.
- Kullanıcı yeni URL, ikinci oran kaynağı veya tekrarlı federasyon onayı vermek zorunda değildir: **kullanıcının bülteni + toplu tek resmî fikstür kontrolü** yeterli işlemsel düzendir.
- Cinsiyet, U19, kupa veya 10 kapsam dışı lig yanlışlıkla ana motorun lig takımına dönüştürülmez; kapsam dışı sistem ayrı LITE politikasıdır.

**Net kural:** Maç günü tek PDF → toplu ad çözme → lig başına tek resmî fikstür karşılaştırması → eşleşenlerin toplu analizi. Tek bir isim belirsizse yalnız o maç işaretlenir; diğer maçlar ve oranlar normal yürür.
