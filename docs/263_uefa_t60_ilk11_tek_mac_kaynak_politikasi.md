# 2.6.3 Avrupa T−60 — İlk 11'den tek seferde maç kimliği kontrolü

**Karar: 2 Kasım 2026.** Kullanıcı tek maçın iki takımı, tarihini ve
Türkiye'deki başlama saatini bildiriyor. UEFA'nın tüm fikstürünü yeniden
doğrulama **zorunlu değil**. Önce 2026/27 10 lig kapsamı kontrol ediliyor.

## Uygulanacak pratik akış
1. İki kulüp 10 ligdeyse bildirilmiş kickoff ile veri analizi
   araştırması başlar. Kullanıcının saati **doğrulanmamış kaynak** olarak
   saklanır; yeni UEFA fikstür araştırması otomatik başlatılmaz.
2. **T−120 ... T−0** aralığında, öncelikle ilgili kulüplerin resmî
   maç günü ilk 11 açıklaması, UEFA maç merkezi veya güvenilir
   maç merkezlerinin **tek maç sayfası** incelenir.
   LiveScore, FotMob, Sofascore, ESPN, Maçkolik alternatifleri.
   Rastgele haberden tahmini kadro kabul edilmez.
3. Kaynakta iki kulüp, turnuva, tarih ve varsa kaynak kickoff'u,
   ev/deplasman yönü ve **CONFIRMED** ilk 11 kesinleşme durumu
   görünmelidir. İki taraf için 11'er farklı oyuncu
   listelenmeli. Bu tek kaynak maçın doğru olduğuna
   dair pratik kimlik çapasıdır: önce tüm fikstürü aramak gerekmez.
4. Kaynak kickoff'u kullanıcı saatinden 15 dakikadan fazla
   farklıysa **kaynak/maç uyuşmazlığı** olarak işaretlenir;
   yanlış maçın oyuncuları analizde kullanılmaz.
5. Kadro açıklanmadıysa/erişilemiyorsa sakatlık, takım formu,
   xG vb. kaynaklı maç öncesi araştırma **durmaz**.
   **İlk 11 doğrulanamadı** durumu yazılır. Kadro tahmin edilmez.
6. Kadrolar doğrulansa bile taktik değerlendirmesi yapılır,
   modelde kayıtsız gol çarpanı, EV veya pilot kaydı üretilmez.
   Sağlam etki hesabı ancak veri ve model deneyleri sonrasında.
7. Yeni kod `experiments/263/europe/uefa_t60_lineup_overlay_263.py`
   yalnız maç kimliği ve lineup kaydı **biçim denetimi** yapar.
   Gerçek siteleri GitHub'dan çektiğini iddia etmez.
   `CONFIRMED_LINEUP_SOURCE_CLAIM_MATCHED_AWAITING_SOURCE_REVIEW`
   çıktısı tek başına kaynak doğrulaması değildir.
   ChatGPT web'de veya başka bir bağımsız güvenilir adapter'da
   **kaynağın kendisi** okunmuşsa o teyit kullanıcıya
   ayrıca kaynakla raporlanır. Kodda yeni servis
   bağlantısı bu aşamada henüz yapılmadı.

## Kaynak dayanağı
- UEFA Şampiyonlar Ligi 2026/27, Madde 55.04:
  resmî maç kadrosu en az 75 dakika önce teslim edilmeli.
  https://documents.uefa.com/r/Regulations-of-the-UEFA-Champions-League-2026/27/Article-55-Match-sheet-Online
- UEFA Avrupa Ligi 2026/27, Madde 55.04:
  aynı 75 dakikalık kural.
  https://documents.uefa.com/r/Regulations-of-the-UEFA-Europa-League-2026/27/Article-55-Match-sheet-Online
- LiveScore ilk 11 sayfa bilgisi:
  https://help.livescore.com/hc/en-gb/articles/38995784316562-Can-I-see-football-line-ups-before-a-match

**Main ve mevcut 10 lig, B/C2/C3/M4 modelleri, Salı güncellemesi, A/B/C,
100 pilot ve önceden kabul edilen testler değişmedi.**
