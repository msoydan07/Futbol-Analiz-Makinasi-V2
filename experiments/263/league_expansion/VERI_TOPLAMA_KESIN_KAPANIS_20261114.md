# 22 lig × iki sezon — VERİ TOPLAMA AŞAMASI KESİN KAPANIŞ
**14 Kasım 2026 · Son maç kesimi: 13 Kasım 2026 · Sadece araştırma dalı**

## Amaç ve sınır
22 lig (13 analiz hedefi, 9 yalnız eğitim araştırması) için 2025/26'nın kaynak arşivi ve 2026/27'nin 13 Kasım'a kadar gözlenen sonuç kaynaklarının tekilleştirilmiş envanteri üzerinde **tek seferlik, kaynak SHA sabitli seçim** yapıldı. Bu kapanış, 2026/27'nin ileride oynanacak maçlarının tamamlandığını veya 13 aktif üretim ligine yükseltme yapıldığını iddia etmez.

## Sonuç — GitHub Actions doğrulanmış
- GitHub Actions PASS: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43620094675
- Ana 10 ligdeki önceki **4.617 sonuç satırı**: aynen korunur, `EXISTING_CORE_4617_FROZEN_RESULTS_ONLY`. Yeni bir 4.617 resmî maç doğrulaması yapılmadı; son 99 kayıttan 43'ü yalnız kısmi resmî eşleşmeyle arşivli.
- Genişleme araştırma kaydı **4.843** = eski 4.505 + 331 Segunda normal lig + 6 Segunda play-off + 1 Belçika resmî karşılaşma.
- Genişlemede **4.218 skor olgusu** kaynak / sonuç kalite denetimi açısından araştırmada kullanılmak üzere seçildi: `SCORE_FACT_RESEARCH_ONLY_QA_PASS`.
- Genişlemedeki **625 kaynak kaydı temiz skor-olgu havuzundan çıkarıldı**: 296 eski tarih/skor HOLD, 325 üst kaynak kullanım hakkı belirsiz, 3 Avusturya lig dışı Conference play-off, 1 Bastia–Red Star terk edilmiş (sahte tamamlanmış 0–0). Kaynak satırları denetim için korunmuştur, **silinmemiştir**.
- **9.460** kaynak-maç satırı = 4.617 eski + 4.218 araştırma skor-olgu uygun + 625 dışlanan; **9.460 yeni eğitim örneği değildir**.
- **Yeni model eğitimine otomatik kabul: 0**. Eski ana M4, model ağırlıkları, oynanmış maç mühürleri ve xG Excel'i değiştirilmedi.

## Kanonik teslim
1. [Satır bazlı kararlar — 9.460 kaynak işaretçisi, skor yeniden yayımlaması yok](./FINAL_9460_SOURCE_ROW_DECISIONS_NO_SCORE_REHOST_20261114.csv). Alanlar: kaynak yolu, 1 tabanlı satır numarası, lig, sezon, anonim maç anahtarı SHA256, kaynak blob SHA, karar, gerekçe.
2. [Toplu makinece okunabilir envanter](./FINAL_9460_RESEARCH_SCORE_FACTS_FILTERED_20261114.json). Kapalı kaynak kümesi, karar sınıfları ve test sayıları.
3. [Tekrarlanabilir SHA sabitli filtre](./final_9460_selection_closeout_20261114.py). Eski dış kaynakları yeniden indirmeden yerel kayıtları denetler. Script yalnız araştırma dalında çalışır.
4. [Tek-seferlik kabul testi](../../../../.github/workflows/263-final-9460-source-selection-closeout.yml). Sayılar kayarsa hata verir, uygunsuz maçları otomatik kabul etmez.

### Kayıtların kullanımı
- `SCORE_FACT_RESEARCH_ONLY_QA_PASS` sadece **maç sonucuna ilişkin araştırma/kalite karşılaştırması için** kullanılabilir; o maçın maç sonrası FT, HT veya xG'si aynı maçın **maç öncesi tahmin girdisi olamaz**. Play-off/lig geçiş maçları normal sezon sonuçlarından ayrı tutulur.
- `EXISTING_CORE_4617_FROZEN_RESULTS_ONLY` kullanıcı tarafından daha önce izin verilen mevcut bazdır; bu seçim eski 4.617'yi yeniden sertifikalandırmaz.
- `EXCLUDED_*` kayıtları seçilmiş veri görünümüne veya yeni modele alınmaz. Hukuki hak veya yeni kaynak kanıtı ortaya çıkmadıkça tekrar test başlatılmaz.
- Kaynak ve özellik kullanım hakkı, gerçek maç önü gözlem zamanı, önceki maç için sonucunun hedef maçtan önce erişilebilir olması, takım kimliği, kronolojik ayrım ve ileriye bakış hatası ayrı bir eğitim kabul sözleşmesidir. Eski geçmişe sahte `available_at` yazılmaz.

## Bilinçli olarak dışarıda kalanlar
- 2026/27 canlı API araştırma kaynağına erişilen, fakat kalıcı yeniden yayımlanabilir arşivi olmayan **633 karşılaşma**: ENG5 190, ESP2 141, ITA2 110, FRA2 108, DNK1 84. Kullanım hakkı netleşene kadar GitHub'a ham kayıt taşınmaz.
- İskoçya, İsviçre, Yunanistan ve Avusturya'da kaynaktan fazla görülen **118 olası güncel maç** yalnız toplu sayı farkıdır, bağımsız tek tek maç kimliği kanıtı değildir. 9.460'a dahil edilmez.
- **1.855 eksik maç sonrası xG** kullanıcı Excel'inde: 90 güncel + 1.765 geçmiş, ayrıca önceki sağlayıcıyla tek taraflı 56. Bu veri ayrı, kullanıcı tarafından ve kaynak izinleriyle tamamlanır.
- 2026/27 devam eden bir sezondur. Sonraki maçlar haftalık yeni veri rutininde ayrı kesim olarak işlenir; kapanmış 13 Kasım arşivine gelecekteki maç eklenmiş gibi davranılmaz.

## Döngü kilidi
Eski 1.775/461/1.268/106/8 doğrulamalarını ve eski 296 HOLD denetimlerini **aynı kaynak SHA ile yeniden çalıştırma**. Önceki kaynakları yeniden indirme, `main` dalına otomatik birleşme yapma, yeni pilot başlatma, M4'ü veya mühürleri değiştirme. Veri toplama projesi bu kesit için **KAPALI**; model mühendisliği ayrı sonraki aşamadır. Haklar/kimlikler onaylanmadan 13 analitik lig üretime alınmaz.

**Kapanış kararı:** Kullanılabilen sonuç kaynaklarını sakla ve karar manifestinden seç; uygun olmayanları görünümden çıkar; erişim veya hak engeli olanları dürüstçe dışarıda bırak; kaynak toplama için aynı döngüyü tekrarlama.
