# 2.6.3 — UEFA Şampiyonlar / Avrupa Ligi için **10 Lig Kapsamı ÖN KONTROLÜ**

**2 Kasım 2026 — Kullanıcı kararı, kabul edilmiştir.**

Artık Avrupa kupalarında yalnız **her iki takımın da** mevcut 10 yerel
ligin **2026/27 sezonunda** bulunduğu isim/kimlik doğrulanabilen
maçlar araştırmaya adaydır. Biri kapsam dışındaysa yeni ülke
ligi araştırılmayacak, veri toplanmayacak, tahmin yapılmayacak.

Mevcut 10 lig: ENG1, ENG2, GER1, ESP1, ITA1, FRA1, NED1,
TUR1, POR1, BEL1. Bu, Avrupa kupalarının turnuva kapsamını
daraltır; 10 ligin yerel maç analizlerini değiştirmez.

## İş sırası — zorunlu

0. **Sadece yerel read-only canonical index**:
   `experiments/263/evidence/identity_index_263.json`.
   `uefa_ten_league_scope_gate_263.py --home X --away Y`.
   Bu çağrı ağ erişimi yapmaz; UEFA kaynağı, rakip ülke
   ligleri, puan tablosu, kadro, oran, model veya geçmiş maç araştırmaz.
1. Eğer iki isim de current-season canonical ID üzerinden
   **kendi 10 ligimizdeyse** sadece
   `TEN_LEAGUES_SCOPE_PASSED_NOT_YET_VERIFIED` denir ve
   UEFA resmî fikstür kontrolüne geçilebilir.
   Tam isim eşleşmesi UEFA'dan bağımsız kulüp kimliği
   teyidi sayılmaz.
2. En az bir tanınmış canonical ID güncel on lig üyeliğinde
   **değilse**, `ANALYSIS_SKIPPED_OUTSIDE_TEN_LEAGUES`.
   Kullanıcı mesajı: **"Bu maçta kapsam dışı takım olduğu
   için analiz yapılmıyor."**
3. Bir isim local reviewed aliases içinde hiç yoksa,
   `ANALYSIS_SKIPPED_TEAM_SCOPE_UNVERIFIED`.
   Kullanıcı mesajı: **"Bu maçta en az bir takımın
   10 lig kapsamındaki kimliği doğrulanamadığı için analiz
   yapılmıyor."** Bu, takım kesinlikle başka ülkeden
   demek değildir; UEFA isim yazımı farklı olabilir.
   Rastgele fuzzy eşleme veya tüm yeni ligi araştırma yok.
4. Durdurulduysa **başka veri hattı çağrılmaz**:
   `preflight_then` yalnız iki taraf izinliyken sonraki
   bağımsız onay fonksiyonunu çağırır.
   Bu projede Avrupa için canlı named-match üretim
   orkestratörü henüz yoktur; oluşturulursa bu gate
   ilk ve zorunlu adım olacak. Modülün varlığı
   gelecekteki orkestrasyonun otomatik bağlı olduğuna
   tek başına kanıt değildir.

## Örnekler (2026/27 canonical index)

- Galatasaray – Barcelona: TUR1+ESP1 → sonraki doğrulamaya **aday**.
- Aston Villa – Fenerbahçe: ENG1+TUR1 → aday.
- Galatasaray – Celtic: Celtic yerel index'te yok → STOP,
  takım kapsamı doğrulanamadı; Celtic lig araştırması YOK.
- Galatasaray – Leicester: Leicester index'te mevcut,
  ama güncel 2026/27 10 ligde değil → STOP, kapsam dışı.

## Korunan işler

B/C2/C3/M4, 17 bölüm, A/B/C, canlı oran, 10 liglik veri
güncellemesi, main, 100 maçlık pilot, mevcut test arşivi
ve tarihsel UEFA kaynak denetim raporları değişmedi.
Bu kuralın amacı ilerideki **tek maç araştırması** öncesi
kapsamı daraltmaktır. Tarihsel akademik kaynak envanteri
(432 maç) arşiv olarak tutulabilir ama kapsam dışı
takımları tahmin modeline katmak için araştırmaya
devam edilmeyecek. Geçmiş H2H araştırması da yok.
