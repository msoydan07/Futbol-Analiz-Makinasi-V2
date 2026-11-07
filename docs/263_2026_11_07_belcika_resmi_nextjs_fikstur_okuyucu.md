# 2.6.3 — Belçika Pro League gerçek fikstür okuyucusu (7 Kasım 2026)

## Saha kanıtı
7 Kasım'da GitHub Actions ile Belçika'nın resmî **https://www.proleague.be/jpl-kalender!** sayfasını açtık. Görünen kartlarda saatin metin karşılığı bulunmuyordu. Kaynak HTML'nin **__NEXT_DATA__** JSON bölümünde **Jupiler Pro League**, **Seizoen 2026/2027** için dokuz resmî maç kaydı, takımlar, gün ve UTC başlama saatleri bulundu.

Dokuz kayıt: 6 Kasım 1 maç, 7 Kasım 4 maç, 8 Kasım 4 maç. Yerel kaynak günü ile Europe/Brussels eşleşmesi denetleniyor. Başlama saati, takım kimliği veya yarışma yanlışsa satır kabul edilmez. Mükerrer ve çelişen resmî kimlik verisi reddedilir.

## Değişiklikler
- `sabah_belgium_official_nextjs_263.py`: Resmî JSON'dan tarih-saatli maçları ayıklar; başka lig/kupa, yerel gün uyumsuzluğu ve geçersiz UTC saatini dışarıda tutar.
- `official_page_lookup_263.py`: BEL1 kaynağı doğrudan resmî takvime ve yeni ayrıştırıcıya yönlendirildi; başka JSON-LD'den maç uydurulmuyor.
- `sabah_official_fixture_gateway_263.py`: Mevcut kod yeni parser'ı kullanırken önceki kanonik takım-ID/official named gate'i **değiştirmiyor**.
- `test_sabah_belgium_official_nextjs_263.py`: Güvenlik ve fixture saat doğrulaması için hedefli testler.
- `263-sabah-offline-components.yml`: Tek toplu kabul testine eklendi.

## Açık kalan
**ENG2 Championship** resmî EFL sayfalarının GitHub koşucusunda okunması hâlâ doğrulanmadı. Belçika ve Portekiz'in tamamını kanıtladık diye tüm 10 ligin **tam kapsandığını** söylemiyoruz. Yarın sabah akışı ve The Odds API Pinnacle ücretli sorgu, gerçek maç öncesi kayıt ve pilot mühürleme bu denetimde **yapılmıyor**. Mevcut araştırma/96 pilot/new100 kayıtları ve main dalı korunur.
