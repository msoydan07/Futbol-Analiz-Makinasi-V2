# 2.6.3 — 2025/26 Şampiyonlar + Avrupa Ligi tek sezon 10 lig kaynak/kimlik birleşim denetimi

**Karar tarihi: 2 Kasım 2026.** Bu bir yeni veri/kimlik kabulü;
eski 432 maçlık puan/xG/Poisson deneyini yeniden çalıştırmaz.

Bu iş paketinde `uefa_cl_el_union_scope_263.py`:

- **CL:** 2025/26 lig aşamasının 144 maçı/487 golünü daha önce
  dondurulmuş OpenFootball SHA'dan okur; 6 somut skor/tarih
  çapasını resmî UEFA'nın 2025/26 maç sonuç listesine karşı
  önceden belirler.
- **EL:** Halihazırda tek kaynaktan alınmış 2025/26 144 maç/386
  golü, önceki decoder ve 6 resmi UEFA skor/tarih
  çapası üzerinden yeniden kullanır. Bu model testi değildir.
- **Kimlik:** Aynı sezonda 2025/26 yerel canonical 10 lig üyelik
  kayıtlarını kullanır, 2026/27 ile sessizce değiştirmez.
- CL expanded official club names ile canonical kısa adları
  arasında 19 *tekil ve açık listelenmiş* eşleme vardır.
  Dayanak:
  - UEFA 2025/26 CL kulüp listesi:
    https://www.uefa.com/uefachampionsleague/news/0296-1d21e9bdf7e4-808a7511165c-1000--2025-26-champions-league-format-dates-draws-final/
  - UEFA 2025/26 CL bütün sonuçlar:
    https://www.uefa.com/uefachampionsleague/news/029c-1e9a2f63fe2d-ebf9ad643892-1000--champions-league-2025-26-all-the-results/
  - OpenFootball tam takım adları SHA:
    https://github.com/openfootball/champions-league/blob/abfaeddc2ee3d14f99ecc163c9ddb46cb4d67cef/2025-26/cl.txt
- Özellikle kaynağın `AS Monaco FC (MCO)` etiketi,
  **ülke koduyla** dışarı atılmaz; Monaco'nun canonical
  `FRA1` üyeliği esas alınır.
- Bilinmeyen takım adları/hakikaten dış ligde olan takımlar
  için yeni ülke ligi araştırması yapılmaz.
- İki takımın da 2025/26 10 lig içinde bulunduğu maçlar
  ayrı `REVIEW_ONLY` veri paketi olur. Kaynak yönü,
  skor, turnuva, 2025/26 sezonu ve canonical **aday**
  kimliği saklanır.
- Bu adaylar henüz UEFA kulüp-ID'siyle *tam kanıtlanmış*
  değil; yalnız 12 sabit resmî çapa var. Bütün 288
  maçın resmî maç sayfası düzeyinde doğrulandığı
  iddia edilmez.
- Aynı 10 lig arasında maç yapanların **bağlantı grafiği**
  yalnız maç *sayısıyla* ölçülür; veriden henüz takım
  gücü, xG veya kazanma olasılığı hesabı yapılmaz.
  10 ligde sadece örneklemde UEFA takımı yoksa bunun
  bir veri boşluğu olduğu ayrı raporlanır.

## Çıktı

`data/europe_staged_263/2025_26_cl_el_union_audit/`
üç dosya: `*_union_report.json`, `*_review_only_matches.json`
ve `*_summary.md`. GitHub Actions artefaktı:
`263-uefa-2025-26-cl-el-ten-league-single-coverage`.

**Tek kabul deneyi → tek rapor.** Model seçimi, M0/M1/M2
toplu testine ancak sezon-uyumlu maç öncesi yerel güç
özellikleri, kaynak ID'leri, seçim yanlılığı ve kronolojik
dış test kapandığında gidilecek.

Main, 10 lig, Salı güncellemesi, B/C2/C3/M4, 17 bölüm,
ilk 11, A/B/C ve 100 maç pilotu DEĞİŞMEDİ.
