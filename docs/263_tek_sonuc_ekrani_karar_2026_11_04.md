# Futbol Makinası 2.6.3 — TEK SONUÇ EKRANI KARARI

**Amaç:** Matematik raporunu değiştirmeden kullanıcıya sorulduğunda gösterilecek sonuçları basit bir hiyerarşide sunmak. Kullanıcı 'maçı analiz et' dediğinde teknik 17 bölüm silinmeyecek; birincil kısa görünüm öne gelecek, ayrıntılar ikinci bölümde kalacak. Kullanıcı 'detaylı rapor' isterse tam şablon korunacak.

## 1) Her zaman aynı sıralama

1. **MAÇ + kayıt zamanı + veri durumu** (T−60, erken shadow, offline, maç sonucu net).
2. **KARAR:** S1 en olası / S2 değerli (bağımsız etiketler, sadece onaylı kararlarsa). Onaylı seçim yoksa '**ONAYLI TERCİH YOK**'. Farklı tercihler çıkarsa ikisi de gerekçesiyle farklı satırda kalır; tek 'kazanan' uydurulmaz.
3. **PİYASA:** eşzamanlı kaynağın marjsız olasılığı ve ana/aday modelden farkı. Kullanıcı kâr amaçlı seçim yapıyormuş gibi sunulmaz. Piyasaya yakın model seçici + harmanlama + ayrışma denetçisi ayrı, henüz kabul edilmemiş araştırma adayıdır.
4. **DÖRT MODEL:** B,C2,C3,M4 MS1/X/2, KG, 2.5 Alt/Üst; gerekirse görünür ek detay. C2 mevcut kanonik karar referansı; M4 otomatik terfi etmez.
5. **AYRINTILAR:** 17-bölümlük veri, kadro, sakatlık, xG, yöntem, kaynak, güven sınırı — gerektiğinde tam olarak gösterilir.
6. **MAÇ SONU:** ayrı ekran. Önceden mühürlenmiş tercihler/olasılıklar gerçek sonuçlarla Brier, log-loss ve pilot sonuç olarak karşılaştırılır. Geçmiş tahmin asla değişmez.

## Göstermeme kuralları

- Yüksek ham olasılık, tek başına resmî S1 veya bahis önerisi sayılmaz.
- Oranı bulunmayan maçta piyasa, EV, S2 'hesaplanmadı / doğrulanamadı' kalır.
- 2026-11-04 Gaziantep FK–Kasımpaşa erken gölge kaydındaki üçüncü taraf eski Betano oranlarını **canlı S2** gibi sunma.
- Mevcut S1/S2 eşikleri aynen korunur, yeni fiyat seçici sistem devreye girmez; bir modelin piyasaya yakınlığı **öneri değil** araştırma göstergesidir.
- S1/S2'nin aynı maç için birbiriyle çatışması mümkündür; birbirini sessizce geçersiz kılmaz.
- Her sonuç, geçerli maç saati, veri tarihi, model sürümü, kaynak ve kayıt türü taşımalıdır.

## Gerçek ilk ekranın denemesi

`experiments/263/compact_result_view_263.py` sadece daha önce SHA'sı kilitlenmiş **2026-11-04 erken araştırma kaydı** ile ikinci kaynak fiyatlarını okur ve `model_preview_compact.md` üretir. Bu yeni bir maç tahmini, motor geliştirmesi, resmî 96 kayıt veya S2 bahsi değildir; **yalnız sunum biçimi kabulü**. Gerçek güncel onaylı pilot başladığında karar motorunun zaten kilitlediği kararları okuyacak genel renderer için ayrı entegrasyon yapılır. S1/S2 kararını sunum katmanı hesaplamaz. Böylece henüz üretilmemiş onaylı tercihler taklit edilmez.
