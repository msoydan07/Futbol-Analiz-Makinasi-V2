# Futbol 2.6.3 — Maç sabahı gerçek hazır bulunuşluk kontrolü
**Denetim tarihi:** 2026-11-19  
**Kaynak dal:** `research/263-13-lig-22-havuz-20261113`, operasyon tetikleyici dal: `experiment/263-toplu-karsilastirma`  
**Sonuç:** **MAÇ SABAHI TAM HAZIRLIK ONAYI YOK — AÇIK ENGELLER VAR**.

> Bu belge, `docs/263_KARAR_DEFTERI_TEK_GECERLI_KAYNAK.md` dosyasındaki **D-ODDS-001** kararını uygular. Oran kaynağı iddaa.com iki kullanıcı PDF'sidir. 1. PDF ile tek tahmin ve mühür; 2. PDF ile **yalnız futbol yorumu/oran hareketi**, tahmin yeniden hesaplanmaz.

## Denetlendi — tekrardan veri toplama gerekmedi
1. Kullanıcının kabul ettiği **4.618 maçlık özel dondurulmuş snapshot**: SHA-256 `3b13921daafab70aa121fe807fea0a74e0c72f0fc2381366b183f621edea762c`.
2. Eski **4.413 maçlık** tarihsel kaynak: SHA-256 `35c5e7b4e0fad45c592fd51cf094616f2ff60330ce52bcf21cd595968169f5a1`.
3. Karşılaştırmada **4.413 fixture_id eksiksiz var**, maç kimliği, lig, sezon, tarih, ev/dep, skor ve sonuçta **0 uyumsuzluk**.
4. **205 yeni skor kaydı** ayrı eklendi; toplam 4.618 kayıt. Özel araştırma alanında, xG sütunları içermeyen ve yalnız eski 26 sütunluk skor şemasıyla uyumlu bir CSV projeksiyonu yazıldı. SHA-256: `54250bb6107250d0623b74ad9c56f90731f02d10dab3bf386deefb27aae487ea`.
5. Kaynak hash / bütünlük / eski satır koruması / xG gizliliği / olumsuz kaynak değiştirme dahil **7 yerel kontrol geçti**. **Bu, canlı kaynak kabulü veya GitHub iş akışının veri bağını değiştirdiğimiz anlamına gelmez.** Özel kaynak/veriler kamu reposuna yüklenmedi.

## Gerçek kod engelleri (kanıtlanan)

| Öncelik | Bulgu | Kod/kanıt | Maç günü etkisi |
|---|---|---|---|
| P0 | Maç önü workflow hâlâ `2026-11-10_completed_4617_scores_only.csv` kullanıyor ve 4.413 baseline'ı PIN'liyor | `.github/workflows/263-sabah-new100-on-request.yml`, `forward_quad.verify_snapshot` | 4.618 özel kabul anlık analize **otomatik bağlı değil** |
| P0 | `MAX_DATA_AGE_DAYS=10`; donmuş lig son skorları çoğu 8 Kasım, ENG2 7 Kasım; 20 Kasım'da 12/13 gün fark | `forward_c3.py`, `forward_quad.py` | Kaynak aslında eksiksiz olsa bile `stale_history_refresh_required` engeli verebilir. **10 günü körlemesine yükseltme/kaldırma**; resmi bitmiş maç denetimi gerekir |
| P0 | Resmi fixture, takım alias, saat, ilk PDF'yi gerçek 10 lig maçlarıyla birlikte uctan uca kabul etme kanıtı henüz yok | `iddaa_pdf_one_step_263.py` + ilgili araştırma belge/testleri | İlk gerçek PDF'de satır bazlı BLOKE riski var |
| P0 | **Oran kendi modelimizin tercihini yönetmemeli**, ama mevcut `four_model_value_policy_263.py` içinde EV, no-vig edge ve oran yokluğu seçim/PAS kapısı olarak kullanılıyor | `docs/263_KARAR_DEFTERI_TEK_GECERLI_KAYNAK.md` D-MARKET-006; `four_model_value_policy_263.py` | **Daha önce kilitlenen MARKET=5. referans kararına aykırı.** Model seçimi ve yalnız karşılaştırma amaçlı fiyat raporu ayrıştırılmalı; ikinci PDF asla kararı değiştirmemeli |
| P0 | Son 2026-11-19 kalibrasyon/model seçimi araştırma kodu canlı tahmin ve ilk PDF ile entegre değil | `four_model_value_policy_263.py` hâlâ eski C3/M4 DEV kilidini kullanıyor | Yeni karar sistemi kendiliğinden devreye girmez; eski araştırma kararını yeni sonuç gibi sunma |
| P1 | `new100` akışı en az 3 model + C3/M4 şart koşuyor; C2 sezona erken başladığında eksik kalabilir | `sabah_batch_263.py` | Teknik blok ile geçerli PAS ayrı raporlanmalı |
| P1 | new100 kabul kapasitesi 100, `forward_quad.py` içindeki `PILOT_GOAL=96` | `sabah_batch_263.py` / `forward_quad.py` | Ayrı yeni kohortta dosya sayısı 97–100 olursa sınır engeli olabilir; eski 96 kayıt kesinlikle değiştirilmez |
| P1 | İkinci PDF futbol yorumu modülü **research** dalında var; eski operasyon `experiment` dalında aynı dosya yok | `iddaa_pdf_last_review_263.py` ve dal karşılaştırması | Tek çalışan uçtan uca hat henüz oluşmadı |
| P1 | İkinci PDF'nin XI gözlemleri program tarafından otomatik yeniden teyit edilmiş sayılamaz | `iddaa_pdf_last_review_263.py` | Teyitsiz kadro yorumu neden-sonuç gibi sunulmayacak |

## Önceden karara bağlanmış oran iş akışı — **DEĞİŞMİYOR**

**Sabah:** Kullanıcının iddaa PDF'si → yedi pazar (MS 1/X/2; KG Var/Yok; 2.5 Alt/Üst) → fixture/alias/sonuç tarihi kontrolü → B/C2/C3/M4 mevcut matematikle hesap → **model güvenilirliğiyle oranlardan BAĞIMSIZ ana/alternatif/PAS** → bir adet SHA'lı sabah tahmin ve tercih/PAS mührü. **MARKET beşinci referanstır**: aynı maçın iddaa marjsız piyasa olasılıkları ayrı karşılaştırma alanıdır; ana/alternatif/PAS'ı değiştirmez.

**İlk 11 sonrası:** İkinci kullanıcı iddaa PDF'si → aynı maça bağlanan iki fiyatın farkı → ilk 11/sakat/rotasyon/taktik ve kanıt varsa olası futbol gerekçesi → **ayrı ekleme-only yorum dosyası**; yeni tahmin, yeni EV/ana tercih, ikinci mühür **YOK**.

**Maç sonrası:** Yalnız sabah orijinal SHA'lı karar ve ayrı yorum kaydı sonuçla karşılaştırılır. Değişiklik yapılmaz.

## İşi bitirmiş saymak için kabul kapıları (tek seferlik)

- [ ] `4618` skorları yeni maç önü modelin veri şemasına ve geçerli kaynağa **kaynak kanıtıyla** alınmış; eski 4.413 alanları, mühürler ve M4 SHA korunmuş.
- [ ] 10+ günlük arada gerçekten bitmiş yeni lig maçının eksik olmadığını **resmî sonuç fikstürüyle** kontrol eden, izin verildiğinde arayı makul kabul eden, aksi hâlde hata veren araştırma kontrolü uygulanmış.
- [ ] Gerçek kapsam ligi iddaa sabah PDF'si ile aynı maç için **resmi fixture → B/C2/C3/M4 → kalibrasyon/tek tercih-PAS → SHA → rapor** tek işlemde kanıtlı.
- [ ] İkinci PDF ve kaynaklı ilk 11 kontrolü birinci SHA'yı **değiştirmeden** ekleme-only yorum oluşturmuş.
- [ ] Yanlış takım, yanlış PDF, eksik pazar, eski oran, eksik C2/M4, başlama sonrası talep, paket/ağ sorunu ayrı teknik nedenleriyle dönmüş; sahte PAS veya sahte başarı yok.
- [ ] Aynı işlemler **tetikleyici operasyon dalında** okunabilir/çalışabilir; yalnız local sentetik test veya farklı araştırma dalı yeterli değil.

**Bu kontroller tamamlanana kadar canlıya hazır denmez.** `4618` özel skor projeksiyonunun oluşturulması P0 veri biçimi aşamasını ilerletti; P0 canlı kaynak kabulü, programın tarihsel kaynak kısıtları ve gerçek PDF uçtan uca kabulü hâlâ açıktır.

**Güvenlik kararı:** Ana M4, mevcut çalışan 2.6.3 üretim, tarihi SHA mühürleri, 96 pilot ve otomasyonlarda **değişiklik yapılmadı**. Yeni özel xG/score CSV'leri GitHub'a yüklenmedi.
