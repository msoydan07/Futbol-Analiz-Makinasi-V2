# 2.6.3 — 7 Kasım 2026 sabah resmî kimlik + deneysel veri kabul denetimi

## Amaç
Dün canlı resmî kaynak sayfalarında bulunan **18/44 saatli eşleşmeyi**, eski analyze_named_match_gate.run üzerinden, mevcut 215 takımlık değişmez kimlik ve sezon kapsam kapısına tek seferde sokmak. Resmî sayfadan saat çıkarmak ve **nihai maçı doğrulamak farklı aşamalardır**.

## İşlem
- sabah_named_source_acceptance_263.py: 96 adaydan bugünkü 44 maçı okur; aynı resmî sayfayı lig başına en fazla bir kere çeker. Önce salt kaynak eşleşmesi, sonra yalnız saatli eşleşmeler için eski isim/ID/lig/dönem kapısı çalışır.
- **Aynı sayfayı yeniden indirmeden** HTML SHA'sı, resmî URL ve canlı eşleşme saati korunur. Eski bağımsız lig okuyucu fallback'u bu tanıda kapalıdır; geçmişe ait bir sayfanın yanlış doğrulamasından kaçınılır.
- Kaynak sayfasındaki ve kimlik kapısındaki UTC kickoff **birebir eşleşmek zorundadır**. KO geçmişse veya 2 dakika sınırı aşıldıysa ileri tahmin hazır ilan edilmez.
- Tarih-only / ekip kimliği belirsiz / ters ev-deplasman / kaldırılmış kaynak / maç saatinde tutarsızlık ayrı blok nedenleriyle verilir.
- data/quad_accepted_263 dosyaları varsa, CSV SHA-256 ile sahibi tarafından araştırma için onaylanmış source_acceptance.json SHA'sı, yedi günlük gözden geçirme penceresi, model-kilidi kod SHA'sı ve DEV onayı tarafı salt okunur kontrol edilir. Kaynaktaki all_4518_independently_verified:false, research_only:true ve betting_authorized:false **korunur**. İnsan kaynak kabulü otomatik ağ doğrulaması değildir.
- Denetim **sıfır tahmin**, **sıfır Pinnacle API çağrısı**, **sıfır mühürlü forward kayıt** ile çalışır. Gerçek model hazır oluşu, ayrı dört modelli pre-KO denemeyi geçmeden iddia edilmez.

## Kanıt
İlgili GitHub Actions: .github/workflows/263-sabah-official-page-live-check.yml.
Artefaktlar:
- /tmp/263-official-coverage.json — 44 maç kaynak durumu
- /tmp/263-named-source-preflight.json — kaynak + resmî isim/lig kimliği + veri/kilit SHA özeti

## Geçiş kuralları
Bir sonraki aşamaya yalnız resmî named gate'den geçmiş, maçı başlamamış ve araştırma verisi kod/dosya kilidi eşleşen maçlar geçebilir. B/C2/C3/M4 tekrar eğitilmez, parametreler değişmez, başka bir kohorttan maç taşınmaz. Bir maçın geçememesi bu maçın gerçekte oynanmayacağı anlamına gelmez: yalnız mevcut kanıt yetersizdir.
