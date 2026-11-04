# 2.6.3 - 4 Kasim kesinlesen karar uygulamasi

Dort model B/C2/C3/M4 birbirine karistirilmiyor. Tek ana, yalniz baska pazar ailesinden anlamli alternatif ya da PAS. 1.5 Ust keyfi cezalandirilmiyor; kendi lig tabani, DEV kalibrasyon becerisi, 3 model destegi ve marjsiz fiyat farki ile butun pazarlara esit kural. Yalniz ham yuksek yuzde deger degildir. EV >= %5 ve no-vig fark >= 3 puan. Eski sikı 3 modelin >=%75 ve <=10 puan dagilimi S1 olasilik uyarisidir, S2 icin kosulsuz kilit degildir. M4 otomatik ana model olmadi. Gercek T-60 oncesi SHA forecast olmadan calismaz. Saatli bookmaker gozlemi disinda fiyat iddia edilmez.

Yeni salt okunur arastirma karari: four_model_value_policy_263.py. GOALS_1.5 ve GOALS_3.5 tam fiyat ciftleri manuel oran girisine eklendi. Pazar bazinda pozitif gelistirme Brier becerisi yoksa guvenilir deger adayi secilmez; 1.5 Ust yine yuksek olasilik uyarisinda gorunebilir ve gelecekte beceri kaniti iyilesirse ana adaya hak kazanabilir. Odss yoksa ana deger tercihi PAS, ama olasilik raporu saklanir.

Eksik: canli oran sitelerinden gercek otomatik alici yok, T-60 kadro/gozlem butunlesmesi ve tek komutla fiyat+karar+GitHub kilidi ayri. Once bu kodun tek toplu testi, sonra son baglanti testi; 880 gecmis maci tekrar hesaplamayalim. Uretim/ROI/bahis iddiasi yok.
