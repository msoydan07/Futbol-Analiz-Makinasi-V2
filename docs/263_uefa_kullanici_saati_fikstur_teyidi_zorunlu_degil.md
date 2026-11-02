# 2.6.3 — Kullanıcı maç ve başlama saati verirse UEFA fikstür teyidi ön analiz için zorunlu değil

Karar: 2 Kasım 2026. Uygulama yalnız experiment/263-toplu-karsilastirma dalındadır.

Yeni araştırma giriş noktası: experiments/263/europe/uefa_user_time_research_263.py

1. Kullanıcı iki takım ve Türkiye saatini söyler; maç tarihi bağlamda açıksa aynen kullanılır. Eksik/gerçekten belirsizse yalnız tarihi netleştir.
2. Yerel canonical index üzerinden her iki takımın da 2026/27 sezonundaki 10 ligden birinde olduğu doğrulanır. Kapsam dışı veya belirsiz kimlikte başka hiçbir araştırma çağrılmaz.
3. Kullanıcı saati Europe/Istanbul olarak yorumlanır, sonraki yedi günde olmalı. Bu saat resmî teyit değil; USER_SUPPLIED_NOT_VERIFIED olarak açıkça etiketlenir.
4. Uygunsa gerçek futbol istatistikleri, xG/xGA, takım gücü, kadro ve güncel veriler güvenilir kaynaktan araştırılır. Resmî UEFA fikstür sayfasını her seferinde tekrar bulmak zorunlu DEĞİLDİR.
5. Oyuncu kadrosu henüz açıklanmadıysa çalışma durdurulmaz; veri icat edilmez.
6. Daha önceki isteğe bağlı official article ve web handoff kaynak doğrulama araçları ana analiz ön koşulu olmaktan çıktı. Zamanında doğrulanmış gerçek maç/pilot kaydı için bağımsız başlangıç saati ve maç kanıtı hâlâ gerekir.
7. Bu yeni kod yalnız araştırmaya izin verir. UEFA güç motoru ve dört üretim modelinin Avrupa uyumu hâlâ kanıtlanmadı. Yeşil test gerçek tahmin, 17 bölüm veya 100 maçlık pilot kabulü değildir.

Testlerde örnek eşleşme ve saatler KURGUSAL girişlerdir, resmî maç vardır iddiası DEĞİLDİR.
Main, 10 yerel lig, 4 motor, güncelleme, A/B/C ve pilot değişmemiştir.
