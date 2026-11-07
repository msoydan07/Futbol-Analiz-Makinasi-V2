# Futbol Maç Analiz Makinası 2.6.3 — 7 Kasım canlı kimlik ve gerçek dört-model kabul

## Son kanıtlanmış durum
- **Resmî kaynak ve eşsiz takım kimliği kontrolü**: 44 sabit tarih-listesi adayından 18'inde resmî sayfada açık başlama saati; bu 18 eşleşmenin tamamı mevcut canonical named-match ve 2026/27 lig üyeliği kapısından geçti. Kalan 26 aday resmî sayfada saatli eşleşme kanıtı vermedi: analiz veya "kesinlikle maç yok" iddiası yapılamaz.
- **Çevrimdışı güvenlik/kabul**: 78/78 test başarılı, run https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42356800553 .
- **Canlı 18-maç named-match + kaynak SHA denetimi**: https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42356800471 .
- **Kaynak durumu**: 4518 güncel sonuç dosyası SHA 1170ecf9bdc31426e80a069cfc63d7112d0ab0c0c7d527e3bb5daf9b3841ece9. Pinned 4413 baz SHA 35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1. M4 kod SHA kilidi eşleşti. İnsan kaynak değerlendirmesi **sınırlı deneysel araştırma** için kabul edilmiş; bütün 4518 satır bağımsız doğrulanmış DEĞİL ve bahis yetkisi YOK.
- **Gerçek 4-model geçici araştırma kabulü**: Valencia–Real Madrid, lig ESP1, resmî açılış 2026-11-07T20:00:00+00:00 (TSİ 23.00), canlı kaynak ve 215-UUID kimlik kapısından geçerek 2026-11-07T08:50:02Z'de test edildi. Run https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42357121539 .
- Bu gerçek maçta **B/C2/C3/M4 = AVAILABLE / AVAILABLE / AVAILABLE / AVAILABLE**. 4518 kabul edilen araştırma sonuçları ve 4413 pinli arşivle dört kod tek çalışmada hesaplandı. Tarihsel pazar bazları ve dondurulmuş DEV kalibrasyon karar katmanı **RESEARCH_PAS** üretti (gerçek/doğrulanmış bahis oranı yok).
- Geçici forecast SHA a9cd87c1a4f3035c098bb80a40bfd5c0bfa185b79e2fb0d895c78a06b05fa406; geçici decision SHA c02bef13289b102d4b1b33d4cfbb26f396be8da1e574cb8d9c460f16f3385469. Bunlar **pilot defteri kaydı değildir**. Modelin geçici çıktı dosyası testten sonra silindi. Yalnız kısa ömürlü GitHub Actions test artefaktında ayrıntılı deneysel yüzde raporu kaldı.
- **Özellikle korunmuş**: 96-maç eski kohort, ayrı 100-maç yeni kohort, eski mühürlü dört pilot tahmini, kalibrasyon/Poisson matematiği, main, Pinnacle günlük kredi politikası. Yeni ileri pilot kaydı 0, bookmaker API çağrısı 0, resmî bahis önerisi 0.

## Sıradaki tek mühendislik adımı
Bu iki kabul, sabah **toplu çalışma workflow_dispatch** girişinin gerçek immutable Git kayıtlarına güvenli, istek üzerine ve kullanıcı tarafından belirlenen kohorta bağlı olarak uçtan uca yazdığını henüz kanıtlamaz. Sıradaki kabul, kaynak doğrulamasından geçebilen gerçek maçlar için batch manifest/günlük limit, mühürleme, commit öncesi KO kontrolü ve mobil tekli/toplu ekran bütünlüğünü **aynı tek çalışmada** doğrulamak. Böyle bir testte eski 96 aday dosyasını geriye dönük kayıtla değiştirmek yasaktır. Pinnacle kredisi için kullanıcı varsayılanı KAPALI olmaya devam eder.

**Mühendislik hükmü**: Resmî fikstür (18 eşleşme), 4-model kaynak/kilit ve gerçek tekli matematik/karar hattı TEST EDİLDİ. Ancak tüm 10 lig için eksiksiz fikstür veya gerçek sabah batch'in kalıcı mühürlemesi henüz kanıtlanmış değildir.
