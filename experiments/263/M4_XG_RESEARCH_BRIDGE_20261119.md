# M4 için xG ek girdisi — kontrollü araştırma bağlantısı (19 Kasım 2026)

## Ne değişti?
- \`m4_integrated.py\`, B/C2/C3, eski SHA mühürleri ve \`main\` **değişmedi**.
- \`m4_xg_support_263.py\`, mevcut M4'ün beklenen ev/deplasman gollerine **geçmiş maçların xG/xGA bilgisiyle** isteğe bağlı bir düzeltme hesaplıyor.
- \`sabah_batch_263.py\` araştırma dalında isteğe bağlı \`--xg-snapshot\` alıyor ve **ayrı** \`m4_xg_evidence.json\` üretiyor. Orijinal tahmin, fiyat kararı ve mühür korunuyor. Mobil raporda M4 ile xG katkılı M4'ün 2.5 Üst ve KG Var yüzdeleri karşılaştırılıyor.

## Girdi ve kalite kapıları
- 10 lig, 2025/26 ve 2026/27. Özel araştırma CSV'si yerelde tutulur, GitHub'a yüklenmez.
- Maç kimliği, ev/deplasman kimlikleri, tarih ve skor; tahminde kullanılan **aynı kabul edilmiş tarihsel skor kaydıyla** eşleşmelidir.
- **Sadece hedef maç tarihinden ÖNCE** oynanmış maçların xG değerleri kullanılabilir. Hedef maçın kendi xG'si veya aynı günün xG'si kullanılmaz.
- 5 büyük ligde Understat; ENG2/NED1/POR1/BEL1/TUR1 liglerinde xgEdge kaynak aileleri seçildi. Şüpheli, başka sağlayıcıdan veya teyidi bekleyen satırlar dışlanır. Bu yüzden sayısal xG'nin tamamı otomatik olarak modele girmez.
- Ev sahibi takımın son 12 **iç saha**, deplasman takımının son 12 **dış saha** maçından hücum xG ve rakibe izin verilen xG hesaplanır. Altı maçlık lig ortalaması yumuşatması ve 0.438 araştırma ağırlığı kullanılır.
- En az 40 geçmiş lig maçı ve her takımın uygun rolde en az 3 maçı bulunmazsa, M4'ün orijinal beklenen golü **aynen** korunur.
- Beklenen gol aralıkları, negatif/sonsuz değerler, duplicate fixture ID ve uyumsuz takım kimlikleri fail-closed davranır.

## Kullanım
Kod, mevcut sabah akışının aynı parametreleriyle çalışır; **ilave** bir özel CSV parametresi verirseniz xG araştırma raporu da üretir:

\`\`\`bash
python experiments/263/sabah_batch_263.py \
  --cohort new100 --day YYYY-MM-DD --input SABAH_MANIFEST.json \
  --history ACCEPTED_RESULTS.csv --baseline FROZEN_BASE.csv \
  --source-acceptance SOURCE_APPROVAL.json \
  --m4-lock experiments/263/m4_lock.json \
  --xg-snapshot /PRIVATE/FUTBOL_263_4618_XG_KILITLI_20261119.csv \
  --report output_batch.json --mobile output_mobile.md
\`\`\`

Tek bir **önceden mühürlenmiş** tahmine xG bilgisi eklemek için (asıl tahmine dokunmadan):

\`\`\`bash
python experiments/263/m4_xg_support_263.py \
  --forecast ALREADY_SEALED_FORECAST.json \
  --history SAME_ACCEPTED_RESULTS.csv \
  --xg /PRIVATE/FUTBOL_263_4618_XG_KILITLI_20261119.csv \
  --out m4_xg_research_sidecar.json
\`\`\`

## Test kanıtı ve önemli sınırlar
- Yerel kod kontrolü: sekiz güvenlik davranışı sınandı (geçmişe bağlılık, sonraki/same-day sızma, kimlik, kaynak, eksik veri, provider, duplicate, sıfır katsayı).
- Sabit 4.618 satırlık özel CSV SHA-256: \`3b13921daafab70aa121fe807fea0a74e0c72f0fc2381366b183f621edea762c\`. 10 ligin her birinde geçmiş kaynak kapısı çalıştırıldı, çok sayıda kabul edilen xG ve bazı dışlanan satırlar görüldü.
- Bu bir **bağımsız ileriye dönük performans kanıtı değildir**. Geçmişte 1.083 maçla bulunan Brier iyileşmesini aynen yeniden üretildi diye iddia etmiyoruz; bu araştırma sürümündeki türetme ve kaynak eleme kuralları ayrı doğrulama ister.
- Üretim kodu, eski kayıtlar, S1/S2, fiyat/EV ve bahis kararı değişmedi. xG as-of yayın sürümü ve kaynak kullanım hakları bağımsız teyit edilmedikçe üretime otomatik alınmamalı.
- \`--xg-snapshot\` **verilmezse** sabah akışının eski davranışı korunur. Bu dosya bulutta otomatik bulunmaz; yerel/özel ortamda sağlanmalıdır.
