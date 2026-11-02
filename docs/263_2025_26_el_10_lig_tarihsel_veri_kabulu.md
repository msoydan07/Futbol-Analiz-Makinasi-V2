# 2.6.3 — Eksik 2025/26 UEFA Avrupa Ligi 144 maç veri kabulu ve 10 lig sınırı

**Tarih 2 Kasım 2026; sadece yeni deney dalı.**

Mevcut 432 maç arşivinde `UEFA_EL 2025/26` yoktu;
`openfootball/champions-league` deposunun sabit ve güncel
`2025-26` klasörlerinde `el.txt` mevcut DEĞİL.

Kaynakları ayırdık:
- **Resmî UEFA sonuç arşivi:** https://www.uefa.com/uefaeuropaleague/news/029c-1e9b4e18c28e-3bb76afa22ac-1000--europa-league-league-phase-results-by-team/
  (29 Ocak 2026, tüm 36 takım ve sonuçlar, 288 tekrar).
- **Makine tarafından indirilebilir alternatif (resmî UEFA değil):**
  https://fixturedownload.com/feed/json/europa-league-2025

Yeni kod `experiments/263/europe/uefa_el_2025_26_scope_source_263.py`
şunları uygular:
1. HTTPS JSON feed'i tek kaynak olarak çeker; yeniden yönlendirme
   alan adını, içerik tipini, boyutunu kontrol eder.
2. Yalnız RoundNumber 1–8 dahil; lig aşaması 144 maç, her
   haftada 18 maç, 36 takımın her biri 8 maç koşulunu
   ve toplam 386 golün kaynak uyumunu doğrular.
3. Resmî UEFA sonuç sayfasından **altı bağımsız belirlenmiş
   somut maç tarih/isim/skor kontrolünü** zorunlu kılar.
   Bu altı kontrol 144 maçın tamamını bağımsız UEFA
   doğrulamasına eşdeğer DEĞİLDİR.
4. 2025/26 canonical üyelik kaydına göre **her iki kulüp de**
   mevcut 10 lig kapsamı içinde ve birebir eşleşen
   kimliğe sahipse aday tarihi maç ayrılır.
   Dış veya bilinmeyen kulüp bilgisi için başka lig
   araştırması YOK.
5. Çıktı sadece deneysel ayrı veri alanına / artefakta;
   **model eğitimi, xG katsayısı, UEFA tahmini, pilot, main
   ve 10 lig haftalık veri hattına otomatik entegrasyon YOK.**

Resmî UEFA takım kimliği crosswalk hâlâ doğrulanmadığı
için ad eşleşmesi tam kabul anlamına gelmez.
Gerçek zamanlı model testi ve veri kapsam kararı ayrıca
kanıtlanmalıdır.

Toplu kabul: **tek yeni 2025/26 Avrupa Ligi kaynak
testi ve tek özet**. 432 maçlık eski UEFA
puan/hafta deneylerini tekrar ÇALIŞTIRMA.
