# 2.6.3 — 4.617 Maçlık Sonuç Arşivinin M4 Araştırma Motoruna Bağlanması
**Tarih:** 10 Kasım 2026  
**Dal:** `experiment/263-toplu-karsilastirma`

## Durum: 4.617 skor verisi gelecek yeni maç analizleri için aktif araştırma girdisi

- 4.518 özgün kabul edilmiş satır, `data/quad_accepted_263/extended_history.csv`, SHA256 `1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9`, **değişmedi**.
- 99 yeni, daha önce 99/99 tarih/takım/skor eşleşmesi yapılmış sonuç `data/quad_accepted_263/completed_99_results_only_20261110.json` içinde ayrıca korunur.
- 4.617 satırlık yalnız maç sonuçları veri dosyası `data/results_only_263/2026-11-10_completed_4617_scores_only.csv`, SHA256 `637b8597ac5bf479934a0b66aaed726b5fc30c20d9a5e9b4a770913cf9d68a89`.
- 9 eski ENG2 kayıtlarının içerikleri aynen korundu; 99 yeni satırdan şut, korner, kart ve başka eksik/denetlenmemiş ayrıntılı istatistikler alınmadı.
- Yenilenen yeni100 sabah ve eski dört-modelli tek-maç iş akışları, **artık bu 4.617 satırlık dosyayı ve açık kaynak sınıfı manifestosunu** (`data/results_only_263/4617_research_input_provenance.json`) kullanır.
- M4 ile B/C2/C3 matematik fonksiyonları, 2025/26 DEV kilidi, eski 40 mühür, LITE ve basketbol değiştirilmedi.
- Motor **10 ligin tamamını her seferinde maç maç simüle etmez**: istenen ligin yalnız maç tarihinden önceki, normal tam süre oynanmış geçmiş satırlarını ilgili model fit'ine alır.
- Yeni100 arşivindeki daha önce mühürlenmiş 8 Kasım maçları yeniden hesaplanmaz veya geriye dönük güncellenmez.

## Bağımsız kaynak statüsü — kesin ayrım

Bu yükseltme **araştırma kullanımına** alınmıştır, bütün 99 maçın resmî federasyon tekil maç kimliği onaylandığı iddiası değildir. Yeni skorlar için gözlem sınıfları: 28 lig/federasyon+sağlayıcı araştırma uyuşması; 28 doğrudan lig/kulüp skor sayfası; 43 ikincil skor + kısmi resmî fikstür çapraz kontrolü. Bu durum mühür verisinde `APPEND_ONLY_4617_PUBLIC_RESULTS_ONLY_RESEARCH_NOT_OFFICIAL_ID_VERIFIED` olarak açıkça işaretlenir; insan kaynak onayı bayrağı **false**, resmî bahis onayı **false** kalır.

## Gerçek GitHub testi ve dal devri

- [7/7 CI regresyon, asıl 4.617 veriyle gerçek M4 fit farkı ve dört-model/sabah/telefon-mühür testleri](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42817490005) — SUCCESS.
- En son kaynak SHA'ları 4.413 temel, 4.518 eski, 4.617 yeni **üçü de doğrulandı**.
- Testte kullanılan sahte fikstür **yalnızca geçici test dizininde** oluşturuldu; gerçek yeni tahmin gibi kaydedilmedi.
- İş akışları `263-sabah-new100-on-request.yml` ve `263-quad-forward-on-request.yml` yeni dosya ve kaynağı okuyor.
- Dal devri 10 Kasım 2026'da `experiment/263-toplu-karsilastirma` üzerine ileri yönlü (fast-forward) yapıldı. O sıradaki dal SHA `b93c2f6825afcfed7c82b112a5ddc5159a6c53c9`. `main` değiştirilmedi.

## Tek sonraki iş

Yeni gerçek bir maç geldiğinde **resmî canlı fikstürü önce doğrula**, 4.617 kaynakla gerçek maç öncesi sabah tahmini üret ve SHA mühürle; sonuçtan sonra aynı mührü gerçek sonuçla kıyasla. **Yeni 99 maç için aynı kaynak araştırmalarını yeniden başlatma.** Gelecekteki 99'luk veya başka sonuç gruplarını arşive eklerken ayrı kanıt sınıflarını koru; model formüllerini kör pilot performansı olmadan değiştirme.
