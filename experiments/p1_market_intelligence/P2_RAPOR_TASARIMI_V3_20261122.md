# Üç Makine — 3 Sütunlu Rapor Ekranı v3

Tarih: 22 Kasım 2026. Tasarım prototipi (üretim otomatik PDF'ye henüz bağlanmadı).

## Kesin görünüm

Her maçın üst satırı: **Takım A - Takım B** ve maç saati.

Altında **eşit üç sütun**, aynı hizada:

| ANA MAKİNE | P0 | P2: UYUMLU |
| --- | --- | --- |
| KG Var | KG Var | İddaa oranı: 1,64 |
| %52,40 | %52,74 | **Fark: 0,34 puan** |

Alt ince çizgi: **Alternatif: 2.5 Üst %50,30** (kırmızı).

- Sütun 1 = Ana M4/C3'ün MS/KG/2.5 arasındaki **kendi zirve tercihi ve kendi yüzdesi**.
- Sütun 2 = P0'ın marjdan arındırılmış MS/KG/2.5 yedi olasılık içindeki **bağımsız zirve tercihi ve kendi yüzdesi**.
- Sütun 3 = **P2: UYUMLU / FARKLI / ORAN EKSİK** → altında **İddaa oranı: ...** (P0 liderinin ilk PDF'deki ham oranı) → altında **Fark: ... puan**.
- Ana ve P0 liderleri farklıysa `Fark: —`; birbirinden farklı maç olaylarının yüzdeleri çıkarılmaz.
- P0 yedi olayın zirvesi eksik fiyat nedeniyle bilinmiyorsa P0 tercih/yüzde ve P2'nin fiyatı/farkı `—` kalır; P2 `ORAN EKSİK` der.
- Rapor ekranında **'Şart 1', 'Şart 2', 'Evet/Hayır'** denetim satırları **gösterilmez**.
- P1 bu üç sütunda bağımsız başka bir makine olarak gösterilmez; yalnız istenirse tekli raporun teknik notunda belirtilebilir.
- Beyaz arka plan, siyah ana yazı, simetrik kutular, Arial benzeri font. **Alternatif** ve hesaplanabilen **fark puanı** kırmızı.
- Fiyat ve seçilen yüzdeler sadece ilk, SHA ile ilişkilendirilmiş iddaa PDF'sinden; ikinci PDF değişiklikleri önceki sabah mühürlü kararı değiştirmez.

## Ekran prototipi

İki sayfalık PDF bu görüşmenin dosyalarına kaydedildi:
`uc_makine_rapor_tasarimi_v3.pdf`. 1. sayfa dört maçlık toplu görünüm, 2. sayfa tekli detay/eksik oran. Model yüzdeleri 22 Kasım araştırma kayıtlarındandır; bugün yeni bahis tahmini olarak iddia edilmez.

**Uygulama durumu**: Sadece tasarım şablonu. Ana üretim PDF raporlayıcısı ve mühürler değiştirilmedi. P2 iki bağımsız lider tek kıyas motoru olarak kalır.
