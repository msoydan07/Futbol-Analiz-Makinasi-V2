# FUTBOL MAÇ ANALİZ MAKİNASI 2.6.3 — GERÇEK ÜÇ MAÇ TOPLU MÜHÜR + MOBİL KABULÜ
**Tarih:** 7 Kasım 2026, TSİ 12:09–12:10  
**Durum:** BAŞARILI — kapsam *mühendislik acceptance3*, 96/100 ileri pilotlarının kendisi değildir.

## 1. Kanıt
- GitHub Actions: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42358492713 — **success**.
- Kalıcı gerçek kayıt commit'i: 5d0e5dfd561bae1276886d50e47e2ca57a3c508d.
- Son offline kabul: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42358433359 — **87/87 tests passed**.
- Kaydedilen kabul makbuzu: experiments/263/sabah_acceptance_results/acceptance3_42358492713.json.
- Kaydedilen mühürlü batch: experiments/263/sabah_batch_reports/acceptance3_42358492713.json.
- Tekli + toplu telefon ekranları: experiments/263/sabah_mobile_reports/acceptance3_42358492713/.
- Kaydedilen 3 gerçek forward: forward_acceptance_263/2026-11-07/ (3 dosya), her biri kendi SHA'yla imzalı.
- Kaydedilen 3 baseline ve 3 research decision: experiments/263/sabah_research/acceptance3/2026-11-07/.
- GitHub uzak branch'de makbuz, özet ve bütün tahmin dosyalarının mevcut olduğu çalışma içinde kontrol edildi.

## 2. Üç gerçek müsabaka

| Lig | Maç | Başlama TSİ | Durum | Kalibre MS yönü | Karar |
|---|---|---|---|---|---|
| ESP1 | Valencia – Real Madrid | 23:00 | B/C2/C3/M4 AVAILABLE | MS2 %56,6 | RESEARCH_PAS |
| ENG1 | Arsenal – Hull City | 18:00 | B **UNAVAILABLE_INSUFFICIENT_CONTEXT**; C2/C3/M4 AVAILABLE | MS1 %64,0 | RESEARCH_PAS |
| TUR1 | Samsunspor – Konyaspor | 16:00 | B/C2/C3/M4 AVAILABLE | MS1 %42,4 | RESEARCH_PAS |

Sayısal MS değerleri dondurulmuş DEV kalibrasyon motorunun çıktısıdır, dört model yüzdelerinin basit ortalaması değildir. B modelinin Hull City eşleşmesindeki **yetersiz bağlam** durumu gizlenmedi ve tahminle doldurulmadı. C3/M4 her üçünde AVAILABLE, dört modelin durumu açıkça kayıtlı.

## 3. Bağımsız bütünlük
- 3 mühürlü forecast SHA, 3 baseline SHA, 3 decision SHA, toplu mobil ekran SHA ve üç tekli mobil ekran SHA makbuzda bağlı.
- Mobil ekranların orijinal mühürlü SHA verilerinden **byte-for-byte** üretildiği kanıtlandı.
- Resmî kaynak canlı sayfada yeniden denetlendi, canonical takım kimlikleri uyuştu. Git commit'ten önce ve push öncesinde tüm kickoff'lar hâlâ gelecekteydi (2 dakika emniyet payı).
- Tarihsel baz arşivi SHA **35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1**.
- Güncel kabul araştırma verisi SHA **1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9**.
- Bu insan tarafından sınırlı deneysel kullanım için kabul edilmiş veri, **4518 maçın tamamı bağımsız doğrulandı** anlamına gelmez. İlk 11/rotasyon eksiklikleri varsa niteliksel olarak işaretlenir.
- **Bookmaker API calls = 0, quoted prices = none, betting_authorized = false**, üçü de RESEARCH_PAS.
- Önceki dört mühürlü pilot tahmini, eski 96 kohortu, ayrı yeni 100 kohortu, main ve mevcut M4/C3/B/C2 formülleri değiştirilmedi.

## 4. Gerçekçi mühendislik sonucu
**Kanıtlandı:** Kaynağı doğrulanmış **birden fazla gerçek müsabakanın**, ayrı ve değişmez bir GitHub mühendislik kohortunda toplu B/C2/C3/M4 hesaplaması, dürüst eksik-model bildirimi, temel lig oranı, DEV kararı, SHA-256 mühürleme, GitHub commit/push, tekli/toplu mobil ekranla aynı mühürün doğrulanması.

**Henüz kanıtlanmadı:** Yeni 100 maçlık esas ileri pilotun kullanıcı tarafından belirlenmiş her maç için aynı çalışmayla sürekli yönetimi, 10 ligin eksiksiz güncel resmî fikstürü, resmî güncel Pinnacle oranı/EV doğrulaması veya bahis başarısı. Gerçek acceptance3 kayıtları 96/100 pilotlarına sonradan taşınmaz.

## 5. Sıradaki tek adım
Yeni 100 maçlık **asıl** ileri pilotu kullanıcı tarafından isimleri belirlenmiş maç isteğiyle çalıştırmadan önce, deneysel acceptance3 işindeki doğrulanmış **fail-closed mobil/SHA denetimini** yeni100 canlı hatta taşımak ve mevcut workflow_dispatch girişinin GitHub tarafından gerçekten ulaşılabilir olduğuna dair kabulünü yapmak. Krediler varsayılan KAPALI kalır. Önceki failed runları yeniden çalıştırma.
