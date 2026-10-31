# Futbol Maç Analiz Makinası V2

Temel analiz şartnamesi: **2.6.2 (değişmeyecek)**. Bu depo temiz kod altyapısıdır; eski depo korunur.

## Kapsam
Premier League, Championship, Bundesliga, La Liga, Serie A, Ligue 1, Eredivisie, Süper Lig, Primeira Liga, Pro League. Sezonlar: 2025-26 ve 2026-27.

## Onaylı aşamalar
1. Takım ve maç kimlikleri
2. Veri havuzu ve 2.6.2 veri ihtiyaçları
3. İki sezon / 10 lig veri toplama ve manuel eksik tamamlama
4. Veri kabul ve bağlantı testleri
5. Tek merkezi 7 günlük fikstür
6. Ana matematik motoru
7. Yardımcı Elo (başlangıçta tahmin olasılıklarını değiştirmez)
8. İlk yarı, korner ve diğer pazarlar
9. Tam 2.6.2 analiz ve tahmin raporu
10. Kronolojik geçmiş sezon testleri ve kalibrasyon
11. Gerçek maç pilotu ve sonuç karşılaştırması
12. Haftalık güncelleme ve otomatik işletim

## Takip kaydı
| Aşama | Durum | Kullanılan modül | Test kanıtı |
|---|---|---|---|
| 1 — Kimlikler | Başlanmadı | — | — |

Bir aşama ancak kabul kriteri ve test kanıtı kaydedilince tamamlanır. Yeşil CI tek başına matematiksel doğrulama değildir. Tamamlanan modül yeniden yazılmaz. Aynı iş için paralel modül/klasör açılmaz. Değişiklik olmadan başarısız test tekrarlanmaz.

## İlk işin kabul kriteri
10 ligde iki sezon boyunca takım kimlikleri tutarlı; aynı takım farklı yazımlarda aynı kimliğe eşlenir; farklı takımlar yanlışlıkla birleştirilmez; maç kimlikleri benzersiz ve tekrarlanan veri alımlarında sabittir. Bu özellikler somut test çıktısıyla kanıtlanmadan aşama 1 bitmiş sayılmaz.

## Kesin karar — tek maç fikstür akışı (31 Ekim 2026)
Kullanıcı belirli bir maçı analiz et dediğinde, önce mevcut oynanmamış maç listesindeki iki takım eşleşmesi aranır. Bulunan maçın kayıtlı tarihi/saati kullanılır; belirsizlik veya değişiklik ihtiyacı varsa ilgili ligin resmî fikstüründen yalnızca o maç için kısa kontrol yapılır. Eşleşme ve tarih/saat yeterince netleştiğinde fikstür aşaması sona erer ve 2.6.2 analizine geçilir. Resmî siteye erişim sorunu, ilk 11'in açıklanmaması veya tekrar tekrar fikstür testleri analizi otomatik olarak bloke etmez; doğrulanamayan alan açıkça belirtilir. Listede maç yoksa bunu dürüstçe bildir, varsa canlı kaynaktan bulmaya çalış; maç veya saat uydurma. Modül 0 sadece kullanıcı açıkça 'maç bul' dediğinde çalışır. 10 lig kapsamı korunur. Yeni paralel fikstür sistemi, toplu örnek eşleşme kabul testleri veya aynı soruna tekrar tekrar workflow koşuları ekleme. Bu karar yeniden tartışmaya açılmayacak; otomatik kodun canlı başarısı ayrıca kanıtlanmadıkça iddia edilmeyecek.
