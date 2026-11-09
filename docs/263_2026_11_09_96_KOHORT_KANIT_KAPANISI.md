# 2.6.3 — 6–8 KASIM 2026 / 96 ADAYLIK ÇALIŞMANIN KANIT KAPANIŞI
**Tarih:** 9 Kasım 2026  
**Tür:** Mevcut kayıtların bir kez uzlaştırılması, yeni pilot başlatma talebi DEĞİLDİR.  
**Ana karar:** **Mevcut kilitli M4 ile düzenli analiz kullanımına geçme kararı yürürlükte.** B/C2/C3 korunur. LITE 1.3 kapsam dışıdır.

## 1. Aynı sayı farklı anlama gelmesin
6–8 Kasım için sabitlenmiş `legacy96` aday sayısı **10 + 44 + 42 = 96**. Bu sayı tamamlanmış 96 resmî tahmin+sonuç kanıtı değildir.

| Tarih | Sabit aday | Maç öncesi matematik araştırması | Depoda bağımsız kalıcı 2.6.3 mühür | Sonuç kanıtı |
|---|---:|---|---|---|
| 6 Kasım | 10 | En az 4 gerçek maç önü dört-model SHA kaydı | `forward_quad_263/2026-11-06/`: **4** | GitHub attestation yok |
| 7 Kasım | 44 | Kullanıcı Library araştırma JSON'unda **44/44**, biri yalnız 2/4 model | `forward_acceptance_263/2026-11-07/`: **3 ayrı kabul kaydı**, 44 resmî pilotu temsil etmiyor | Önceki Library raporunda **43 skor**, bir maç ertelenmiş; hepsi ağdan yeniden doğrulanmadı |
| 8 Kasım | 42 | **42/42 en az bir model:** ilk 34 + sonraki 8 resmî ad/kimlik kurtarma; dört-model mevcudiyeti B 37/42, C2 41/42, C3 41/42, M4 42/42 | `forward_morning_263/2026-11-08/`: **40** (new100 ve legacy96'dan ayrı!) | GitHub attestation yok; araştırma tablosu Estoril–Marítimo için erteleme kaydı içeriyor |

**Toplam:** En az **90 farklı aday** için zamanında model sonucu veya dört-model mühür bulunduğu belgeleniyor (4+44+42). Bu, **90 resmî pilot başarısı** anlamına gelmiyor. 7 ve 8 Kasım araştırma hesaplarıyla 8 Kasım 40 SHA mührü iki kere sayılmıyor. 7 Kasım'daki 3 `forward_acceptance_263` kaydı ayrı ve tekrar sayılmıyor.

**İhtilaflı “95 tamamlandı” ifadesi:** 7 Kasım araştırma raporu `Nacional–Académico`, 8 Kasım düzeltilmiş araştırma raporu `Estoril–Marítimo` maçını ertelenmiş etiketliyor. Bu iki kayıt bağımsız resmî kaynaktan uzlaştırılmadan **95 tamamlanmış maç** iddiası doğrulanmış olarak yazılmaz. Kesin tamamlanan sayısı ile oynanan maç sayısı farklı tutulur.

## 2. İlk gerçek sonuçlardan çıkarılabilecek mühendislik kararı
- 7 Kasım 43 skor içeren araştırma raporunda **35 eşit dört-model ortak maç** için MS yön isabeti M4 **19/35 (%54,3)**, B **17/35**, C3 **16/35**, C2 **15/35**. MS Brier değerleri sırasıyla M4 **0,5991**, B 0,6145, C3 0,6113, C2 0,6012. Bu **araştırma** verisidir; bahsi kazandırdığı ya da 96 resmî pilot başarısı değildir.
- Aynı 43 araştırma maçında dört-model **ham medyan** KG Var/Yok yönü **26/43**, 1,5 Alt/Üst **30/43**, 2,5 Alt/Üst **24/43**, 3,5 Alt/Üst **34/43**. Basit daima 1,5 Üst **30/43**, daima 3,5 Alt **33/43** olduğundan yüksek yüzdeler üstünlük kanıtı değildir.
- Eşit geçmiş haftalık bilgi setli 896 maçlık retrospektifte M4'ün MS yön isabeti **%53,35**, XGBoost'un **%51,12**. 397 ortak tarihsel maçta MS-korumalı gol dağılımı dört gol Brier hatasını iyileştirdi, ancak incelenmiş sonuçlara bakıldıktan sonra tasarlandığı için keşifseldir.
- **Karar:** Ana M4 sabit kalır; araştırma adayları (XGBoost, MS-korumalı KG/gol düzeltmesi, otomatik seçici) mevcut tahmin zincirine terfi ETMEZ. **Yeni bir pilot bekleme şartı konmaz.**

## 3. Teknik denetim — engel ve somut düzeltme
- GitHub araştırma dalında **4 (6 Kasım) + 40 (8 Kasım) = 44** ayrı SHA mühür dosyası var. Resmî `experiments/263/sabah_postmatch_inputs/` attestation dosyası **0**. Bu nedenle bu 44 mühre ait resmî maç sonu skor isabet oranı raporlanamaz.
- Örnek gerçek mühürlerde `created_at_utc`, kapı `source_checked_at_utc` değerinden **12–39 mikrosaniye önce** yazılmış. Bu bir istek başlangıcı/kaynak damga sırası: her iki zaman da maç başlangıcından öncedir.
- Önceki `sabah_postmatch_new100_263.py` kuralı `source_checked<=created<kickoff` olduğu için böyle bir mühre sonradan doğru sonuç girilse dahi değerlendirme reddedilebilirdi. Kayıtları geriye dönük değiştirmeden yalnızca **en fazla 60 saniyelik** resmî sayfa sorgu süresi toleransı ve **her iki damga kickoff öncesi** şartı getirildi. Daha büyük fark ve kickoff-sonrası kaynak kontrolü otomatik RED olur.
- Bu değişiklik sadece sonuç eşleştirici + iki sentetik sınama içindir; B/C2/C3/M4 motor, DEV kilidi, tahmin mühürleri, Pinnacle kredileri, otomasyon zamanlaması, geçmiş sonuçlar ve `main` **değişmez**.
- Test kodunun varlığı **CI sonucunun geçtiği iddiası değildir**; CI sonucu ayrı denetlenmelidir.

### 3B. 8 Kasım gerçek push → SHA → mobil zincirinin izahı
GitHub'ın halihazırdaki iki gerçek `new100` batch raporu denetlendi:
- **Run 42469245388:** 42 isimli girdi → **33 yeni kalıcı mühür**, 9 bloke; kaynak, kararı ve tekli/toplu mobil SHA görünümü aynı isteğin kayıtlarıdır. API oran çağrısı **0**, resmî bahis onayı **0**.
- **Run 42469487639:** ilk turdan 8 bloke adı yeniden kaynaktan deneme → **7 yeni kalıcı mühür**, 1 bloke. **Toplam 40/42** kalıcı new100 mühür, iki ayrı başarılı kaynak geçişli Git kayıt paketi.
- 42 araştırma maçından resmî new100'a alınmayan **SC Cambuur–PSV**: C3 çıktısı olmadığı için `REQUIRES_C3_M4_AND_THREE_AVAILABLE` emniyet kapısı; ayrıca araştırma hesabı ayrı dosyada mevcuttur.
- **FC Utrecht–NEC Nijmegen:** KNVB resmî sayfa kontrolü istenen karşılaşmayı teyit edemedi: `OFFICIAL_GATE_FAILED:official_match_not_confirmed`. Araştırmada hesap olması resmî kimlik kapısından geçtiği anlamına gelmez.
- **İşletim kararı:** 8 Kasım için gerçek `girdi → resmî doğrulama → dört-model denemesi → git SHA mührü → mobil ekran` zinciri **40 maçta çalışmıştır**. Ancak maç sonu resmî sonuç kaydı hâlâ **0**; 7/10 gün tüm kupaları kapsayan rotasyon veri seti yetersiz; Pinnacle/EV doğrulanmadı. Bütün 40 kararda `RESEARCH_PAS` olmasına şaşırılmamalıdır.
- Kayıtlar: `experiments/263/sabah_batch_reports/new100_42469245388.json`, `new100_42469487639.json`, eşleşen `sabah_new100_receipts` ve `sabah_mobile_reports` dosyaları. Kayıtlar yeniden hesaplanmadı.

**Zaman sırası kod düzeltmesi sonrası tek toplu CI:** postmatch #42599249693 **PASS**; sabah offline bütünleşik bileşen denetimi #42599249981 **PASS**. Bunlar yeni maç tahmin başarısı değildir.

## 3C. 6 Kasım dört kalıcı mührün ilk maç sonu puanlaması
6 Kasım `forward_quad_263` altında kaydedilmiş **dört ayrı gerçek maç önü SHA** dosyası GitHub'dan okunup takımlar resmî kulüp/lig skorlarıyla eşleştirildi. Bu da **salt-okunur web araştırmasıdır**; `postmatch_inputs` insan teyitli resmî kayda terfi ettirilmemiştir.

| Lig | Maç | Skor | M4'ün ham MS yönü | M4 doğru mu? |
|---|---|---:|---|---|
| TUR1 | Gaziantep – Kasımpaşa | 0-2 | MS2 | Evet |
| ITA1 | Venezia – Udinese | 2-1 | MS2 | Hayır |
| FRA1 | Toulouse – Strasbourg | 3-1 | MS1 | Evet |
| NED1 | Willem II – PEC Zwolle | 1-1 | MS2 | Hayır |

| Model | Ham MS yön doğru/4 | Çok sınıflı MS Brier |
|---|---:|---:|
| B | 1/4 | 0,783362 |
| C2 | 1/4 | **0,695070** |
| C3 | 1/4 | 0,736566 |
| M4 | **2/4** | 0,777795 |

Bunlar aynı dört maçtan ve maçtan önceki orijinal `model_predictions` olasılıklarından elle/araç yardımıyla hesaplanan tanımlayıcı değerlerdir. M4 yön tercihlerinde 2/4 ile önde olsa da en düşük Brier **C2'de**; yön ve olasılık kalitesi farklı kavramlardır. Dört maçın hiçbiri model değişimi gerektirmez.

Resmî kaynaklar: [TFF Gaziantep–Kasımpaşa](https://www.tff.org/Default.aspx?macId=317874&pageId=29), [Lega Serie A Venezia–Udinese](https://www.legaseriea.it/serie-a/news/venezia-udinese-2026-2027-2-1-cronaca-risultato-gol), [Toulouse FC–Strasbourg](https://www.toulousefc.com/match-center/equipe-professionnelle-20262027-a4qw50gbzq6myjglp6r96l4wk), [KNVB Willem II–PEC Zwolle](https://www.knvb.nl/competities/eredivisie/uitslagen).

## 3D. Üç güne ait bulguyu birleştirirken doğru payda
Aynı pazarın **ham M4 maç-sonu yönü** açısından karşılaştırılabilen, kendi kayıt kategorilerinde skoru bulunan maçlar:
- 6 Kasım kalıcı dört SHA: **2/4** doğru; birincil kaynaklardan asistan web kontrolü.
- 7 Kasım ayrı araştırma belgesi: **19/35** doğru (dört modelin ortak hesaplandığı 35 maç); skorların bir kısmı bağımsız ağdan yeniden doğrulanmadı.
- 8 Kasım gerçek new100 kalıcı mühürler: **25/39** doğru; 35 birincil, 4 medya çapraz kontrolü; Estoril–Marítimo ertelendi.

Toplam **46/78 (%58,97)** yalnız *farklı kanıt kategorilerini yan yana koyan betimsel* bir ham MS yön sayımıdır. **96 resmî pilot sonucu, tam SHA/sonuç eşleşmeli kohort veya piyasa üstü başarı kanıtı değildir.** Ayrıntılı metrikler kategorilerinde ayrı kalır. Aynı skor iki kere sayılmaz. Kullanım kararı için bu bulgular yeterli bağlamsal kanıt sağlar, ancak sistemin tüm maçları bilebildiği sonucunu vermez.

## 4. Sonlu takip — pilot tekrarına girmeden
1. Önceden mühürlü 44 maçın kaynak/sonuç eşleştirmesini güvenilir eldeki kanıt kadarıyla ayrı `verified / human-attested / unknown / postponed` gruplarında kapat; eksiklere geçmişe dönük tahmin veya skor uydurma. 7 Kasım araştırma skoru kendi kategorisinde kalır.
2. Sadece kullanım için kritik sabah **istek dosyası → resmî fikstür → B/C2/C3/M4 → SHA commit → mobil rapor** zincirini denetle ve eksik bağlantı varsa tek hedefli onarım yap. Eski `263-sabah-live-batch.yml` bilerek fail-closed; mevcut giriş `263-sabah-new100-on-request.yml` üzerinde push ile çalışır. Bu yapı, kullanıcının mesajının kendiliğinden GitHub CI tetiklediği anlamına gelmez.
3. Ertesi gün resmî skorları model tahminlerine **yeniden hesaplama olmadan** ayrı kaydet; yeni kullanım süresince Brier/log-loss güncellenebilir. Matematik motorunun yeni sürüme yükselmesi artık zorunlu pilot şartı değildir.

## 5. Kaynaklar
- GitHub `experiment/263-toplu-karsilastirma`: `forward_quad_263/2026-11-06/`, `forward_acceptance_263/2026-11-07/`, `forward_morning_263/2026-11-08/`, `experiments/263/sabah_postmatch_inputs/`, `experiments/263/sabah_batch_263.py`, `experiments/263/sabah_postmatch_new100_263.py`.
- Kullanıcının Library dosyaları: `2026-11-07_MAKINA_263_TAM_44_MAC_ANALIZI(1).json`, `ANA_263_7_KASIM_2026_SONUC_DENETIMI.md`, `ANA_263_7_KASIM_GOL_PAZARLARI_MUHENDISLIK_KARARI.md`, `ANA_263_2026_11_08_42_MAC_DORT_MODEL_GERCEK_RAPOR.md`, `ANA_263_2026_11_08_EKSIK_8_MAC_KURTARMA_RAPORU.md`, `ANA_263_8_KASIM_2026_DUZELTILMIS_42_MAC_VE_10_SECIM.md`.
- GitHub araştırma dalı: `research/model_challenge/TENLEAGUE_263_FINAL_MS_MODEL_DECISION_2026_11_09.md`, `research/model_challenge/KG_GOALS_JOINT_CALIBRATION_DECISION_2026_11_09.md`.

**Çalışma kararı:** 2.6.3 **M4 ile kullanılır**; 96 adaylık çalışma “yeni pilot lazım” gerekçesine dönüştürülmez. Saha üstünlüğü ve otomatik işletim durumu yalnızca gerçek kanıt ölçüsünde raporlanır.
