# 2.6.3 Maçkolik ismi → resmî maç → analiz kapısı

- Kullanıcı Maçkolik'te gördüğü **ev sahibi – deplasman** adlarını söyler. Maçkolik sadece ad kaynağıdır; maçın resmî teyidi değildir.
- Önce existing `Registry` ve `team_name_resolver.resolve` üzerinden aynı sabit takım kimlikleri aranır. Yeni takım kimliği üretilmez.
- `data/team_aliases_reviewed.csv` yalnız internette örneği kontrol edilmiş Maçkolik yazımlarını, kanıt URL'sini ve kayıttaki adı bağlar. Belirsiz eşleşmeler **REVIEW_REQUIRED**.
- `analyze_named_match_gate.run`, yalnızca kullanıcının bildirdiği iki takım için mevcut ligin resmî adaptörünü sorgular; tek kayıtlı takım ID'ye bağlı ad varyantlarını en fazla sekiz denemede kullanır. Toplu fikstür/Modül 0 YOK.
- Resmî gözlemdeki ev/deplasman takımları aynı ID'lere ve sıraya karşılık gelmelidir; eski `verify_named_match` resmî alan adını, UTC saatini ve kaynak güncelliğini ayrıca denetler. Maç bulunamazsa analiz başlatılmaz.
- **Sınır:** mevcut `verify_named_match` saat yayımlanmamış maçı tam VERIFIED yapamaz. Deneysel yerel `mackolik_identity_gate_263.py` paketi tarih-doğrulama ile saat-doğrulamayı ayrı ele alır; bu genişleme üretim/legacy doğrulayıcısına otomatik eklenmedi.
- Mevcut resmî adaptörler her ligde bütün eşleşmeleri kapsamayabilir; bir kaynak URL'sinin kayıtlı olması doğrulama değildir.
- İlk 11 açıklanmaması raporu durdurmaz; doğrulanmayan haber λ hesaplarını değiştirmez. Matematik, pilot, EV ve gerçek maç kayıtları değiştirilmedi.
- Bu commitle **yalnız deney dalındaki** kapı ve kaynaklı ad listesi güncellendi. Matematik deneyleri tekrar koşulmadı.
