# 2.6.3 — Matematik ve futbol bağlamı işletim denetimi

**Kapsam:** Fikstür geliştirmesi YOK. Model B mevcut hesap, kanonik C2 `k=5,w=0.5`, C3 ve kalite katmanı birlikte gösterilir. Bu çalışma bir **offline matematik çalıştırıcısıdır**; üretim/gerçek maç kabulü değildir.

## Değişen teknik boşluk

Önceki birleşik rapor C2 ve C3'ü çıkarıyordu; mevcut üretim Model B'nin ayrı hesabı aynı raporda yer almıyordu. `operational_report_263.py` halihazırdaki `experimental_poisson_baseline.estimate` fonksiyonunu parametrelerine dokunmadan çağırır. İlk yarı ve korner kalite sınıflandırması mevcut kilitli kabul kanıtıyla korunur. Son 5 cari sezon maçının skor formu **rakip düzeltmesi yapılmadan** yalnız tanımlayıcı alanda görünür. Beklenen gol parametrelerine dış bilgi, Elo, xG, sakatlık veya form çarpanı eklenmedi.

## Tamamlananlar ve kesin sınırlar

- Tekli/çoklu (en fazla 20) **varsayımsal offline vaka** için Maçkolik benzeri kullanıcı adlarını, korunmuş 215 takım kimliği dizini ile eşleştirir; gerçek fikstür adı ve tarihi **doğrulanmış sayılmaz**.
- 4.413 maçlık dondurulmuş CSV ve kilitli kabul JSON SHA-256 kontrolü; her hesapta `match_date < target_date`.
- Model B (C1) ayrı ve hesaplanmış; C2 varsa kanonik `k=5,w=.5` korunur. C2 yoksa Model B alternatif olasılıkları *gösterilebilir ama kanonik model, kalibre edilmiş bahis tercihi veya kabul edilmiş alternatif sayılmaz*. C3 deney olarak ayrı kalır.
- 1X2, çift şans, goller, KG, doğru skor hesapları ortak Poisson dağılımından; ilk yarı ve korner referansı/deneyi ayrı sınıflandırılır. Geçmiş kabul sonucunda ilk yarı gol çizgileri ve köşe sayım modeli güvenilir iyileşme kanıtlamadı.
- xG ayrı kayıtlar otomatik birleştirilmedi. Elo, kadro, sakatlık, hava ve odds/EV λ'ya eklenmedi. Karar/A-B-C ve bahis önerisi üretilmedi.
- `python -m unittest -q ...` tek entegrasyon regresyonunda **73 test OK**. Bunlar **yazılım testleridir**; tahmin başarısını ölçen yeni geçmiş karşılaştırma veya ileri bağımsız örneklem testleri yapılmadı.
- 3 farklı ligde tek uçtan uca offline çalıştırma OK. Örnekler varsayımsaldır ve resmî maç teyidi içermez.
- Üretim `main` ve `feature/01-kimlikler` dalları değiştirilmedi; gerçek maç kaydı/pilot yok.

## Çalıştırma — yalnız offline

Repo kökünden örnek (dondurulmuş geçmiş CSV ayrıca verilmelidir):

```bash
cd experiments/263
python operational_report_263.py \
  --history /path/to/frozen/historical_results.csv \
  --evidence evidence/acceptance_263.json \
  --index evidence/identity_index_263.json \
  --aliases ../../data/team_aliases_reviewed.csv \
  --named /path/to/sample_named_hypothetical_cases.json \
  --out /tmp/offline_263
```

Bu araç, mevcut resmi maç gate'ini devre dışı bırakmaz. Kullanıcı gerçek bir maç verdiğinde resmî kontrol sohbet sırasında anlık yapılacak; yazılımı canlı/otomatik hizmet diye ilan etmek doğru değildir.

## Açık işler — tam üretim kabulünü bloke edenler

1. Güncel kaynakların gerçekten toplanıp periyodik snapshot olarak dondurulması; son mevcut veri 29.10.2026 ile sınırlı.
2. Kullanıcının maç için resmî teyidinden sonra doğru tarih, kaynak, kimlik ve maç başlamamış durumu ile bu matematik raporunun **tek canlı çağrı yoluna bağlanması**.
3. Futbol analizinin doğrulanabilen güncel kadro/haber/xG/şut/rakip kalitesi alanlarının kanıt protokolüyle tamamlanması (λ üzerinde otomatik, kanıtsız düzeltme yok).
4. Henüz onaylanmamış modeller için ayrı ileri dönem kanıtı ve sonunda tek kapsamlı sistem kabulü. Oran/EV ve maç önü tahmin defteri/pilot kullanıcı kararıyla daha sonra.

**Net karar:** Çalışan offline matematik rapor altyapısı mevcut; canlı, eksiksiz 2.6.3 tahmin makinası henüz kabul edilmiş değildir. Yeni fikstür geliştirmesi veya geçmiş model hiperparametre araması yapılmaz.
