# Futbol Makinası 2.6.3 — Döngü kontrolü ve maç doğrulama kapsamı
Tarih: 2026-11-01

## Tekrarlanmayan işler
- Geçmiş 4.413 maçlık matematik performans deneyleri, C2/C3 ve ilk yarı/korner testleri **yeniden çalıştırılmadı**.
- Mevcut `analyze_named_match_gate.py` ve `data/team_aliases_reviewed.csv` zaten GitHub deney dalında var. Maçkolik ismini takım kimliğine bağlama kuralı daha önce kararlaştırılmıştır.
- Ana `main` ve `feature/01-kimlikler` üretim dalları değiştirilmedi. Gerçek maç tahmini, pilot ve oran/EV çalışması yapılmadı.

## Yeni yerel çalışma — GitHub'a henüz aktarılmadı
- Kayıtlı 215 takım, 370 alias ve iki sezonun lig üyeliklerinden özgün 2,4 MB kimlik kayıt dosyasına bağlı, 85 KB salt-okunur bir **kimlik dizini** oluşturuldu. Özgün dosyanın SHA-256 özeti ve dizinin kendi bütünlük özeti korundu.
- Özgün 4.413/4.413 geçmiş fikstür kimliği ilgili sezon/lig üyeliğiyle karşılaştırıldı; uyumsuzluk görülmedi. Bu, gelecekteki maçın oynanacağını **doğrulamaz**.
- Önceden oluşturulmuş `mackolik_identity_gate_263.py` içindeki bu dizin yolu ve tarih-doğrulanmış/saat-yayımlanmamış durumu tamamlandı.
- Mevcut federasyon/kulüp kaynaklarının alan adı uyumsuzlukları giderildi: `psg.fr` (FRA1), `knvb.nl` (NED1), `kvmechelen.be` (BEL1). Başka keyfi alan adlarına güvenilmiyor.
- Değişen yerel kod üzerinde 49 sentetik/birim test geçti. **Resmî siteler üzerinden gerçek uçtan uca doğrulama testi yapılmadı.**
- Hazırlanan modül, test ve dizin dosyalarının tamamı henüz GitHub üzerinde yer almadığından **GitHub dağıtımı tamamlandı denemez**.

## Mevcut on resmî adaptörün statik kapsam denetimi
| Lig | Mevcut kaynak yaklaşımı | Kapsam |
|---|---|---|
| ENG1 | Premier League Ekim–Kasım değişiklik haberi | Belirli dönem, genel değil |
| ENG2 | EFL 29 Ekim–4 Kasım hakem duyurusu | Belirli dönem, genel değil |
| GER1 | Bundesliga/DFL fikstür sayfası | Genel uç nokta, canlı erişim doğrulanmadı |
| ESP1 | LaLiga 2026/27 11. hafta URL'si | Tek hafta |
| ITA1 | Serie A 10. hafta hakem duyurusu | Tek hafta |
| FRA1 | PSG 9. maç haftası duyurusu | Belirli takım/hafta |
| NED1 | KNVB Eredivisie programı | Genel kaynak, canlı erişim doğrulanmadı |
| TUR1 | TFF haftalık Süper Lig sayfası | Güncel sayfa ayrıştırması henüz sınanmadı |
| POR1 | 12. haftaya kadar ilan edilen saatler haberi | Sınırlı dönem |
| BEL1 | KV Mechelen'in 31 Ekim maçına özel kontrol | Artık geçmişte; genel doğrulama yapamaz |

## Nihai iş sırası ve kabul şartı
1. **Önce** yerel kimlik dizini, 2.6.3 maç giriş modülü ve testlerini tek seferde GitHub deney dalına aktar; SHA/dizin/parite denetimini doğrula.
2. Sabit haber/hafta bağlantılarına dayalı adaptörleri **kullanıcının seçtiği herhangi bir maç için**, ilgili federasyon/lig veya kulüp resmî kaynağında **o anda** doğrulama yapan kodlara geçir. Kaynak erişilemiyorsa `NOT_VERIFIED`, sahte varlık veya saat bilgisi yok.
3. Maçkolik isimleri yalnızca eşleştirme girdisi; resmî kanıt değil. Kimlik eşleşmesi + resmî ev/deplasman/tarih gözlemi bir arada olmadıkça analiz yok. Saat açıklanmamışsa ayrı `NOT_ANNOUNCED`.
4. Önce tüm uygulama ve source-adapter güvenlik testlerini paket halinde hazırla, **sonunda tek toplu GitHub Actions doğrulaması** yap. Yeni bir model performans testi/pilot/gerçek maç kaydı başlatma.

Bu belge statik kod denetimi ve tamamlanan **yerel** geliştirmeyi ayırır. Resmî 10 lig kapsamı henüz kabul edilmemiştir.
