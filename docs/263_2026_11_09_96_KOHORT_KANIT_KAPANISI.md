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
- Önceki `sabah_postmatch_new100_263.py` kuralı `source_checked<=created<kickoff` olduğu için böyle bir mühre sonradan doğru sonuç girilse dahi değerlendirme reddedilebilirdi. Kayıtları geriye dönük değiştirmeden yalnızca **en fazla 1 saniyelik** ölçüm sırası toleransı ve **her iki damga kickoff öncesi** şartı getirildi. Daha büyük fark ve kickoff-sonrası kaynak kontrolü otomatik RED olur.
- Bu değişiklik sadece sonuç eşleştirici + iki sentetik sınama içindir; B/C2/C3/M4 motor, DEV kilidi, tahmin mühürleri, Pinnacle kredileri, otomasyon zamanlaması, geçmiş sonuçlar ve `main` **değişmez**.
- Test kodunun varlığı **CI sonucunun geçtiği iddiası değildir**; CI sonucu ayrı denetlenmelidir.

## 4. Sonlu takip — pilot tekrarına girmeden
1. Önceden mühürlü 44 maçın kaynak/sonuç eşleştirmesini güvenilir eldeki kanıt kadarıyla ayrı `verified / human-attested / unknown / postponed` gruplarında kapat; eksiklere geçmişe dönük tahmin veya skor uydurma. 7 Kasım araştırma skoru kendi kategorisinde kalır.
2. Sadece kullanım için kritik sabah **istek dosyası → resmî fikstür → B/C2/C3/M4 → SHA commit → mobil rapor** zincirini denetle ve eksik bağlantı varsa tek hedefli onarım yap. Eski `263-sabah-live-batch.yml` bilerek fail-closed; mevcut giriş `263-sabah-new100-on-request.yml` üzerinde push ile çalışır. Bu yapı, kullanıcının mesajının kendiliğinden GitHub CI tetiklediği anlamına gelmez.
3. Ertesi gün resmî skorları model tahminlerine **yeniden hesaplama olmadan** ayrı kaydet; yeni kullanım süresince Brier/log-loss güncellenebilir. Matematik motorunun yeni sürüme yükselmesi artık zorunlu pilot şartı değildir.

## 5. Kaynaklar
- GitHub `experiment/263-toplu-karsilastirma`: `forward_quad_263/2026-11-06/`, `forward_acceptance_263/2026-11-07/`, `forward_morning_263/2026-11-08/`, `experiments/263/sabah_postmatch_inputs/`, `experiments/263/sabah_batch_263.py`, `experiments/263/sabah_postmatch_new100_263.py`.
- Kullanıcının Library dosyaları: `2026-11-07_MAKINA_263_TAM_44_MAC_ANALIZI(1).json`, `ANA_263_7_KASIM_2026_SONUC_DENETIMI.md`, `ANA_263_7_KASIM_GOL_PAZARLARI_MUHENDISLIK_KARARI.md`, `ANA_263_2026_11_08_42_MAC_DORT_MODEL_GERCEK_RAPOR.md`, `ANA_263_2026_11_08_EKSIK_8_MAC_KURTARMA_RAPORU.md`, `ANA_263_8_KASIM_2026_DUZELTILMIS_42_MAC_VE_10_SECIM.md`.
- GitHub araştırma dalı: `research/model_challenge/TENLEAGUE_263_FINAL_MS_MODEL_DECISION_2026_11_09.md`, `research/model_challenge/KG_GOALS_JOINT_CALIBRATION_DECISION_2026_11_09.md`.

**Çalışma kararı:** 2.6.3 **M4 ile kullanılır**; 96 adaylık çalışma “yeni pilot lazım” gerekçesine dönüştürülmez. Saha üstünlüğü ve otomatik işletim durumu yalnızca gerçek kanıt ölçüsünde raporlanır.
