"""Human-readable read-only views of already recorded B/C2/C3/M4 pilot predictions.

No model fitting, fixture lookup, price scraping or betting authorization.
Write once before kickoff and verify identical content after branch rebase.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from classification_odds_263 import canonical_markets
from market_fifth_baseline_263 import sealed_payload

MODELS=("B","C2","C3","M4")
MARKETS=("MS1","MSX","MS2","OVER_1.5","UNDER_1.5","OVER_2.5","UNDER_2.5",
         "OVER_3.5","UNDER_3.5","BTTS_YES","BTTS_NO")
NAMES={"MS1":"MS 1","MSX":"MS X","MS2":"MS 2",
       "OVER_1.5":"1.5 Üst","UNDER_1.5":"1.5 Alt",
       "OVER_2.5":"2.5 Üst","UNDER_2.5":"2.5 Alt",
       "OVER_3.5":"3.5 Üst","UNDER_3.5":"3.5 Alt",
       "BTTS_YES":"KG Var","BTTS_NO":"KG Yok"}
FORECAST_PATH=re.compile(r"forward_quad_263/(\d{4}-\d{2}-\d{2})/([a-f0-9]{24})\.json")
RUN_SHA=re.compile(r"[a-f0-9]{40}")
OK="REGISTERED_FOUR_MODELS_EXPERIMENTAL"

def clean(v):
    return str(v).replace("|","/").replace("\r"," ").replace("\n"," ").replace("<","‹").replace(">","›").strip()
def pct(x):
    return "—" if x is None else ("%0.1f"%(100*x)).replace(".",",")+"%"
def number(x):
    return "—" if x is None else ("%0.2f"%x).replace(".",",")
def name(x):
    return NAMES.get(x,clean(x)) if x else "—"
def load(p):
    return json.loads(p.read_text(encoding="utf-8"))
def within(root,rel):
    p=(root/rel).resolve()
    if not p.is_relative_to(root) or not p.is_file():raise ValueError("USER_REPORT_SOURCE_MISSING_OR_UNSAFE")
    return p

def decision(root,day,stem,f):
    choices=(
      ("CURRENT_OR_MIXED",root/"experiments/263/quad_priced_decisions"/day/(stem+".json")),
      ("MORNING_ONLY",root/"experiments/263/quad_conditional_morning_decisions"/day/(stem+".json")),
      ("NO_PRICE",root/"experiments/263/quad_research_links"/day/stem/"preprice_decision.json"))
    for stage,p in choices:
        if not p.is_file():continue
        d=load(p)
        sealed_payload(d,"263_four_model_value_decision_research_v1")
        if d.get("forecast_sha256")!=f["payload_sha256"] or d.get("fixture")!=f["fixture"]:
            raise ValueError("USER_REPORT_WRONG_FORECAST_IN_DECISION")
        if stage=="CURRENT_OR_MIXED" and not d.get("quote_sha256"):
            raise ValueError("USER_REPORT_MISSING_CURRENT_PRICE_SHA")
        if stage=="MORNING_ONLY" and (not d.get("morning_quote_sha256") or d.get("quote_sha256")):
            raise ValueError("USER_REPORT_INVALID_MORNING_SHA_LINK")
        if stage=="NO_PRICE" and (d.get("quote_sha256") or d.get("morning_quote_sha256")):
            raise ValueError("USER_REPORT_UNPRICED_WITH_PRICE_SHA")
        if d.get("betting_authorized") is not False:
            raise ValueError("USER_REPORT_UNAUTHORIZED_BETTING")
        return d,stage
    raise ValueError("USER_REPORT_MISSING_BASELINE_PAS")

def label(row,f):
    req=row.get("requested",{})
    if isinstance(req,dict) and req.get("home") and req.get("away"):
        if req.get("league")!=f["fixture"]["league"]:
            raise ValueError("USER_REPORT_WRONG_LEAGUE_NAME")
        return clean(req["home"])+" – "+clean(req["away"])
    return clean(f["fixture"]["home_id"])+" – "+clean(f["fixture"]["away_id"])

def pick(c):
    if not c:return "PAS"
    status=" (sabah / KOŞULLU)" if c.get("price_age_class")=="MORNING_ARCHIVE_NOT_CURRENT" else " (T−60)" if c.get("price_age_class")=="CURRENT_T60" else ""
    return name(c["market"])+" "+pct(c.get("calibrated_probability"))+" · oran "+number(c.get("observed_odds"))+status

def top_score(m):
    scores=m.get("goals",{}).get("top_scores",{})
    if not isinstance(scores,dict):return "—"
    valid=[(float(v),clean(k)) for k,v in scores.items()
           if isinstance(v,(int,float)) and not isinstance(v,bool) and 0<=v<=1]
    if not valid:return "—"
    val,score=max(valid,key=lambda x:(x[0],x[1]))
    return score+" "+pct(val)

def market_row(key,d):
    if d is None:return "| "+name(key)+" | — | — | — | — | — | Hesaplanamadı |"
    vals=sorted(d.get("raw_model_probabilities",{}).values())
    n=len(vals)
    median=(vals[(n-1)//2]+vals[n//2])/2 if n else None
    odds=number(d.get("observed_odds"))
    ev=("%+.1f%%"%(100*d["EV"])).replace(".",",") if d.get("EV") is not None else "—"
    age={"MORNING_ARCHIVE_NOT_CURRENT":"Sabah/koşullu","CURRENT_T60":"T−60"}.get(d.get("price_age_class"),"Oran yok")
    when=clean(d.get("price_checked_at_utc") or "—")
    reasons=d.get("qualification_reasons",[])
    verdict="Değer adayı" if not reasons else "PAS / "+clean(", ".join(reasons))
    return "| "+name(key)+" | "+pct(median)+" | "+pct(d.get("calibrated_probability"))+" | "+odds+" | "+ev+" | "+age+" ("+when+") | "+verdict+" |"

def details(row,f,d,stage):
    fx=f["fixture"];data=f["data"]
    lines=[
       "# Tek maç analizi — "+label(row,f),"",
       "**2.6.3 DENEYSEL / MAÇ ÖNCESİ — resmî bahis veya kesin sonuç tavsiyesi değildir.**","",
       "Lig: "+clean(fx["league"])+" · Türkiye tarihi: "+clean(fx["match_local_date"]),
       "Başlama UTC: "+clean(fx["kickoff_utc"])+" · Tahmin kaydı UTC: "+clean(f["created_at_utc"]),
       "Resmî fikstür kaynağı: "+clean(fx.get("official_source","DOĞRULANAMADI")),
       "Fikstür kontrol UTC: "+clean(fx.get("source_checked_at_utc","DOĞRULANAMADI")),"",
       "## A. Gerçek kaydedilmiş veriler",
       "- Kaynak kabul sınıfı: **"+clean(data.get("snapshot_acceptance","DOĞRULANAMADI"))+"**. Bu sınıf bütün maçların bağımsızca yeniden doğrulandığını göstermez.",
       "- Önceki lig maç sayısı: **"+clean(data.get("league_history_rows","—"))+"**; son kayıtlı sonuç: **"+clean(data.get("league_latest_result_date","DOĞRULANAMADI"))+"**.",
       "- xG/xGA, güncel sakatlık, cezalılar, ilk 11, hava durumu: **BU DÖRTLÜ KAYITLA DOĞRULANAMADI**. Ayrı kontrol yapılmış olabilir; burada uydurulmaz.","",
       "## B. B / C2 / C3 / M4 ayrı tahminleri",
       "| Model | MS 1 | MS X | MS 2 | 2.5 Üst | KG Var | Beklenen gol λ ev/deplasman | En olası skor |",
       "|---|---:|---:|---:|---:|---:|---:|---|"]
    for m in MODELS:
        r=f["model_predictions"].get(m,{})
        if r.get("status")!="AVAILABLE":
            lines.append("| "+m+" | — | — | — | — | — | — | Hesaplanamadı: "+clean(r.get("reason",r.get("status","VERİ YOK")))+" |")
            continue
        goals=r["goals"];p=canonical_markets(goals["markets"])
        vals=[m,pct(p["MS1"]),pct(p["MSX"]),pct(p["MS2"]),pct(p["OVER_2.5"]),
              pct(p["BTTS_YES"]),number(goals.get("lambda_home"))+"/"+number(goals.get("lambda_away")),top_score(r)]
        lines.append("| "+" | ".join(vals)+" |")
    lines+=["","Model yüzdeleri basit ortalamayla birleştirilmez; geçmiş performans kalibrasyonu karar aşamasında ayrı değerlendirilir.","",
        "## C. Kalibre olasılıklar ve piyasa fiyatları",
        "| Pazar | Modellerin medyanı* | Kalibre yüzde | Oran | EV | Gözlem zamanı | Eleme / değer durumu |",
        "|---|---:|---:|---:|---:|---|---|"]
    diag={x["market"]:x for x in d["all_market_diagnostics"]}
    lines.extend(market_row(k,diag.get(k)) for k in MARKETS)
    lines+=["","*Medyan betimleyicidir; kalibre karar yüzdesi yerine kullanılmaz.*","",
        "## D. En olası sonuç ve matematiksel değerlendirme",
        "- En olası 1X2 (açıklayıcı dört-model medyanı): **"+name(d.get("descriptive_most_likely_1x2_by_model_median"))+"**.",
        "- Tek skor tahminleri her model satırında ayrı gösterildi; birleşik tek skor olasılığı uydurulmadı.",
        "- Oran kanıtı: **"+clean(d.get("quote_status","DOĞRULANAMADI"))+"**; sabah fiyatı: **"+clean(d.get("morning_quote_status","NO_MORNING_ARCHIVE"))+"**.",
        "- 1.5 Üst yalnız yüksek yüzde nedeniyle ana tercih yapılmaz. Model desteği, fiyat, EV ve kalibrasyon koşulları gerekir.","",
        "## E. Ana tercih / alternatif / PAS",
        "- **Ana tercih:** "+pick(d.get("main_candidate"))+".",
        "- **Alternatif (ayrı aile):** "+(pick(d["alternative_candidate"]) if d.get("alternative_candidate") else "YOK")+".",
        "- Nihai karar statüsü: **"+clean(d.get("status","DOĞRULANAMADI"))+"**."]
    main=d.get("main_candidate");alt=d.get("alternative_candidate")
    for title,c in (("Ana",main),("Alternatif",alt)):
        if not c:continue
        ev=("%+.1f%%"%(100*c["EV"])).replace(".",",")
        lines.append("- "+title+" seçim: EV "+ev+"; "+clean(c.get("quote_source","—"))+"; fiyat zamanı UTC "+clean(c.get("price_checked_at_utc","—"))+".")
        if c.get("price_age_class")=="MORNING_ARCHIVE_NOT_CURRENT":
            lines.append("  - **KOŞULLU:** Sabah fiyatının T−60'da da alınabildiği doğrulanmadı; EV yalnız geçmiş fiyat senaryosudur.")
    if not main:
        lines.append("- **PAS nedeni:** "+clean(", ".join(d.get("PAS_reasons",[])) or "Yeterli değer adayı bulunamadı")+".")
        lines.append("- **PAS analiz yok demek değildir.** Fiyat olmasa da model olasılıkları yukarıda görünür.")
    lines+=["","## F. Kanıt ve sınırlamalar",
        "- Tahmin SHA: "+clean(f["payload_sha256"]),
        "- Karar SHA: "+clean(d["payload_sha256"]),
        "- Tarihsel veri SHA: "+clean(data.get("snapshot_sha256","DOĞRULANAMADI")),
        "- Güncel oran SHA: "+clean(d.get("quote_sha256") or "YOK"),
        "- Sabah oranı SHA: "+clean(d.get("morning_quote_sha256") or "YOK"),
        "- Kaynak karar sınıfı: "+stage,
        "- Bu dosyada kaç simülasyon veya kaç başarı testi yapıldığına dair doğrudan kanıt yoksa sayı eklenmez.",""]
    return "\n".join(lines)

def generate(root,report_path):
    root=Path(root).resolve();report_path=Path(report_path).resolve()
    if not report_path.is_relative_to(root) or not RUN_SHA.fullmatch(report_path.stem):
        raise ValueError("USER_REPORT_BATCH_PATH_INVALID")
    batch=load(report_path)
    if batch.get("schema")!="quad_named_match_batch_report_v1":raise ValueError("USER_REPORT_BATCH_SCHEMA_INVALID")
    outcomes=batch.get("outcomes")
    if not isinstance(outcomes,list) or not 1<=len(outcomes)<=12:
        raise ValueError("USER_REPORT_BATCH_MATCH_COUNT_INVALID")
    rows=[];files={};registered=pas=conditional=blocked=0
    for row in outcomes:
        if row.get("status")!=OK:
            blocked+=1
            req=row.get("requested",{})
            if not isinstance(req,dict):req={}
            title=clean(req.get("home","?"))+" – "+clean(req.get("away","?"))
            reason=clean(row.get("reason",row.get("status","DOĞRULANAMADI")))
            rows.append("| "+title+" | — | **ÜRETİLEMEDİ** | — | "+reason+" |")
            continue
        rel=row.get("path")
        match=FORECAST_PATH.fullmatch(rel) if isinstance(rel,str) else None
        if match is None:raise ValueError("USER_REPORT_FORECAST_PATH_INVALID")
        day,stem=match.groups();f=load(within(root,rel))
        sealed_payload(f,"quad_forward_263_v1")
        if f["payload_sha256"]!=row.get("payload_sha256") or day!=f["fixture"]["match_local_date"]:
            raise ValueError("USER_REPORT_FORECAST_SHA_OR_DATE_MISMATCH")
        d,stage=decision(root,day,stem,f)
        registered+=1
        if d.get("status")=="RESEARCH_PAS":pas+=1
        if d.get("any_selected_value_conditional",d.get("main_value_conditional",False)):
            conditional+=1
        diag=d.get("all_market_diagnostics",[])
        price_count=sum(x.get("observed_odds") is not None for x in diag)
        summary="{}; oranlı pazar {}; {}".format(stage,price_count,clean(d.get("status","—")))
        alt=pick(d["alternative_candidate"]) if d.get("alternative_candidate") else "YOK"
        rows.append("| "+label(row,f)+" | "+name(d.get("descriptive_most_likely_1x2_by_model_median"))+
                    " | **"+pick(d.get("main_candidate"))+"** | "+alt+" | "+summary+" |")
        files["matches/"+day+"/"+stem+".md"]=details(row,f,d,stage)
    summary="\n".join([
      "# Futbol Maç Analiz Makinası 2.6.3 — Toplu maç raporu","",
      "**DENEYSEL.** Bütün yüzdeler ve oranlar SHA-kayıtlı kaynaklardan okunur; örnek veri üretilmez.",
      "İstenen: {} · Tahminli: {} · PAS: {} · Koşullu seçimli: {} · Analizi engellenen: {}".format(
          len(outcomes),registered,pas,conditional,blocked),
      "Kaynak kayıt: "+clean(report_path.relative_to(root)),"",
      "| Maç | En olası MS sonucu | Ana tercih | Alternatif | Durum / açıklama |",
      "|---|---|---|---|---|",*rows,"",
      "Her maçın dört modeli, kalibre edilmiş pazar yüzdeleri, fiyat kanıtı, veri eksikleri ve karar gerekçesi matches/ altında ayrıca gösterilir.",
      "**PAS:** Analiz var ama fiyat veya yeterli değer yok. **ÜRETİLEMEDİ:** Gerçek tahmin kaydı oluşmadı.",
      "Sabah fiyatı kullanılırsa KOŞULLU ibaresi zorunludur; güncel oran farklıysa güncel olan önceliklidir.",""])
    return summary,files

def execute(root,report,out_dir,mode):
    root=Path(root).resolve();path=within(root,report)
    summary,details_files=generate(root,path)
    target=(root/out_dir/path.stem).resolve()
    if not target.is_relative_to(root):raise ValueError("USER_REPORT_OUT_DIR_UNSAFE")
    outputs={"summary.md":summary,**details_files}
    for rel,body in outputs.items():
        dest=target/rel
        if mode=="write":
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open("x",encoding="utf-8") as fp:fp.write(body)
        elif mode=="verify":
            if not dest.is_file() or dest.read_text(encoding="utf-8")!=body:
                raise ValueError("USER_REPORT_FILE_MISSING_OR_CHANGED_"+rel)
        else:raise ValueError("USER_REPORT_MODE_INVALID")
    return {"status":"REPORT_WRITTEN" if mode=="write" else "REPORT_VERIFIED",
            "summary":str(target/"summary.md"),"details":len(details_files),
            "forecast_and_decision_unchanged":True}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("write","verify"))
    p.add_argument("--report",required=True)
    p.add_argument("--root",default=".")
    p.add_argument("--out-dir",default="experiments/263/quad_human_reports")
    a=p.parse_args()
    print(json.dumps(execute(a.root,a.report,a.out_dir,a.mode),ensure_ascii=False))
if __name__=="__main__":main()
