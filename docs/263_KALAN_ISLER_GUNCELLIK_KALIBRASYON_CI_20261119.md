# Futbol 2.6.3 — Kalan iki işin kontrolü (19 Kasım 2026)

**Sonuç:** Veri bütünlüğü ve ikincil kaynak sayımı kontrol edildi; aday tercih yüzdeleri tarih sıralı test edildi; araştırma GitHub CI doğrulandı. **Tam resmî sonuç aralığı ve gerçek kullanıcı PDF uçtan uca onayı henüz yok.**

## Veri durumu

- 4.618 özel skor satırı SHA-256 doğrulandı. 4.413 eski satır korunmuş ve 205 skor satırı eklenmiş. Özel xG ham verileri kamusal depoya yüklenmedi.
- 10 ligin 2026/27 sezonu maç adedi, *open-matchday* adlı bağımsız ikincil GitHub kaynağındaki adediyle 10/10 eşleşti; bu, **resmî federasyon teyidi değil**.
- Sekiz Kasım sonrasında bu ikincil kaynaklarda yeni maç görünmüyor. Ancak çoğu kaynak **10 Kasım**, Portekiz **16 Kasım** güncellenmiş: 9–19 Kasım arasının eksiksizliğini tek başına kanıtlamaz.

| Lig | 2026/27 skor | İkincil kaynak | Son skor | İkincil kaynak güncelleme |
|---|---:|---:|---|---|
| BEL1 | 99 | 99 | 2026-11-08 | 2026-11-10 |
| ENG1 | 100 | 100 | 2026-11-08 | 2026-11-10 |
| ENG2 | 180 | 180 | 2026-11-07 | 2026-11-10 |
| ESP1 | 119 | 119 | 2026-11-08 | 2026-11-10 |
| FRA1 | 90 | 90 | 2026-11-08 | 2026-11-10 |
| GER1 | 81 | 81 | 2026-11-08 | 2026-11-10 |
| ITA1 | 110 | 110 | 2026-11-08 | 2026-11-10 |
| NED1 | 108 | 108 | 2026-11-08 | 2026-11-10 |
| POR1 | 98 | 98 | 2026-11-08 | 2026-11-16 |
| TUR1 | 99 | 99 | 2026-11-08 | 2026-11-10 |

## Tahmin yüzdelerinin zaman sıralı değerlendirmesi

- Eski 496 maçtan **286 ana aday**, **210 PAS**; 286 adayın tümünde ortalama model olasılığı %69,5, gerçekleşme %62,6. Bu örneklem geçmiş araştırmalarda da kullanılmış; bağımsız son test değil.
- 9–25 Ekim (161 aday): ortalama model yüzdesi %69,3, gerçekleşme %57,8. Bu dönemin verisiyle tek parametreli geçmişe yönelik olasılık düzeltmesi hazırlandı.
- 26–31 Ekim (47 aday): düzeltme Brier skorunu 0,2110 → 0,2143 ile **kötüleştirdi**.
- 1–8 Kasım (78 aday): ham model ortalama %70,0 ve gerçekleşme %70,5; düzeltme Brier skorunu 0,2004 → 0,2150 ile **kötüleştirdi**.
- 2.5 Alt: 30 adayın yalnız 11’i doğru (%36,7); ortalama beklenen %65,1. **Yüksek güvenilirlik sorunu / inceleme gerektirir.** 2.5 Üst: 90 adayın 57’si doğru (%63,3), ortalama tahmin %71,3.
- Genel yüzde kırpması/düzeltmesi canlı makineye uygulanmadı. Kayda alınacak uyarı: Alt 2.5 için ham tahmine aşırı güvenmek güvenli değil. Farklı pazarların gelecekteki performansı için sonuç dışından bağımsız kanıt gerekiyor.

## GitHub otomatik test sonucu

- 19 Kasım yeni araştırma workflow’u önce geçersiz iş kimliği nedeniyle çalışmıyordu; düzeltme commit `9d165020b2cdf44ac6cd9608dd8fcb9b8e99d2f2` ile yapıldı.
- [GitHub Actions 44560118778](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/44560118778) artık **SUCCESS**. Test, import ve orijinal model koruma adımları geçmiştir; gerçek iddaa PDF içermediği için canlı kabul değildir.

## Açık kapılar

1. Resmî lig/federasyon kaynaklarından **9–19 Kasım 2026** dönemindeki bütün oynanmış (erteleme dahil) lig maçlarının eksiksiz olduğu teyit edilmeli. Stale ikincil kaynak bu işi tek başına bitirmiyor.
2. Gerçek kullanıcının ilk iddaa PDF’si geldiğinde resmî fikstür + 4 model + orandan bağımsız ana/PAS + SHA + PDF raporu uçtan uca denenmeli. İkinci PDF/ilk 11 yalnız ayrı futbol yorumu olarak kaydedilecek.
3. Aday yüzdelerine şu an otomatik genel düzeltme uygulanmayacak. 2.5 Alt gibi tutarsız pazarları kullanıcıya özellikle belirterek ihtiyatlı yorum yapmak gerek.

**Değişmeyen kararlar:** İddaa oranları yalnız beşinci referans, ana tahmini yönetmez; tek mühür; ana M4/96 eski pilot/önceki SHA kayıtları değiştirilmez.