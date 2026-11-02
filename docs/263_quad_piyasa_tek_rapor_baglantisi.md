# 2.6.3 salt-okunur dört model + oran + A/B/C tek rapor bağlantısı

2 Kasım 2026. `experiment/263-toplu-karsilastirma` deney dalı.

- Kullanıcı bir maç adı söyler; mevcut resmî fikstür kapısı **önce** çalışır.
- Sabit tarihsel veri kullanımı halen yalnız OFFLINE/ön izleme kabulüdür. 17 bölümlük mevcut kabul kuralı bozulmaz.
- İsteğe bağlı `--include-four-model-market-reference` bayrağı, model matematiğini mevcut dondurulmuş kodlardan ayrı ayrı çağırır: B, C2, C3, M4. `forward_quad.predict_quad_from_verified_gate` çağrılmaz (o fonksiyon kayıt yazar).
- `model_preview.md` içine dört modelin MS 1/X/2, 2.5 üst ve KG var tahminleri ile piyasa karşılaştırması ayrı eklenir. JSON eki `readonly_four_model_market_reference.json` adındadır; **pilot kaydı değildir**.
- Fiyat sağlayıcı varsa aynı analiz isteğinde **bir kez** çağrılır; C2 karar eki ile dörtlü piyasa kıyası aynı kaynaktan gelen gözlemleri tüketir. MS/KG/1.5/2.5/3.5 aynı kaynak/saat ve tam karşı fiyatlar olmadan kıyaslanmaz.
- Canlı fiyat sağlayıcı bugün otomatik bağlı değildir: bu yüzden CLI'da fiyatlar **DOĞRULANAMADI** kalır.
- Piyasaya yakın model ana modele dönüştürülmez. C2 mevcut kanonik model, M4 deneysel. A/B/C onayı, kupon, kayıt ve model ağırlıklandırması yok.
- Mevcut `main`, Salı veri yenileme zamanlayıcısı ve tahmin defteri değişmedi.
