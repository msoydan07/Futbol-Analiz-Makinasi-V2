# 2.6.3 — FAZ 1: Gerçek takım gücü/veri yeterliliği denetimi
**Tarih:** 11 Kasım 2026 (Türkiye). **Kaynak:** 4.617 gol/skor sonucu, 10 lig, 2026/27.

## İş tamamlandı; gerçek verili kabul raporu

- [GitHub Actions: 9/9 PASS, gerçek 10 lig analizi](https://github.com/msoydan07/Futbol-Analiz-Makinasi-V2/actions/runs/42907028500).
- Toplam **192 2026/27 sezonunda maç kaydı bulunan takım**.
- **31 farklı takımın**, ev ya da deplasman rolünden en az birinde, **8'in altında geçmiş maç** bulunuyor. Bunu risk veya belirsizlik gösterge adayı olarak kaydediyoruz; doğrulanmış tahmin isabet eşiği değil.
- **Ev sahibi örneği yetersiz:** toplam 30 takım-rol. **Deplasman örneği yetersiz:** toplam 26 takım-rol. Bu sayılar farklı takım sayısı olarak toplanamaz; takım hem ev hem deplasmanda sınırlı olabilir.
- **Güncel sezondaki maç sayısı:** bu 192 takımın hiçbiri 2026-11-11 as-of tarihinde ev/deplasman rolünde 4'ün altında değil; hiçbiri güncel sezon toplamında 6'nın altında değil. Bu, lig başındaki başka günlerde sorun çıkmayacağı anlamına gelmez.
- **60 günden uzun aralıksız takım:** güncel sezon aktif 192 takım içinde bu tarih için 0.
- **M4 yeni/kimliği bilinmeyen takım davranışı:** `predict_m4`, geçmiş lig verisinde olmayan takımın katsayılarını **0** alıp kısmen lig başlangıç ortalamasına dönebiliyor. Bu, takım gücü biliyormuş gibi sunulmamalı. Tek maçlık araştırma aracı bunu `UNSEEN_TEAM_M4_LEAGUE_BASELINE_FALLBACK` olarak açıkça gösteriyor; M4 matematik motoru değiştirilmedi.
- Eski **4.518 satır ve kaynak SHA'sı**, yeni **4.617 skor kaydı**, **M4 matematik motoru SHA'sı** birebir doğrulandı. **1 hükmen sonuçlanmış erken tamamlanan maç** 90 dakika beklenti denetimi dışında bırakıldı. Uydurma maç, skor, kadro yok; eski pilot veya 99 maç sonuç kontrolü yeniden başlatılmadı.

### Lig bazında sayılar (güncel sezonda kayıtlı takım / evde 8 altı / deplasmanda 8 altı)

| Lig | Aktif takım | Ev rolü az | Dep rolü az |
|---|---:|---:|---:|
| ENG1 | 20 | 3 | 3 |
| ENG2 | 24 | 5 | 1 |
| GER1 | 18 | 3 | 3 |
| ESP1 | 20 | 3 | 3 |
| ITA1 | 20 | 3 | 3 |
| FRA1 | 18 | 2 | 2 |
| NED1 | 18 | 3 | 3 |
| TUR1 | 18 | 3 | 3 |
| POR1 | 18 | 2 | 2 |
| BEL1 | 18 | 3 | 3 |
| **Toplam** | **192** | **30** | **26** |

### Araştırma eşikleri — üretim güven sınırı DEĞİL

- İç sahada geçmiş maç sayısı 8'den azsa `HISTORICAL_ROLE_LT8`.
- Aynı rolün güncel sezon maç sayısı 4'ten azsa `CURRENT_SEASON_ROLE_LT4`.
- Güncel sezonda her sahada oynadığı maçlar toplamı 6'dan azsa `CURRENT_SEASON_TOTAL_LT6`.
- Takım son 60 günde gözlenmediyse `LAST_MATCH_MORE_THAN_60_DAYS_OLD`.
- Ligde hiç görünmeyen takımda `UNSEEN_TEAM_M4_LEAGUE_BASELINE_FALLBACK`.

Bu eşikler **istatistiksel olarak optimize edilmedi**, sadece eksik veri ve hangi maçta sonuçlara daha dikkatli bakılacağını görünür kılmak için seçildi. Eşik aşılınca güvenilirlik otomatik kabul edilmez; altında olunca mutlaka yanlış tahmin demek de değildir.

### Tek sonraki iş (Faz 2 hazırlığı)

Önce **bu 31 takımın geçtiği gelecek gerçek fikstürlerde**, modelin M4/C3/C2/B çıktılarıyla birlikte bir **veri yeterliliği açıklaması** gösteren, katsayıya dokunmayan ve SHA mühürlerini değiştirmeyen güvenli yan rapor tasarla. Eşiklerin gerçek hatayla ilişkisi ancak ileride maç önü mühürlü sonuçlar geldiğinde ölçülebilir.

Daha sonra KG/2.5 Üst için beklenen gol hatası mı, gol ilişkisi mi sınırlayıcı sorusuna yeni tarihli SHA mühürlerden giden mevcut `prospective_goal_error_attribution_263.py` ile devam et. **984 geçmiş maçlık DC/bivariate testi, 39 sonuçluk pilot, 99 arşiv işi yeniden açılmaz**. `main`, mevcut 2.6.3 aktif dalı, M4 katsayıları, LITE ve basketbol korunur.

### Dosyalar
- Araştırma kodu: `research/team_strength/team_coverage_audit_263.py`
- 9 regresyon: `research/team_strength/test_team_coverage_audit_263.py`
- Tam 10 lig takım-ID JSON: başarılı GitHub Actions çalışmasının `263-team-strength-10league-4617-coverage-risk-research-readonly` adlı artifact dosyası
- Araştırma dalı: `research/263-team-coverage-risk-audit-20261111`
