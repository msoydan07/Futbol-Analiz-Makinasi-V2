# 2.6.3 — 4 Kasım 2026 T−60 dört-model kaydı ve değer kararı bağlantısı

## Tek kabul kararı: BAŞARILI (yalnız yeni bağlantı, gerçek maç pilotu henüz yok)

Son gözlenen değişiklik: [commit 5aeda693c](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/commit/5aeda693c513e1e3f17055b65e2c434b2aa47376).
Yalnız yeni 7 entegrasyon testi: [GitHub Actions 41876512990](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41876512990), **7/7 başarılı**. Önceki dört-model ve oran kabulü: [41864815416](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/41864815416), **23/23 başarılı**. Eski 880 maçı yeniden hesaplayan test yok.

## İşleyen kayıt zinciri

1. Kullanıcı tek maçı adıyla seçer; mevcut resmî fikstür kapısı, 4.518 kabul edilen araştırma verisi ve kilitli M4 ayarları B/C2/C3/M4 tahminini hesaplar. **Gerçek GitHub Actions başarı ve KO-öncesi commit şartı korunur.**
2. Artık **aynı workflow içinde**, ilk tahminin SHA'sına bağlı **tarihsel lig baz oranı** ve **oransız dürüst PAS/olasılık raporu** da oluşturulur. Bu kayıtlar yoksa forecast dosyası tek başına yayımlanmaz. Her adım KO öncesi ve ilk forecast'ten itibaren 10 dakika içindedir.
3. Gerçek bahis sitesinin tam karşı seçimleri (MS 1/X/2, KG Var/Yok, 1.5, 2.5, 3.5 Alt/Üst) bizzat kaynak ve UTC gözlem saatiyle kontrol edilip, önceki tahminle eşleştirilmiş **manuel gözlem** girilirse sonraki ayrı workflow **aynı kaynak SHA'sına bağlı** fiyatlı **ana / başka aile alternatifi / PAS** kararını yazabilir.
4. İlk forecast, baz ve PAS kaydı **silinmez/yeniden düzenlenmez**; fiyatlı karar yeni SHA mühürlü ayrı dosyadır. Fiyat eksik veya eskiyse EV yoktur; ilk rapor PAS kalır.
5. Kayıtların hiçbiri otomatik bahis, resmî S1/S2 veya kârlılık onayı vermez. Olasılık raporu ile matematiksel değer kararı ayrı tutulur. 1.5 Üst'e otomatik ceza yoktur; pazarın kendi DEV kalibrasyon becerisi ve odds gereklidir.

## Değişen uygulamalar
- `experiments/263/quad_prematch_bridge_263.py` — yeni iki kayıt köprüsü.
- `experiments/263/test_quad_prematch_bridge_263.py` — 7 senaryo: PAS, fiyatlı ana/alternatif, çift kayıt engeli, KO sonrası engel, tahmin SHA bozulması, kaynak baz yokluğu, batch SHA bozulması.
- `.github/workflows/263-quad-forward-on-request.yml` — yalnız **yeni** kullanıcı maç isteği JSON eklendiğinde çalışacak; model + baz + PAS kaydını koşu içinde kontrol edecek; kayıtsız bir tahmini başarılı yayımlamayacak.
- `.github/workflows/263-market-quote-lock-on-new-request.yml` — **yeni** ve gerçek kaynaklı bahis oranı girişinde, fiyat kaydıyla değer kararını beraber oluşturacak; sadece kısmi/hatalı girişte engel raporu.
- `.github/workflows/263-quad-prematch-bridge-ci.yml` — yalnız yeni bağlantıya ilişkin 7 hedefli kontrol.

## Açık ve gerçek eksikler
- **Canlı bookmaker fiyatını kendi kendine indiren, bağımsız doğrulayan entegrasyon mevcut değil.** ChatGPT kaynak kontrolü ve manuel oran gözlem dosyası gerekebilir; kaynak yoksa PAS. Fiyatı uydurma veya rastgele sitelerden karıştırma yasak.
- Bu yeni B/C2/C3/M4 ikili SHA kayıt zinciri henüz *gerçek* KO-öncesi kullanıcı maç isteğiyle denenmedi. `forward_quad_263/` dalda hâlâ boş. Bir sonraki gerçek maçta **yalnız bir uçtan uca kontrollü kayıt** yeterlidir; yeniden geçmiş model testi yapılmayacak.
- Fenerbahçe–Liverpool 4 Kasım UEFA T−60 gölge tahmini **ayrı M0/M0+Elo** kaydıdır ve dokunulmadı: `experiments/263/europe/t60_locked/2026-11-04_2045_TR/2049620.json`. Yerel lig dört-model pilotu hesabına yazılmadı.
- Kullanıcı ilk 11 açıklanmadı diye matematik analizinin durmasını istemiyor; kadro kanıtı bağlamsal olarak korunur, resmen test edilmemiş gol çarpanı modele sokulmaz.

**Tek sonraki eylem:** kullanıcı ismiyle ilk gerçek lig maçı, resmî fixture, T−60 forecast + as-of PAS ve uygun bulunursa kaynaktan taze fiyat eklentisi. Hileli geçmiş zaman damgası yok; 4.413 temel ve 4.518 kabul edilmiş kaynak korunacak.
