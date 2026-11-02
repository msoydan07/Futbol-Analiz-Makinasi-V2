# 2.6.3 — Avrupa CL+EL 2025/26 maç öncesi yerel veri kapsam denetimi

132 maçlık daha önce doğrulanmış *aday* kapsam artefaktı ve SHA-256 kilitli 4.413 maçlık yerel sonuç arşivi yeniden kullanılır. Aynı CL/EL kapsam testi ve UEFA ağ erişimi çalıştırılmaz. 

Her tarihsel UEFA maçı için iki kulübün ilgili 2025/26 liginde o maçın tarihinden **önce tamamladığı** maçların sayısı, dört ve sekiz maç kapsama eşiği, kullanılabilir xG çiftleri sayılır. Aynı günün maçları (saat bilinmediği için) hariçtir. Eşikler tahmin performansı veya model kabulü anlamına gelmez.

**Önemli sınır:** 2026'da derlenmiş arşivden maç tarihine göre geçmişi kesebilmek, kaynak istatistiklerinin o tarihte gerçekten erişilebilir olduğunu kanıtlamaz. Ayrıca UEFA kaynak takım adlarının resmî numerik kulüp ID eşleştirmesi ve 132 maçın her birinin resmî olarak bağımsız doğrulaması henüz yoktur. Bunlar yüzünden model eğitimi, oran/EV, pilot, canlı tahmin, ligler arası güc katsayısı, main veya yerel veriye entegrasyon yasaktır.

Çıktı yalnız deney dalında tek JSON özet + inceleme amaçlı geçmiş maç uygunluğu JSON dosyası. Plan: sonuçta eğer yeterli tarihsel sayı var ama kaynak zaman damgası kanıtı yoksa, matematik testi başlamadan ayrı veri kanıtı şartlarını özetle; 132/288 ortak kapsam testini yeniden çalıştırma.
