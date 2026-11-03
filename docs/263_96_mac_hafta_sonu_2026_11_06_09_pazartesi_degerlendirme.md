# 2.6.3 — 96 Maçlık Hafta Sonu ve Pazartesi İncelemesi

**Karar:** 4 Kasım 2026'da, ilk maçtan önce 100-maç hedefi kullanıcı isteğiyle **6–8 Kasım 2026 için sabitlenmiş 96 fikstür adayı** olarak değişti. 9 Kasım Pazartesi TSİ genel değerlendirme yapılır. **Bu belge maç önü tahmin kaydı değildir.**

## Değiştirilemez aday evreni
- Önceden GitHub'a yazılan [96 maçlık liste](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/blob/077bfeb22a5c3caec9ffa69693a608598eb34764/experiments/263/local_leagues/2026-11-06_09_10_league_date_only_candidates.json), blob SHA `803378e8ef0f1f285a3393a7231567eea8f25e80`: **Cuma 10, Cumartesi 44, Pazar 42, Pazartesi 0**.
- Resmî başlangıç saatlerini T−60'da yeniden doğrula. İlk araştırmada 48 saat resmî, 48 saat yardımcı kaynak statüsünde idi. Yanlış/ertelenen/oynanmayan/adı eşleşmeyen maçlar açıkça dışarıda bırakılır; sonraki hafta ekleme veya geriye dönük tahmin YOK.
- Kullanıcı tüm 96 takvim adayını önceden uygun bulmuştur. Tek tek eski otomatik maç bulma (Modül 0) veya bahis getirisine göre sonradan seçim YOK.
- **Gerçek kilit sayısı N** yalnız resmî fikstür teyidi, gerçek canlı veri kabulü, T−60 civarı analiz ve maç başlamadan GitHub commit+SHA kanıtı olan kayıtları sayar. 96 aday=96 başarılı kayıt demek değildir. Sayısal limit 96'ya ayarlanmıştır; mevcut kodda tam 96'lık aday üyeliği otomatik bloklanmıyor; Pazartesi listeyle tek tek denetlenmeli.
- İlk 11 henüz açıklanmamış olması modeli durdurmaz; yayınlanmış gibi raporlanmaz. B/C2/C3/M4 formülleri ve ayar kilitleri değişmez.
- Mevcut A/B/C deneysel; resmî onay yok. Harçlık S1 ve S2 gölge defterleri sadece maç **başlamadan** ayrıca kilitlenmişse sonradan değerlendirilebilir. Gölge kodu henüz devrede değilse durum `NOT_IMPLEMENTED`, sonradan seçki yazılmaz.

## 9 Kasım Pazartesi tek rapor
1. **96 aday → resmen doğrulanan → oynanan → kickoff öncesi gerçek kayıt N → sonuçlanan kayıt N_final → dört modelin ortak olduğu N_common.** Her eksik açık neden koduyla açıklansın.
2. **Dört model:** 1X2 isabeti, Brier ve log-loss; KG ve 2.5 üst/alt; model kapsaması, aynı maçlardaki eşleşmiş karşılaştırmalar, lig kırılımları.
3. **S1:** yalnız önceden kayıtlı yüksek olasılık filtresinin seçtiği/pas geçtiği maçlar; isabet ve kapsama. **S2:** yalnız doğrulanmış karşılıklı fiyatlarda sanal 10 birim tekli bahisler; getiri, ROI, kayıp serisi; oran yoksa `UNPRICED`/hesaplanamaz.
4. **25 kayıt ara kontrolü:** teknik bütünlük ve tarih sızıntısı; parametreleri değiştirme. 96 kayıt olmazsa yine 9 Kasım'da gerçek N ile rapor yap; haftaya dört maç bekleme.
5. **Dürüst belirsizlik:** 96 karşılaşma sadece üç takvim gününde planlandı. Mevcut tarih-blok bootstrap aralığı için **en az 10 farklı tarih gerekir**. Bu nedenle raporda `CI_NOT_AVAILABLE_THREE_DAYS`; istatistiksel model üstünlüğü, garantili kâr veya kalibre A/B/C ilan edilmez.
6. Başlama saatleri doğrulanmadan model kilidi uydurulamaz. Maç sonrası yeni skor dosyaları önceki tahminlere dokunmaz.

**Zamanlama:** Cuma–Pazar boyunca mevcut T−60 uyarıları; **Pazartesi 9 Kasım** genel sonuç denetimi. Raporun oluşması için skorların kesinleşmiş ve kayıtların erişilebilir olması gerekir. Bu protokol revizyonu hiçbir maçın analizini/uyarısını otomatik gerçekleştirmiş sayılmaz.
