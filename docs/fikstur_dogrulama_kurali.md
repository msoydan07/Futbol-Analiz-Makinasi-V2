# Fikstur dogrulama kurali — V2

Bu belge yeni bir fikstur motoru veya otomatik gelecek mac havuzu tanimlamaz.

1. Kullanici belirli bir mac sordugunda, ana akis resmi/guncel kaynaklardan gelecek 7 gun icinde maci, tarihi ve saati arar. Zaman penceresi sorgu anina gore hesaplanir.
2. Football-Data skor alanlari bos mac satirlari yalnizca IKINCIL kanittir. Bu satirlar gelecekteki maclar olabilir; ertelenmis/iptal edilmis veya eksik sonuclu kayitlar da olabilir.
3. Ikincil eslesme icin lig/sezon ve dogrulanmis takim kimlikleri karsilastirilir. Sadece benzer takim adlariyla otomatik kesin eslesme yapilmaz.
4. Ana kaynak dogrulamasi yoksa ikincil satir tek basina kesin mac tarihi, saati veya oynanma durumu kaniti olamaz.
5. Ikincil kaynakta bulunamamasi ana kaynakta dogrulanmis maci gecersiz kilmaz.
6. Kaynaklarin tarih/saat bilgileri celisirse CELISKI olarak raporlanir; otomatik uzlastirilmaz.
7. Mac sonucu bos kayitlar matematiksel gecmis performans ve egitim verisine katilmaz.
8. Bu kurallar, gelecekteki mac icin kullanici sorgusu geldiginde uygulanir; mevcut veri kalitesi denetiminin kabul kriterlerini degistirmez.

Durum: Is akisi karari. Otomatik kaynaklar-arasi fikstur dogrulama uygulamasi henuz bu belgede tamamlanmis olarak iddia edilmez.
