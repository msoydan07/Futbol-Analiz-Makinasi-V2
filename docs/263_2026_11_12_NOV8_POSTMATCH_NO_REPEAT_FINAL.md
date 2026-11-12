# Futbol 2.6.3 — 8 Kasım sonuçları artık tek arşivden okunuyor

**Kapanış: 12 Kasım 2026.** Eski 40 `new100` maç önü SHA kaydı için maç-sonu denetimi bir kez sonuç arşivine bağlandı.

- **39 oynanmış maç:** nihai skor, maç önü SHA, özgün maç kimliği, lig, saat ve kaynak adresi `data/results_only_263/nov8_new100_terminal_archive_20261112.json` içinde kalıcı olarak kayıtlı.
- **1 ertelenmiş maç (Estoril–Marítimo):** skor üretilmedi, `POSTPONED_NO_SCORE` durumunda. Bu eski kohorta sahte 0-0 veya oynandı sonucu eklenmez.
- **Kanıt düzeyleri ayrı:** 3 bağımsız canlı TFF tekil maç sayfası kontrolü; 22 resmî lig sitesi web araştırma kaydı; 13 kulübün resmî sitesi web araştırma kaydı; 1 dış federasyon veri merkezi çapraz araştırması. Son 36 için 36 sağlayıcının aynı CI çalışmasında doğrudan ağdan doğrulandığı iddia edilmez; bu düzeyi `WEB_RESEARCH` etiketi taşır. İnsan onaylı resmî attestation sayısı 0.
- **Döngü düzeltmesi:** `experiments/263/postmatch_csv_bridge_263.py`, mevcut 40 eski SHA mührüyle aynı kohort olduğunda sonuçları doğrudan bu arşivden okur; CSV ve TFF kaynaklarına yeniden internet isteği yapmaz. Aynı çağrı tekrarlanırsa aynı 39+1 arşiv çıktısı döner. Gelecekte yeni maç kohortları oluşursa arşiv sabiti 40 SHA eşleşmeyeceği için eski ağ kaynağı araştırma kapısı devreye girer; yeni maç sonucu uydurulmaz.
- **Güvenlik:** Sahte SHA, değiştirilmiş sonuç, kaynak kanıt sınıfının haksız yükseltilmesi veya ertelemeye skor yazılması işlemi engeller; eski 40 tahmin SHA'sı, model kilidi ve 4.617 tarihçe değişmez.
- **Kısıt:** Bu dosya gelecekteki otomatik günlük araştırmalarda aynı bitmiş maçları tekrar araştırmamak için tutulan **sonuç araştırma arşividir**; insan onaylı resmî sonuç akışına sahte evrak girmez. Bu 39 sonuç eğitim verisine sessizce eklenmez, ROI/EV iddiası yapılmaz.

**Operasyon kararı:** 8 Kasım sonuç araştırması tekrar yapılmayacak. Ekranda bir daha bu maçları doğrula adımı açılmayacak; sadece skor çelişkisine dair yeni somut bir kanıt gelirse ayrı istisna incelenir.

Tek GitHub testi: `.github/workflows/263-nov8-terminal-postmatch-archive-ci.yml`.
