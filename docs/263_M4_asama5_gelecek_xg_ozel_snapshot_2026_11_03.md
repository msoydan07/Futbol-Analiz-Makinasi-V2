# M4 — Gelecek xG zaman damgalı özel snapshot altyapısı
**3 Kasım 2026 | Durum: ARAŞTIRMA AMAÇLI GÜVENLİK KATI HAZIR, GERÇEK xG KAYNAĞI BAĞLI DEĞİL**

## Amaç
Aşama 5 incelemesinde 873 ortak C3/M4 maçından 289 maçın geçmişteki xG sürümü doğrulanamadı. Önceki 1.549 maçlık xG-Poisson testini yeniden yapmıyoruz. Bu modül, *gelecek* maçlar için izinli veri ilk edinildiğinde onun özel kopyasını zaman damgasıyla sabitlemeye yarayan güvenlik kapısıdır.

## Hazırlanan dosyalar
- `experiments/263/m4_xg_forward_snapshot_263.py`: Harici veri çekmeyen, izinli CSV baytlarını sadece repo DIŞINDA özel yerel klasöre tekil dosya olarak kaydeden kütüphane. UTC saatini kendisi alır; kullanıcı geri tarih veremez. Önceki günlerden gelen maçlarla tarih koşulu, fixture ID, sayısal xG, SHA256, hedef kickoff kesimi kontrol edilir. Önceden yazılmış dosya silinmez veya üstüne yazılmaz. Klasör 0700, dosya 0600.
- `experiments/263/test_m4_xg_forward_snapshot_263.py`: **11 sentetik güvenlik testi**, gerçek sağlayıcıya bağlanmaz; sonuç veya M4 model testi yürütmez.

## Bilinçli engeller
- **Gerçek Understat toplama otomatik açılmadı**: lisans ve yeniden dağıtım koşulları hâlâ inceleniyor.
- `rights_evidence_ref` sadece operatörün kaynak gösterimidir; gerçek lisans onayı değildir. `vintage_status=LOCAL_OBSERVATION_NOT_EXTERNALLY_ANCHORED` yalnız yerel makine zamanı gösterir; bağımsız zaman damgası / saklama kaydı bulunmadan ileri pilot için kesin as-of kanıtı sayılmaz.
- Model içine doğrudan bağlanmaz; üretilen rapor `approved_for_live_model=false` döndürür, xG değerlerini kamuya açık dosyaya dökmez.
- `GITHUB_ACTIONS=true` altında ham sağlayıcı verisi yazımı varsayılan olarak yasaktır (testlerde `synthetic_test`).
- Public GitHub Actions artifact'i **özel saklama alanı değildir**. Önceki `understat-xg-pilot` artifact'inde ham xG bulunmasıyla ilgili açık hak riski devam ediyor. Bu commit eski artifact'i silmez ve `feature/01-kimlikler` üzerinde çalışan workflow'u değiştirmez.
- Yerel 0700/0600 izinleri ve SHA, sunucu tarafı değişmezliği garanti etmez. Gelecek kabul için güvenilir harici zaman damgası/özel erişimli saklama kanıtı gerekecek.

## Bir sonraki tek kabul kapısı
1. Sağlayıcı erişimi + dahili kullanım/saklama izni yazılı kanıtla netleşir.
2. Public repoda raw veri/artifact upload yolları kapatılır, eski artifact'in erişimi ele alınır.
3. Veri, gerçekten maç öncesinde özel alanda yakalanır; SHA ile birlikte güvenilir, değiştirilemez UTC kabul/zaman damgası alınır; model bu snapshot dışındaki hiçbir veriyi kullanmaz.
4. Sadece yeterli sayıda **yeni** çift-model ileri maç kaydı birikince, önkayıtlı **tek** kapsamlı test ile M4+xG ayrı araştırma kolu değerlendirilir; eski maçlarla yeni ayar avcılığı yapılmaz.

Bu aşamanın kullanıcıya dönük kararı: C3/M4 VE BUGÜNKÜ 23:00 UEFA M0 kayıtları olduğu gibi korunur. xG için yeni maç verisi ve izin durumu henüz onaylanmadığından yeni gerçek xG kaydı veya M4+xG performans testi yapılmadı.

Kaynak notu: https://soccerdata.readthedocs.io/en/stable/intro.html — soccerdata önbelleğinin, kaynakta ne zaman değişiklik yapıldığını kendiliğinden izlemediği belirtiliyor.
