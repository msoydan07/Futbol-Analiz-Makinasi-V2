# 22 Kasım 2026 — 23 maçın maç önü SHA kilidi ve bağımsız resmî kaynak kanıtı

**Durum:** Araştırma SHA'ları maç önünden beri kilitli; resmî üretim/pilot mühürleri ÜRETİLMEDİ.

## Kaynak ve değişmezlik
- Kullanıcının gönderdiği 8 özgün iddaa bülteni PDF'si, yerel oturumda tek tek SHA-256 ile doğrulandı.
- 25 maçın 14.15 ve 14.30'da başlayan Twente–Willem II ile Juventus–Venezia karşılaşmaları yeni mühür adayı olarak dışarıda bırakıldı.
- Kalan 23 maçın M4/C3 ana/alternatif tercihleri, P0 ve P2 karşılaştırmaları **14.56.16 TSİ'de** ayrı araştırma SHA'sıyla sabitlendi.
- Araştırma toplu SHA-256: `f1766f6a94b486c6e91eca9ce3208855e45952faade9fde0841e9b8deabe8ed6`.
- Orijinal PDF'ler bu GitHub Actions koşucusuna yeniden yüklenmedi. Buradaki resmî kaynak kontrolü tahmin oluşturmadı ve daha önceki resmî SHA mühürlerine dokunmadı.

## 14.59 TSİ canlı resmî fikstür kanıtı
Tek resmî geçit çalışması: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/45019949791

- **19/23** karşılaşmanın lig/ev/deplasman/tarih/başlama saati, maç başlamadan önce resmî lig kaynaklarından bağımsız doğrulandı.
- Resmî geçit kanıtı SHA-256: `4e48bbad731a6e11140c11c7281990af073ec160bf5373db432f335db52cb6a5`.
- Üç Fransız maçı, mevcut resmî site sayfasının *pazar* bölümünü atlayan eski parser nedeniyle geçitten geçemedi. Ancak resmî LFP programı https://ligue1.com/fr/articles/l1_article_5839- bu üç karşılaşmanın tamamını ve saatlerini maç başlamadan önce açıkça listeliyor:
  - Paris FC–Angers, 17.00 TSİ
  - Lorient–Rennes, 19.15 TSİ
  - Marseille–Le Mans, 22.45 TSİ
- **22/23** maç için bağımsız resmî kaynak desteği, ilgili başlama saatleri henüz gelmeden ortaya kondu.
- Burnley–Blackburn, resmî EFL duyurusunda https://www.efl.com/news/2026/november/18/referee-appointments--20---26-november/ 12.00 İngiltere / 15.00 TSİ görünüyor; ancak geçit onu 14.59'da doğrulayamadı ve ayrı resmî metin incelemesi maçın başlama saati sınırında/sonrasında yapıldı. **Burnley için GERİYE DÖNÜK yeni resmî maç önü mührü verilmez.**
- SHA'lı kaynak doğrulama eki (yerel konuşma artifaktı) SHA-256: `ea358c628f1122d2e01f0f0d691afdfcc7f10c32b7817f8988d597a3cb06b33b`.

## Çok önemli ayrım
Bu 23 kayıt hâlâ **önceden SHA ile kilitlenmiş araştırma tahminleridir**. Kaynak doğrulama ekinin eklenmesi resmî ilk-PDF `model_first_decision` mührü, resmi pilot sonucu veya maça başlamadan yeniden yürütülmüş `iddaa_pdf_one_step_263.py` anlamına **gelmez**. GitHub koşucusunda o çalışma için özgün PDF baytları bulunmadı; koşucu yalnız bağımsız resmî fikstür kanıtı üretti.

**Resmî kanonik model mühür adedi: 0 yeni.** Önceki bütün mühürlere ve model matematiğine dokunulmadı. Bu 23 maçı ileride değerlendireceksek kaynak kalitesini açıkça etiketlenmiş ayrı araştırma kohortunda izlemeliyiz; resmî pilot listesiyle karıştırmamalıyız.

Gelecekte yeni bültenlerde resmî kaynak doğrulaması, gerçek orijinal PDF baytları ve futbol modelinin maç-önü SHA üretimi tek aynı kanonik zincirde tamamlanmalıdır.
