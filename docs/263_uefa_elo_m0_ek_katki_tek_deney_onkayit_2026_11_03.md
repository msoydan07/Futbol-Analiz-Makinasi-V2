# 2.6.3 Avrupa Elo matematik katkısı — M0 / M0+Elo ön kayıt
**Tarih:** 3 Kasım 2026. **Tür:** retrospektif keşif; üretim ve pilot yok.

## Kanıt / sabit kaynaklar
- UEFA 2025/26 132 resmi eşleşme-ID adayı, run 41488522760, dosya 132_UEFA_MATCH_IDS_REVIEW_ONLY.json, SHA-256 6111cb58a7cf25bf81a05dabc73c74f9699fb30aa2fbebb8e1820ce5e9f481ac.
- 132 yerel gol profili, run 41493071435, dosya 132_goal_only_feature_inputs_REVIEW_ONLY.json, SHA-256 902a56410dc6b6b877ad768e593db87ab1f742f7657dc87aa4e88d5f5739decd.
- beyondELO geçmiş Elo dosyası, run 41582947375, source_csv/2025-2026.csv, SHA-256 38470d1d17ba4394e85bdf30827ce7fac476dd4f34cdda9c3b198512934adec3; beyondELO (https://beyondelo.com), CC BY 4.0.
- 167 resmî kanonik isim ↔ beyondELO kaynak ad/slug eşleştirme adayı, run 41585362134, elo_bridge_crosswalk_167.json. Bu kaynakta bağımsız ortak UEFA-ID doğrulaması yok.
- Ön denetim: yapısal 124 maçın tamamı için iki önceki Elo kaydı var; son gözlem gecikmesi en fazla 18 gün. 47 tarihsel kulüp mevcut 167 Elo adayında.
- Önceki M0/M1/M2, 432 maç ve B/C2/C3/M4 deneyleri TEKRAR EDİLMEYECEK. Eski M2 eksik geçmiş sorunu nedeniyle bloke idi. Buradaki Elo kıyası yeni ve eskisiyle eşdeğer değil.

## Önceden kilitlenen karşılaştırma
- Aynı 124 UEFA maçında her iki kol; eğitim 76 (Eylül–Kasım 2025), doğrulama 16 (Aralık 2025), ayrılmış son dönem 32 (Ocak 2026). Bir karşılaşmanın hedef günündeki / gelecekteki Elo asla kullanılmaz; yalnız Elo satırı tarihi < hedef maç takvim günü. 124'ten tek maç eksik olursa karşılaştırma BLOKE.
- M0: her takımın kendi ligi ev/deplasman hücum / savunma göreli gol oranları, rol bazlı k=5 yumuşatma; UEFA ev/deplasman gol baz ortalaması yalnız 76 eğitim maçından. λ_home=UEFA_train_home_mean × home_relative_home_attack × away_relative_away_defense; λ_away=UEFA_train_away_mean × away_relative_away_attack × home_relative_home_defense. Her λ 0.15–5.00 aralığında.
- M0+Elo: aynı M0 girdi ve oranları + tek fark d=clip((home_pre_date_Elo−away_pre_date_Elo)/400,−2,2); λH=clip(M0λH × exp(βd),0.15,5); λA=clip(M0λA × exp(−βd),0.15,5). İkinci lig/ülke bonusu, yerel Elo, HFA katsayısı ve xG YOK.
- β tek katsayı, yalnız 76 eğitim karşılaşmasındaki iki golün Poisson log-likelihood toplamıyla; önceden sabit ridge=20 ceza ve β∈[−1,1]. Seçim, güncelleme, yeniden ayarlama için doğrulama veya Ocak sonuçları kullanılmaz.
- Birincil ölçüt: eşli 1X2 log-loss. İkincil: 1X2 Brier, toplam gol/iki skor Poisson log-loss, 2.5 Üst Brier, KG Brier, CL/EL kırılımı. Aralık ve Ocak ayrı; tarih bloklarıyla önceden sabit seed=263 ve 2000 bootstrap; örneklem çok küçük.
- Bu tarihsel sonuçlarda ilk yayın / first_seen kanıtı YOK; sağlayıcı tarihsel Elo'su maç sonrasında güncelleniyor. Bu yüzden sonuç durumu kesinlikle RETROSPEKTIF_KESIF_NO_LIVE_PREGAME_PROOF. Kaynakların REVIEW_ONLY/model_training_permitted=false işaretleri değiştirilmez; elde edilen katsayı yalnız analitik deneme değeridir, geçerli eğitilmiş/üretim modeli sayılmaz.
- Sızıntısız gerçek geçmiş yayın kanıtı, yeni bağımsız sezon ve gerçek maç öncesinde kilitlenmiş snapshot yoksa, sonuç iyi çıksa bile main/B/C2/C3/M4/100 maç pilot/A-B-C/EV değişmez; Elo→Poisson yetkisi VERİLMEZ.

**Tek yürütme:** GitHub Actions'ı yalnız deney dalında bir defa çalıştır, geçmiş dört artefaktı tekrar indirmeden arşivden oku, SHA+kimlik+tarih kilidini denetle, tek karşılaştırma raporuna karar yaz. Başarısız koşuyu aynı girdilerle tekrar çalıştırma.