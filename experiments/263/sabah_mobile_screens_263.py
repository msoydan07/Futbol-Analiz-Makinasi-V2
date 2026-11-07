"""Phone-first read-only batch & single match screens from sealed morning records.

Never re-fits models or modifies S1/S2. Text mirrors the committed SHA.
Price comparison is separately rendered only after persisted API snapshot.
"""
from __future__ import annotations
import argparse,json,math,re
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime
from forward_c3 import read_aware
from market_fifth_baseline_263 import sealed_payload
from sabah_batch_263 import SCHEMA,sha
from classification_odds_263 import canonical_markets

MODELS=("B","C2","C3","M4")
MS=(("MS1","1"),("MSX","X"),("MS2","2"))
TR=ZoneInfo("Europe/Istanbul")
class ScreenError(ValueError):pass

def fmt(p):
 if not isinstance(p,(float,int)) or isinstance(p,bool) or not math.isfinite(p):
  return "—"
 return ("%.1f%%"%(100*p)).replace(".",",")
def safe(s):return str(s).replace("\n"," ").replace("\r"," ").replace("|","/").replace("<","‹").replace(">","›")
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def load_row(root,row):
 rel=row["forecast_path"]
 if not re.fullmatch(r"(forward_quad_263|forward_morning_263|forward_acceptance_263)/\d{4}-\d{2}-\d{2}/[a-f0-9]{24}\.json",rel):
  raise ScreenError("FORECAST_PATH_UNSAFE")
 root=Path(root).resolve();p=(root/rel).resolve()
 if not p.is_relative_to(root) or not p.is_file():raise ScreenError("FORECAST_MISSING")
 f=read(p);sealed_payload(f,"quad_forward_263_v1")
 if f["payload_sha256"]!=row["forecast_sha256"]:raise ScreenError("FORECAST_SHA_UNLINKED")
 return f

def decision(root,cohort,day,stem,f):
 p=Path(root)/"experiments/263/sabah_research"/cohort/day/stem/"decision.json"
 if not p.is_file():return None
 d=read(p);sealed_payload(d,"263_four_model_value_decision_research_v1")
 if d.get("forecast_sha256")!=f["payload_sha256"] or d.get("betting_authorized") is not False:
  raise ScreenError("DECISION_NOT_LINKED_OR_BETTING_AUTHORIZED")
 return d

def single(row,f,d):
 fx=f["fixture"];ko=read_aware(fx["kickoff_utc"]).astimezone(TR)
 title=safe(row["home"])+" – "+safe(row["away"])
 lines=["# "+title,"",
        ko.strftime("%d.%m.%Y %H:%M")+" TSİ · "+safe(fx["league"]),"",
        "**2.6.3 / mühürlü deneysel tahmin** · Resmî bahis veya S1/S2 onayı değildir.","",
        "## 1. Karar",
        ""]
 diag={}
 if d:
  diag={x["market"]:x for x in d.get("all_market_diagnostics",[])}
  cal=[(key,diag.get(key,{}).get("calibrated_probability")) for key,_ in MS]
  valid=[(k,v) for k,v in cal if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)]
  if valid:
   key,p=max(valid,key=lambda x:x[1]);lines.append("**Kalibre MS yönü (uygun DEV model):** "+dict(MS)[key]+" · "+fmt(p))
  else:lines.append("**Kalibre MS yönü:** HESAPLANAMADI (model medyanı kalibrasyon yerine geçmez)")
  lines.append("**S2 ana seçim:** "+("PAS" if not d.get("main_candidate") else "DENEYSEL / RESMÎ ONAYSIZ"))
  lines.append("**S2 alternatif:** "+("YOK" if not d.get("alternative_candidate") else "DENEYSEL / RESMÎ ONAYSIZ"))
  alerts=d.get("high_probability_alerts_not_bets") or []
  lines.append("**S1 yüksek olasılık:** "+("Araştırma uyarısı var, ONAYSIZ" if alerts else "ONAYSIZ / uygun uyarı yok"))
 else:
  lines+=["**Kalibre MS yönü:** karar kanıtı yok","**S2:** PAS / doğrulanmış oran yok",
          "**S1:** ONAYSIZ"]
 lines+=["","**Pinnacle:** Fiyat görüntüleme ayrı arşivde; aynı-anlı doğrulama yoksa piyasa yüzdesi gösterilmez.","",
         "**Rotasyon:** "+", ".join(safe(k)+"="+safe(v) for k,v in sorted(row.get("rotation",{}).items())),
         " (niteliksel; model yüzdesini değiştirmez)","",
         "## 2. B / C2 / C3 / M4",
         "","| Model | MS 1 | MS X | MS 2 | KG Var | 2,5 Üst |",
         "|---|---:|---:|---:|---:|---:|"]
 for name in MODELS:
  m=f["model_predictions"].get(name,{})
  if m.get("status")!="AVAILABLE":
   lines.append("| "+name+" | — | — | — | — | — |")
   continue
  z=canonical_markets(m["goals"]["markets"])
  vals=[name]+[fmt(z[k]) for k in ("MS1","MSX","MS2","BTTS_YES","OVER_2.5")]
  lines.append("| "+" | ".join(vals)+" |")
 lines+=["","## 3. Kanıt","",
         "- Tahmin SHA-256: "+f["payload_sha256"],
         "- Kilit UTC: "+f["created_at_utc"],
         "- Resmî fikstür: "+safe(fx.get("official_source","KANIT YOK")),
         "- Karar SHA: "+(d["payload_sha256"] if d else "YOK"),
         "- Kaynak/kadro/xG eksiklikleri ayrı denetlenir; uydurma sayısal düzeltme yok.",""]
 return "\n".join(lines)

def build(root,report):
 if report.get("schema")!=SCHEMA or report.get("payload_sha256")!=sha({k:v for k,v in report.items() if k!="payload_sha256"}):
  raise ScreenError("UNSEALED_BATCH")
 rows=[];singles={}
 for row in report["outcomes"]:
  if row["status"]=="REGISTERED_FOUR_MODELS_EXPERIMENTAL":
   f=load_row(root,row)
   d=decision(root,report["cohort"],report["day_turkey"],Path(row["forecast_path"]).stem,f)
   s=single(row,f,d)
   singles[Path(row["forecast_path"]).stem]=s
   calibrated="—"
   if d:
    relevant=[(x["market"],x.get("calibrated_probability")) for x in d.get("all_market_diagnostics",[])
              if x.get("market") in ("MS1","MSX","MS2") and isinstance(x.get("calibrated_probability"),(int,float))]
    if relevant:
     key,p=max(relevant,key=lambda a:a[1])
     calibrated=key.replace("MS","MS ")+": "+fmt(p)
   ko=read_aware(f["fixture"]["kickoff_utc"]).astimezone(TR)
   rows.append("| "+ko.strftime("%H:%M")+" | "+safe(row["home"])+" – "+safe(row["away"])+
               " | "+calibrated+" | PAS/ONAYSIZ | "+safe(row.get("decision_status","MODEL_ONLY"))+" |")
  else:
   rows.append("| — | "+safe(row["home"])+" – "+safe(row["away"])+
               " | — | — | "+row["status"]+" |")
 content=["# 2.6.3 — Sabah maç analizleri","",
          "**"+report["day_turkey"]+" (TSİ) · "+report["cohort"]+"**","",
          str(report["new_forecasts"])+" yeni mühürlü · "+
          str(report["already_sealed"])+" önceden kayıtlı · "+
          str(report["blocked"])+" engelli","",
          "Bu özet, tekli ekranlarla aynı değişmez tahmin SHA'sını kullanır.",
          "Bahis onayı yok. Oran ve EV yoksa S2 = PAS.","",
          "| Saat TSİ | Maç | Kalibre yön* | S2 | Kanıt |",
          "|---|---|---:|---|---|",*rows,"",
          "*İlgili DEV kalibrasyonu varsa görüntülenir; dört modelin ortalaması değildir.*","",
          "Rotasyon ve dört model yüzdeleri her maçın tekli ayrıntı sayfasındadır.",""]
 return "\n".join(content),singles

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--report",required=True);p.add_argument("--root",default=".")
 p.add_argument("--output-dir",required=True)
 a=p.parse_args();summary,singles=build(a.root,read(a.report))
 out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
 with (out/"summary.md").open("x",encoding="utf-8") as f:f.write(summary)
 for name,content in singles.items():
  folder=out/"matches";folder.mkdir(exist_ok=True)
  with (folder/(name+".md")).open("x",encoding="utf-8") as f:f.write(content)
 print(json.dumps({"mobile_single_count":len(singles),"summary":str(out/"summary.md")}))
if __name__=="__main__":main()
