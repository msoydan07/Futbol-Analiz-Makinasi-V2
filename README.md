# Futbol Maç Analiz Makinası V2

> **2.6.3 TEKLİ/TOPLU KARAR EKRANI — KALICI SUNUM STANDARDI (06.11.2026):** [docs/263_KARAR_EKRANI_KALICI_STANDART.md](docs/263_KARAR_EKRANI_KALICI_STANDART.md). Önce ana değer kararı / PAS, alternatif ve S1–S2 ayrımı; sonra teknik model tabloları. Yeni sohbetlerde ve yeni tahmin raporlarında bu standart esas alınır. Geçmiş SHA kilitli kayıtlar değişmez.

Temel analiz şartnamesi: **2.6.2 (değişmeyecek)**. Bu depo temiz kod altyapısıdır; eski depo korunur.

## Kapsam
Premier League, Championship, Bundesliga, La Liga, Serie A, Ligue 1, Eredivisie, Süper Lig, Primeira Liga, Pro League. Sezonlar: 2025-26 ve 2026-27.

## Onaylı aşamalar
1. Takım ve maç kimlikleri
2. Veri havuzu ve 2.6.2 veri ihtiyaçları
3. İki sezon / 10 lig veri toplama ve manuel eksik tamamlama
4. Veri kabul ve bağlantı testleri
5. Manuel maç girişi (otomatik fikstür askıda; doğrulanmamış bilgi işaretlenir)
6. Ana matematik motoru
7. Yardımcı Elo (başlangıçta tahmin olasılıklarını değiştirmez)
8. İlk yarı, maç toplamı korner ve diğer pazarlar (ilk yarı korner hariç)
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

## Veri kapsamı kararı (31 Ekim 2026)
İlk yarı korner pazarı 2.6.2 V2 uygulama kapsamından çıkarılmıştır. Kaynak araştırması, eksik veri raporu ve kabul testlerinde zorunlu alan değildir. Tam maç kornerleri kapsamda kalır. İlk yarı gol/sonuç pazarları kapsamda kalır. Eski ilk yarı korner deneysel dosyaları kanıt olarak kullanılmaz ve çalıştırılmaz.

## Veri için sıradaki tek iş
Mevcut `team-source-audit` hattının ürettiği `historical_results.csv` ve denetim raporunu doğrula; ardından doğrulanmış xG kaydını aynı fixture_id ile eşleştir ve `audit_missing_data_262.py` ile tek eksik veri raporu üret. Bu rapor gerçek çıktılar görülmeden tamamlandı sayılmaz.
