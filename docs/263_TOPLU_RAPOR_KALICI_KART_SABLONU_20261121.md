# 2.6.3 — KALICI / ONAYLI TOPLU RAPOR KART ŞABLONU

**Karar:** 21 Kasım 2026 — Kullanıcının görsel örneğiyle onaylandı.  
**Karar ID:** D-OPER-005 (D-OPER-004 üzerine sunum düzeni eklenmiştir).  
**İşletim dalı:** \`experiment/263-toplu-karsilastirma\`.

## Varsayılan tek şablon — değiştirilmez
İlk iddaa PDF'si, adlandırılmış new100 sabah MODEL-ONLY çıktısı ve sohbet içinde hazırlanıp kullanıcıya verilen **tüm toplu analiz PDF'leri** aynı aşağıdaki A4 dikey kart düzenini kullanır. Seçicinin sayısal kararları bu görsel değişiklikten etkilenmez.

- Başlık: **LİG ADI** büyük ve solda (TUR1 => **TÜRKİYE SÜPER LİG**); altında \`GÜN AY YIL · HAFTANIN GÜNÜ · N MAÇ\`.
- Başlık altında bir satır: \`MS 1-X-2 / 2.5 ALT-ÜST / KG VAR-YOK\`.
- **Sayfa başına en çok 6 maç**, hepsi aynı genişlik ve aynı yükseklikte tek tek yuvarlak köşeli kutular.
- Kutunun üstü: sol köşede kapsül **HH:MM**, ortada takım adları **EV - DEPLASMAN**, sağda **01/06** vb. sıra.
- İnce yatay ayraç altında dört sütun, hizaları tüm kutularda aynı:
  **ANA TERCİH | BİZİM % | PİYASA % | FARK (PUAN)**.
  Büyük rakamlar, % bir ondalık Türkçe virgülle; fark yüzde değil **yüzde puan**, açık \`+/-\` işaretiyle.
- Kutunun alt solu **Alternatif: ... %...**; alt sağı **Ana iddaa oranı: ...**. Yalnız fark ve alternatif kırmızı; diğer her şey siyah; zemin beyaz; çizgiler ince açık gri. Arial'e yakın Arimo, sade ve dengeli.
- Alt dipnot: **Piyasa %**, yalnızca kullanıcının ilk orijinal iddaa PDF'sindeki aynı pazar ailesi oranları marjdan arındırılabildiyse gösterilir. \`Fark = Bizim % - Piyasa %\`. Oranlar ana/alternatif tercihi değiştirmez. Veri olmadığı yerde **VERİ YOK / —**; başka bookmaker, varsayılan veya uydurma oran kullanılamaz.
- Teknik veri blokajı \`TEKNİK ENGEL\`; hesap yapılmamış maçlarda yüzdelik veya sahte tercih yok. Model tarafından geçerli PAS, teknik engelden farklıdır.
- Örnek tasarımda kurgusal değerler olabilir; **örneğin rakamlarını gerçek maç raporuna kopyalama**. Yalnız gerçek model-first v4 SHA'lı tercih/olasılık ve kullanıcının kaynağı kullanılır.
- **Tekli rapor** ayrı, zaten onaylanmış dört-kutulu sayfa düzeninde korunur. Bunun düzeni veya eski imzalar bu değişiklikle değiştirilmez.

## Tek uygulama kaynağı

- Ortak kart geometrisi: \`experiments/263/iddaa_pdf_approved_layout_263.py::_draw_grouped_cards\`.
- Kullanıcı iddaa PDF'siyle: \`render_batch(session,target)\` — SHA zinciri doğrulanır, piyasa oranları yalnız kullanıcı PDF'sinden hesaplanır.
- Oransız yeni sabah: \`render_model_only_batch(day,rows,target)\` — özgün v4 SHA imzası ve karar kimliği doğrulandıktan sonra aynı kartlar, piyasa/oran **VERİ YOK**. \`sabah_mobile_model_only_263.py\` bu fonksiyonu kullanır.
- Sohbet sırasında ayrı PDF sunumu üretilirse de burada belirtilen aynı beyaz kart geometrisine uyulur; iki-sayfalık model olasılık tablosu artık varsayılan **toplu** rapor değildir.
- Sürüm yükseltme için kullanıcıdan açık farklı tasarım onayı gerekir; onaysız başlık, kutu sırası, vurgular veya sütunlar değiştirilmez.

## Kanıt sınırları
Bu kalıcı görsel düzen analizin güvenirliğini veya bağımsız ileri doğrulamasını artırdığı iddiasını taşımaz. Önceden mühürlü B/C2/C3/M4 modelleri, M4+kalibre C3 v4 karar katmanı, tahmin SHA'ları, sonuç arşivi, iddaa 1. PDF/2. PDF ayrımı değişmez.
