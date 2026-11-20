# Futbol Maç Analiz Makinası V2

Temel analiz şartnamesi: **2.6.2 (değişmeyecek)**. Bu depo temiz kod altyapısıdır; eski depo korunur.

## 2.6.3 operasyonel kodun gerçek konumu (20 Kasım 2026)

GitHub varsayılan `main` dalı, eski 2.6.2 başlangıç/iş-akışı iskeletidir; **2.6.3'ün çalıştırılabilir kodu burada yoktur**. Güncel 2.6.3 B/C2/C3/M4 normal maç önü hesaplama kodu, veri/kabul testleri ve isimli `new100` iş akışı `experiment/263-toplu-karsilastirma` dalındadır. Bu yüzden yalnız `forward_quad.py` dosyasını `main` dalına kopyalamak çalışır bir motor sağlamaz.

- [Normal B/C2/C3/M4 hesaplama kodu](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/forward_quad.py)
- [Gerçek `new100` sabah iş akışı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/.github/workflows/263-sabah-new100-on-request.yml)
- [Dört modelli maç isteği iş akışı](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/.github/workflows/263-quad-forward-on-request.yml)
- [B/C3 adaptif Poisson sınır testi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/experiment/263-toplu-karsilastirma/experiments/263/test_quad_poisson_tail_extension_263.py)

B/C3 Poisson dağılımı hesaplanırken eski 0–10 gol matrisinin kuyruk olasılığı %0,1'i aşıyorsa, **normal modelin içinde** aynı gol beklentileriyle dağılım hassas biçimde genişletilir. Bu, ayrı bahis/karar kuralı değildir. B/C3 öğrenme matematiği, M4, mevcut mühürler ve eski raporlar değiştirilmez. İki gerçek maç önü giriş noktasında regresyon testi uygulanır. `main` dalına tüm 2.6.3 sistemi için ayrı, tam kapsamlı ve güvenli yayımlama gerekir; bu kayıt o yayımlamanın yapıldığını iddia etmez.

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
| 1 — Kimlikler | Birim testleri geçti; gerçek takım eşleştirmeleri bekleniyor | `identity.py` | `test_identity.py`, GitHub Actions yeşil (kullanıcı teyidi), dal: `feature/01-kimlikler`, commit: `4215c1e` |

Bir aşama ancak kabul kriteri ve test kanıtı kaydedilince tamamlanır. Yeşil CI tek başına matematiksel doğrulama değildir. Tamamlanan modül yeniden yazılmaz. Aynı iş için paralel modül/klasör açılmaz. Değişiklik olmadan başarısız test tekrarlanmaz.

## İlk işin kabul kriteri
10 ligde iki sezon boyunca takım kimlikleri tutarlı; aynı takım farklı yazımlarda aynı kimliğe eşlenir; farklı takımlar yanlışlıkla birleştirilmez; maç kimlikleri benzersiz ve tekrarlanan veri alımlarında sabittir. Bu özellikler somut test çıktısıyla kanıtlanmadan aşama 1 bitmiş sayılmaz.
