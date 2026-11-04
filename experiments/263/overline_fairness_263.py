"""Research-only no-automatic-Over-1.5 rule; never promotes picks or models."""
import csv,hashlib,json,math,argparse
from datetime import date
from pathlib import Path
SOURCE="69d687965500a260cc965a1482c23c1e07f11ebcabb1adaa9441dc6a17334a14"
LOCK="1038b6e9cd1f0bcbceb97367e261bc579b07a56e4e2dc5193c2f247e51e18ffb"
def valid(x):
 if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or not 0<=x<=1:raise ValueError("bad_probability")
 return float(x)
def compare(p15,p25,b15,b25):
 p15,p25,b15,b25=map(valid,(p15,p25,b15,b25))
 if p25>p15+1e-10 or b25>b15+1e-10:raise ValueError("nested_goal_inconsistency")
 a,c=p15-b15,p25-b25
 positive=[(k,v) for k,v in (("OVER_1.5",a),("OVER_2.5",c)) if v>0]
 leader=max(positive,key=lambda x:(round(x[1],12),x[0]=="OVER_2.5"))[0] if positive else None
 return {"p_15":round(p15*100,2),"p_25":round(p25*100,2),
         "lift_15_pp":round(a*100,2),"lift_25_pp":round(c*100,2),
         "raw_p_winner":"OVER_1.5","baseline_research_winner":leader,
         "nested_goals_not_independent_alternatives":True,"S1_approved":False,"S2_approved":False}
def baseline(rows,league,day):
 date.fromisoformat(day)
 past=[r for r in rows if r["league"]==league and r["match_date"]<day]
 if len(past)<100:raise ValueError("insufficient_history")
 totals=[]
 for r in past:
  x,y=r.get("home_goals"),r.get("away_goals")
  if x in (None,"") or y in (None,""):raise ValueError("missing_prior_score")
  a,b=int(x),int(y)
  if min(a,b)<0:raise ValueError("negative_goals")
  totals.append(a+b)
 n=len(totals)
 return {"p15":sum(x>=2 for x in totals)/n,"p25":sum(x>=3 for x in totals)/n,
         "n":n,"last_date":max(r["match_date"] for r in past)}
def report(forecast,rows,sha):
 if forecast.get("payload_sha256")!=LOCK or forecast.get("schema")!="quad_forward_263_v1":raise ValueError("wrong_forecast")
 content={k:v for k,v in forecast.items() if k!="payload_sha256"}
 check=hashlib.sha256(json.dumps(content,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
 if check!=LOCK:raise ValueError("tampered_forecast")
 d=forecast.get("data",{})
 if (sha!=SOURCE or d.get("snapshot_sha256")!=SOURCE or d.get("human_source_acceptance") is not False or d.get("research_shadow_unverified_source") is not True or forecast.get("status")!="EXPERIMENTAL_EARLY_SHADOW_UNVERIFIED_SOURCE_NO_BETTING"):
  raise ValueError("unaccepted_snapshot_cannot_become_approved")
 f=forecast["fixture"]
 if f["fixture_verification"]!="VERIFIED_BY_LIVE_OFFICIAL_GATE" or forecast["created_at_utc"]>=f["kickoff_utc"]:raise ValueError("not_preko")
 b=baseline(rows,f["league"],f["match_local_date"])
 if set(forecast["model_predictions"])!={"B","C2","C3","M4"}:raise ValueError("four_models_required")
 result={}
 for m,v in forecast["model_predictions"].items():
  if v["status"]!="AVAILABLE":raise ValueError("unavailable_model")
  p=v["goals"]["markets"]
  result[m]=compare(p["OVER_1.5"],p["OVER_2.5"],b["p15"],b["p25"])
 return {"schema":"263_over15_anti_monopoly_research_v1","status":"RESEARCH_NOT_APPROVED",
         "source_sha256":sha,"forecast_sha256":LOCK,
         "league":f["league"],"match_date":f["match_local_date"],"baseline":b,
         "models":result,"main_pick":None,"alternative_pick":None,"betting_authorized":False,
         "S1_S2_approved":False,"model_promoted":False,"pilot_increment":0}
def render(r):
 b=r["baseline"]
 a=["# 1,5 Üst ve 2,5 Üst — araştırma sıralaması","",
 "**YALNIZ ARAŞTIRMA — resmi S1/S2, bahis veya ana/alternatif onayı değildir.**","",
 f"Geçmiş {r['league']}: {b['n']} maç (sonuçlar maç tarihinden önce).",
 f"1,5 Üst lig bazı %{b['p15']*100:.1f}; 2,5 Üst lig bazı %{b['p25']*100:.1f}.","",
 "| Model | 1,5 Üst % | 2,5 Üst % | 1,5 baza fark | 2,5 baza fark | Araştırma lideri |",
 "|---|---:|---:|---:|---:|---|"]
 for m,p in r["models"].items():
  leader={"OVER_1.5":"1,5 Üst","OVER_2.5":"2,5 Üst",None:"YOK"}[p["baseline_research_winner"]]
  a.append(f"| {m} | %{p['p_15']:.1f} | %{p['p_25']:.1f} | {p['lift_15_pp']:+.1f} yp | {p['lift_25_pp']:+.1f} yp | {leader} |")
 a+=["","Bu sadece baz farkı; modelin gerçek doğruluk, kalibrasyon, oran değeri veya bahis sinyali değildir.",
 "1,5 Üst yalnız ham olasılığından dolayı öne çıkmaz; ama kendi başarısı kanıtlanınca seçilebilir.",
 "Aynı maçta 1,5 ve 2,5 Üst birbirine bağlı olaylardır; bağımsız ana/alternatif sayılmaz.",
 "Sonraki geniş test: walk-forward kalibrasyon/Brier/log-loss, PAS–kapsama ve gerçek tarihli fiyatlarla EV.",
 "4.509 maç kaynak onayı bekliyor. Modeller ve 96 maçlık ileri pilot değiştirilmedi."]
 return "\n".join(a)+"\n"
def main():
 a=argparse.ArgumentParser()
 for k in ("history","forecast","json_out","md_out"):a.add_argument("--"+k.replace("_","-"),required=True)
 opt=a.parse_args()
 raw=Path(opt.history).read_bytes()
 sha=hashlib.sha256(raw).hexdigest()
 if sha!=SOURCE:raise SystemExit("wrong_history_sha")
 rows=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
 if len(rows)!=4509:raise SystemExit("not_4509_rows")
 f=json.loads(Path(opt.forecast).read_text(encoding="utf-8"))
 r=report(f,rows,sha)
 for path in (opt.json_out,opt.md_out):
  p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():raise SystemExit("refuse_overwrite")
 Path(opt.json_out).write_text(json.dumps(r,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 Path(opt.md_out).write_text(render(r),encoding="utf-8")
 print(json.dumps({"status":r["status"],"models":{k:v["baseline_research_winner"] for k,v in r["models"].items()},"main_pick":None,"source_n":r["baseline"]["n"]},ensure_ascii=False))
if __name__=="__main__":main()