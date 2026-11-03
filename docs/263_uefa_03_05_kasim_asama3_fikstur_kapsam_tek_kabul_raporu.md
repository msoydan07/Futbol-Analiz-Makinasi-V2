# Futbol Maç Analiz Makinası 2.6.3 — 3–5 Kasım UEFA Fikstür/Kapsam Aşama 3 Kabul Raporu

**Tarih:** 3 Kasım 2026 Salı (Türkiye yerel zamanı)  
**Çalışma:** Yalnız UEFA Şampiyonlar Ligi ve Avrupa Ligi; 3 Kasım Salı, 4 Kasım Çarşamba, 5 Kasım Perşembe 2026.  
**Karar:** **17 UEFA karşılaşması / 34 farklı kanonik kulüp WEB DESTEKLİ FİKSTÜR + İKİ TARAFLI KAPSAM İNCELEMESİYLE kabul.** Matematiksel tahmin, veri güncelliği ve değişmez tahmin kaydı bu aşamanın konusu değildir.

## 1. İki resmî UEFA kaynağı

UEFA'nın 2 Kasım 2026 tarihli fikstür duyuruları, 3 Kasım'da ChatGPT web tarayıcısıyla doğrudan incelendi:

- Şampiyonlar Ligi: https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/
- Avrupa Ligi: https://www.uefa.com/uefaeuropaleague/news/02a8-2174cafa5bb6-82bbc20c9b92-1000--2026-27-europa-league-all-the-league-phase-fixtures-and-results/

Her ikisinin açık saat kuralı: "Kick-offs are 21:00 unless stated; all times CET." Türkiye = CET + 2 saat (bu üç Kasım tarihi için). UEFA listesinde açıkça 18:45 veya 16:30 yazılmış maçlar kendi saatinde tutulur. **Hedef maçlar 20:45 veya 23:00 Türkiye saatiyle başlar.**

Bu üç günkü **tüm 36 resmî maç** ilk kapsam incelemesine alındı. Katılım şartı: **iki** takım da 2026/27 sezonu kanonik kulüp kimlikleriyle eşleşip kullanıcı tarafından tanımlanan **167 Avrupa Elo adayına** dahil olmalı.

| Gün / turnuva | Toplam resmî maç | Kapsam içi analiz adayı |
|---|---:|---:|
| 3 Kasım Salı — CL | 9 | **6** |
| 4 Kasım Çarşamba — CL + EL | 10 | **6** |
| 5 Kasım Perşembe — EL | 17 | **5** |
| **Toplam** | **36** | **17** |

**19 maç kapsamdan seçilmedi.** Tanınmayan kaynak takım adı otomatik biçimde "kesin kapsam dışı" ilan edilmedi; yalnız iki taraflı 167 kümesi eşleşmesi sağlanamadı. Championship/ENG2 (24) ve Erzurumspor (1), kullanıcı kararı gereği bu Avrupa Elo alt kümesinde zaten bulunmuyor.

## 2. UEFA resmi maç sayfalarının 17'si tekil bağlantılıdır

Her seçilen karşılaşma için UEFA'nın **tekil maç sayfasına** bağlantı resmî fikstür duyurusundan izlendi. Bu URL'deki sayısal değer **maç ID'sidir; takımların UEFA kulüp ID'si değildir.** Ayrıntılı 17 bağlantı, saat ve kanonik takım-ID çiftleri şurada:

- \`experiments/263/evidence/uefa_2026_11_03_05_fixture_scope_review.json\` (36 maç / 17 seçilen / 19 elenen açıklamalı liste).
- \`experiments/263/evidence/uefa_web_2026_11_03_17_matches_review_only.json\` (UEFA duyurusundan 3 Kasım'da gözlenen 17 maçın tarih/saat metni; mevcut güvenli web destekli hatta uygun şema).

**Kesin ek UEFA kaynak adı eşleştirmeleri (fuzzy eşleştirme yok):**
- "Bayern München" → "FC Bayern München" (GER1).
- "Leipzig" → "RB Leipzig" (GER1).
- "Union SG" → "Royale Union Saint-Gilloise" (BEL1).

Bu üç kayıt federasyon tarafından doğrulanmış mevcut kanonik takım kimlikleri ve 2026/27 lig üyeliğiyle kontrol edildi. **Ana \`identity_index_263.json\` değiştirilmedi.** Sadece \`uefa_requested_match_entry_263.py\` ve önceden zaten mevcut \`uefa_web_evidence_handoff_263.py\` geçici UEFA isim eşdeğerliği kopyasını kullanır. Ev/deplasman yönü ve tüm 10 liglik mevcut kapsam kapısı korunur.

## 3. Kaynak erişimi ve testin dürüst statüsü

GitHub Actions'ın \`www.uefa.com\` ağ okuması **zaten 2 Kasım tarihli projede belgelendiği gibi** TimeoutError vermektedir. Bu hatalı/engellenen URL olduğu kanıtı değildir: resmî kaynak ChatGPT web aracında açıldı ve tüm 17 maç sayfası incelendi.

- Tek doğrudan GitHub UEFA ağ denetimi: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41588913855  
  **FAIL / TimeoutError.** Bu tekrar, eski ağ engeli zaten bilindiği için gerekli değildi; tekrar etmeyeceğiz. Bu adımın sonucu **LIVE_RUNNER_UEFA_VERIFIED = false**.
- Var olan ve güvenli olduğu önceden kabul edilmiş **web destekli kaynak aktarımına** dönüldü. Kaynak kanıtlarının süre kontrolü, sahte alan adı engeli, ilk aşamada kapsam kapısı ve model/pilot yok kuralı korunuyor.
- Bunun tek yeni **offline toplu kabul koşusu:** https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41589333044  
  **SUCCESS; 5/5 odaklı kontrol başarılı.** Bunlar kullanıcıya ve kaynak bağlantısına sadık yazılım/kimlik kontrolleridir; GitHub'ın UEFA'yı canlı okuduğu iddiası YOK.
- Arşiv: artifact **263-uefa-03-05-nov-web-assisted-scope-accepted**; \`assisted_17_scope_gate_report.json\`. Karar durumu: \`17_OFFICIAL_WEB_ASSISTED_FIXTURES_AND_CANONICAL_SCOPE_ACCEPTED\`.

## 4. Gerekli güvenlik ve geçerlilik sınırları

1. Bu aşama **yalnız maç varlığı, tarih/saat, ev/deplasman, 2026/27 iki taraflı lig üyeliği ve 167 Avrupa Elo aday kümesi** incelemesini tamamladı. 17 kulübün güncel maç önü istatistiklerini toplamadı, kadrolarını doğrulamadı, Poisson/Elo'lu olasılık üretmedi.
2. 3 Kasım'da kontrol edilen web destekli kaynak olgularının **en fazla 1 günlük güncellik süresi** vardır; **5 Kasım Perşembe günü kullanmadan önce yeniden güncel resmî UEFA kaynağından teyit şart**. Eski metin üzerinden otomatik doğru denmez.
3. Kaynaklar web'de resmî olarak okundu, ama GitHub runner'ın doğrudan resmi URL indirmesi **blokeli**. Salt JSON kaydı tek başına bağımsız orijin kanıtı değildir. Bu iki durum raporda ayrı tutuldu.
4. Tekil UEFA maç ID'si, kulübün bağımsız resmî UEFA kimlik numarası değildir; sayısal takım ID eşleşmesi için "ayrı doğrulandı" iddiası YOK.
5. \`main\`, yerel 10 lig, Model B/C2/C3/M4, xG/H2H kuralları, Elo'yu gol λ'ya katmama kararı, 0/100 pilot, oran/EV/A-B-C **değişmedi**.

## 5. Sıradaki çalışma

**Aşama 4 — bu 17 maçın maç öncesi yerel gol/puan, son maç, ev/deplasman ve rakip düzeltme girdilerinin kaynak/tarih kontrolü.** En erken başlayacak 3 Kasım Salı maçları için öncelik, 20:45 Türkiye saatinden önce veri temini ve güvenli analiz hazırbulunuşluk raporudur. Tahminleri kilitleme/kayıt aşaması kullanıcı isteği gereği **en son** yapılacaktır.

**Kesin statü:** UEFA web kaynaklı fikstür + kanonik alt küme kabul, doğrudan runner UEFA fetch blokeli, model tahmin yetkisi henüz YOK.
