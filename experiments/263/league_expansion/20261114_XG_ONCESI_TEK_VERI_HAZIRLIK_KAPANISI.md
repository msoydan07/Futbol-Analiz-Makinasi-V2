# 14 Kasım 2026 — xG öncesi TEK veri hazırlık kapanışı

**Karar:** Kullanıcı 15 Kasım'da 1.855 maçlık xG'yi elle girecek. 625 HOLD, model test veri-kabul ön kapısı ve Excel şablonu kontrolü bugün bitirildi. Eski testleri tekrarlamayacağız; xG'yi almadan matematiğe geçmeyeceğiz.

## Bugün kanıtlananlar

1. [625 araştırma HOLD ve test-kabul ön sözleşmesi](./625_PRE_XG_DATA_ADMISSION_CONTRACT_20261114.json) hazırlanıp salt-okunur kaynak manifestinden bir kez hesaplandı. [GitHub Actions PASS](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43640892268).
2. 9.460 kaynak satırı, 4.617 eski ana sistem skoru, 4.218 yalnız skor-olgusu QA-PASS, 625 kaynak HOLD yerinde. HOLD'lar 200 hatalı ENG3/4 + 96 hatalı ENG5 + 325 hak + 3 organizasyon + 1 terk edilmiş. 200 eski hatalı kaydın 178 skor / 22 skor+tarih **düzeltme kaynak işaretçileri** var; eski yanlış kayıtlar hâlâ dışarıda, 200 yeni maç sayılmadı. ENG5 kaynak HOLD'u olan **96**, kullanıcının **96 mühürlü pilotundan ayrı**.
3. Gerçek maç öncesi girdilerin hedef maçın bitiş skoru, hedef xG, HT sonucu vb. sızıntı yapmaması için güvenli zaman/dış kaynak alanları veri-kabul denetimine dahil edildi. Geçmişte bulunmayan zaman kanıtı uydurulmadı.
4. Eski 39 sonuçlu SHA-mühürlü değerlendirme zaten yapılmış; hiçbir model veya eski değerlendirme tekrar çalıştırılmadı. B/C2/C3/M4 karşılaştırması kullanıcı xG sonrası tek planlı karara kadar **yapılmayacak**. 96 mühürlü eski pilot değiştirilmedi, yeni pilot yok.
5. Kullanıcı tarafından [751 yeni aday kapsam dışı bırakıldı](./751_ADAY_KAPSAM_DISI_KARARI_20261114.md). Bu 751 hiçbir zaman 9.460 kayıt içinde değildi. Yeni özel kasa, paralel depo, yeni hak araştırması yok.
6. Asıl Excel çalışma kitabının **6 sayfa** olduğunu orijinal dosyanın XML'iyle kontrol ettik: BASLA, EKSIK_2026, EKSIK_2025, ESKI_459_KONTROL, HAFTALIK_YENI, GOREV_PLANI. GitHub'daki salt-okunur [1.855 xG güvenlik denetleyicisi](./check_manual_xg_excel_1855_read_only.py) bu yapıya göre düzeltildi, [sentetik GitHub testi PASS](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/43641145578). 90 + 1.765 = 1.855 boş xG satırı; 459 kontrol geçmişi; 56 eski tek taraflı sağlayıcı kaydı yerinde. E, F her ikisi gerçekten ölçülmüş maç sonrası xG olmalı, G maçın doğrudan kaynak URL'si, H kontrol tarihi, I 'TAMAM'; eski K/L ve maç ID M değiştirilmez. 0 ancak kaynak açıkça 0 gösteriyorsa girilir. Kaynak formatı kabulü gerçek xG doğruluk/izin kanıtı değildir.

## Şimdi kullanıcıdan beklenen tek MANUEL İŞ

Bilgisayarda mevcut 1.855 satırlık çalışma kitabında sadece kaynakla doğrulanabilen **maç-sonu xG çiftlerini**, maç URL'sini, kontrol tarihini ve TAMAM işaretini doldurmak. Kaynak bulunamayan satıra tahmin veya 0 yazılmasın. Telefon / ek GitHub operasyonu gerekmez. Kullanıcı dosyayı konuşmaya getirince **o somut doldurulmuş dosya** salt-okunur kontrol edilecek; bugün kullanıcı verisi doldurulmuş gibi gösterilmedi.

## xG sonrası zorunlu kalite kapıları (şimdi kendiliğinden çözülmüş sayılmaz)

- 4.218 araştırma skor-kayıt QA-PASS **model eğitimi kabulü değildir**: bağımsız kullanım hakkı ve gerçek geçmiş maç-önü özellik zaman kanıtı araştırma kayıtlarında mevcut değil. Eski 4.617'deki son 99 kaydın **43** tanesi tam resmî kanıtla yeniden teyit edilmiş değil. 
- xG bittiğinde önce xG sayı/kaynak doğrulaması, hangi maçların kaynak ve zaman bakımından uygun olduğu, sezona göre eğitim/eşit SHA-mühürlü değerlendirme ayrımı kesinleşecek. Geçmiş maçlara yeni xG ekleyip eski mühürleri yeniden üretmek yasak.
- Eksikler yüzünden bir araştırma satırı hâlâ elverişsizse öyle işaretlenir; 22 ligde 44/44 hücre eksiksiz veya 9.460 satırın tümü model-uygunmuş gibi rapor edilmez.
- Kullanıcının karar verdiği **B/C2/C3/M4 — MS, KG, 2.5 Üst** ortak-maçlı **tek değerlendirme** veri kabul şartı gerçekleştiğinde ele alınacak, mevcut eski pilot ve matematik kilidi korunacak.

**Sonuç:** Bugün yapılabilir veri ön hazırlıkları tamamlandı. Şimdiki sıra kullanıcı xG girişinde. Geri kalan veri-kabul dış kanıtı koşulları görünür ve dondurulmuş; bunlar xG bitince de kendiliğinden “PASS” olmaz.

**Değiştirilmeyen şeyler:** Ana M4, 10 lig, 13 analiz / 9 eğitim kararı, 22 liglik dosya kapsamı, B/C2/C3/M4, SHA mühürler, gerçek kullanıcı xG çalışma kitabı, eski anket/model pilot sonuçları ve 9.460 önceki kaynak satırı.
