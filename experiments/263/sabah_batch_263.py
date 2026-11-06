"""2.6.3 morning batch, strictly pre-kickoff, independent 96 / new 100 cohorts.

Input is the pinned date-only 96-candidate file OR a user-approved named
morning manifest. Live official fixture verification is always required.
The original B/C2/C3/M4 calculation and DEV lock are not modified.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from forward_c3 import canonical_bytes,read_aware,valid_gate
from market_fifth_baseline_263 import sealed_payload
from sabah_fixture_rotation_263 import validate_legacy_candidates,rotation_from_official_inputs
TR=ZoneInfo("Europe/Istanbul")
SCHEMA="SABAH_TOPLU_KAYIT_V1"
REQUEST="SABAH_TOPLU_V1"
DIRS={"legacy96":"forward_quad_263","new100":"forward_morning_263"}
LIMIT={"legacy96":96,"new100":100}
LEAGUES={"ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1"}
PINNED96="803378e8ef0f1f285a3393a7231567eea8f25e80"
class Blocked(ValueError):pass

def sha(payload):return hashlib.sha256(canonical_bytes(payload)).hexdigest()
def save_new(file,payload):
 p=Path(file);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x",encoding="utf-8") as f:
  if isinstance(payload,str):f.write(payload)
  else:json.dump(payload,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
def named(cohort,day,src):
 if cohort not in DIRS:raise Blocked("UNKNOWN_COHORT")
 raw=Path(src).read_bytes();data=json.loads(raw)
 if cohort=="legacy96":
  blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
  if blob!=PINNED96:raise Blocked("PINNED_96_SHA_CHANGED")
  rows=validate_legacy_candidates(data)
  return [{"league":r["league"],"home":r["home"],"away":r["away"]} for r in rows if r["date"]==day]
 if (not isinstance(data,dict) or set(data)!={"schema","day_turkey","matches"}
  or data["schema"]!=REQUEST or data["day_turkey"]!=day):raise Blocked("MORNING_MANIFEST_INVALID")
 rows=data["matches"]
 if not isinstance(rows,list) or not 1<=len(rows)<=100:raise Blocked("MORNING_COUNT_INVALID")
 seen=set()
 for r in rows:
  if (not isinstance(r,dict) or set(r)!={"league","home","away"}
   or r["league"] not in LEAGUES or any(not isinstance(r[k],str) or not 1<=len(r[k].strip())<=100 for k in ("home","away"))):
   raise Blocked("INVALID_NAMED_MATCH")
  key=(r["league"],r["home"].casefold().strip(),r["away"].casefold().strip())
  if key in seen or key[1]==key[2]:raise Blocked("DUPLICATE_NAMED_MATCH")
  seen.add(key)
 return rows
def keys_in(*dirs):
 keys=set()
 for d in dirs:
  for path in Path(d).glob("*/*.json"):
   f=json.loads(path.read_text(encoding="utf-8"))
   sealed_payload(f,"quad_forward_263_v1")
   x=f["fixture"];key=(x["league"],x["home_id"],x["away_id"],x["kickoff_utc"])
   if key in keys:raise Blocked("DUPLICATE_FORECAST_COHORTS")
   keys.add(key)
 return keys

def run(cohort,day,src,history,baseline,acceptance,lock_path,root=".",now=None,
        lookup=None,predictor=None,baseline_fn=None,decision_fn=None,dev_lock_path='experiments/263/forward_dev_calibration_lock_263.json'):
 now=now or datetime.now(timezone.utc)
 if now.tzinfo is None:raise Blocked("AWARE_TIME_REQUIRED")
 now=now.astimezone(timezone.utc)
 tr=now.astimezone(TR)
 if tr.date().isoformat()!=day or not 5<=tr.hour<13:raise Blocked("NOT_SAME_TURKEY_MORNING")
 rows=named(cohort,day,src);root=Path(root)
 for path in (history,baseline,acceptance,lock_path,dev_lock_path):
  if not Path(path).is_file():raise Blocked("REQUIRED_HISTORY_OR_LOCK_MISSING")
 if lookup is None:
  from analyze_named_match_gate import run as lookup
 if predictor is None:
  from forward_quad import predict_quad_from_verified_gate as predictor
 if baseline_fn is None:
  from forward_empirical_baseline_263 import produce as baseline_fn
 if decision_fn is None:
  from four_model_value_policy_263 import decide as decision_fn
 lock=json.loads(Path(dev_lock_path).read_text(encoding="utf-8"))
 out_dir=root/DIRS[cohort];count=len(list(out_dir.glob("*/*.json")))
 seen=keys_in(root/"forward_quad_263",root/"forward_morning_263")
 if count>LIMIT[cohort]:raise Blocked("COHORT_LIMIT_EXCEEDED")
 outcomes=[]
 for request in rows:
  item={**request,"status":"BLOCKED_NO_FORECAST"}
  try:
   if count>=LIMIT[cohort]:raise Blocked("COHORT_LIMIT_REACHED")
   gate=lookup(request["league"],request["home"],request["away"])
   if not isinstance(gate,dict) or gate.get("status")!="VERIFIED":
    raise Blocked("OFFICIAL_GATE_FAILED:"+str(gate.get("reason") if isinstance(gate,dict) else "INVALID"))
   league,home,away,ko,checked,_=valid_gate(gate,now)
   if ko.astimezone(TR).date().isoformat()!=day:raise Blocked("OFFICIAL_DATE_NOT_TURKEY_TODAY")
   key=(league,home,away,ko.isoformat())
   if key in seen:item["status"]="ALREADY_SEALED_UNCHANGED";outcomes.append(item);continue
   path,forecast=predictor(gate,history,out_dir,lock_path,now=now,
                           base=baseline,source_audit=acceptance)
   sealed_payload(forecast,"quad_forward_263_v1")
   if not read_aware(forecast["created_at_utc"])<=now<ko:raise Blocked("POSTKICKOFF_FORBIDDEN")
   count+=1;seen.add(key)
   item.update(status="REGISTERED_FOUR_MODELS_EXPERIMENTAL",
               forecast_path=path.as_posix(),forecast_sha256=forecast["payload_sha256"],
               kickoff_utc=ko.isoformat())
   try:
    b=baseline_fn(forecast,history,now=now)
    d=decision_fn(forecast,b,lock,observation=None,now=now)
    if d["quote_sha256"] is not None or d["main_candidate"] is not None or d["status"]!="RESEARCH_PAS":
     raise Blocked("NO_PRICE_MUST_BE_PAS")
    prefix=root/"experiments/263/sabah_research"/cohort/day/path.stem
    save_new(prefix/"baseline.json",b);save_new(prefix/"decision.json",d)
    item["decision_status"]=d["status"];item["decision_sha256"]=d["payload_sha256"]
   except (ValueError,OSError,KeyError,TypeError) as exc:
    item["decision_status"]="UNAVAILABLE_MODEL_ONLY";item["decision_error"]=str(exc)[:140]
   rotation=rotation_from_official_inputs(gate,[],now)
   item["rotation"]={k:v["rotation_label"] for k,v in rotation["teams"].items()}
  except (ValueError,OSError,KeyError,TypeError,AssertionError) as exc:
   item["reason"]=str(exc)[:200]
  outcomes.append(item)
 result={"schema":SCHEMA,"cohort":cohort,"day_turkey":day,
         "created_at_utc":now.isoformat(),"input_count":len(rows),
         "new_forecasts":sum(x["status"]=="REGISTERED_FOUR_MODELS_EXPERIMENTAL" for x in outcomes),
         "blocked":sum(x["status"]=="BLOCKED_NO_FORECAST" for x in outcomes),
         "already_sealed":sum(x["status"]=="ALREADY_SEALED_UNCHANGED" for x in outcomes),
         "outcomes":outcomes,"odds_api_calls":0,
         "official_S1_S2_approved":False,"betting_authorized":False}
 result["payload_sha256"]=sha(result)
 return result

def precommit(report,root=".",now=None):
 now=now or datetime.now(timezone.utc)
 if now.tzinfo is None:raise Blocked("AWARE_TIME_REQUIRED")
 if report.get("schema")!=SCHEMA or report.get("payload_sha256")!=sha({k:v for k,v in report.items() if k!="payload_sha256"}):
  raise Blocked("BATCH_REPORT_SHA_CHANGED")
 root=Path(root).resolve()
 for r in report["outcomes"]:
  if r["status"]!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
  rel=r["forecast_path"]
  if not re.fullmatch(r"(forward_quad_263|forward_morning_263)/\d{4}-\d{2}-\d{2}/[0-9a-f]{24}\.json",rel):
   raise Blocked("UNSAFE_FORWARD_PATH")
  file=(root/rel).resolve()
  if not file.is_relative_to(root):raise Blocked("PATH_ESCAPES_REPO")
  f=json.loads(file.read_text(encoding="utf-8"));sealed_payload(f,"quad_forward_263_v1")
  if (f["payload_sha256"]!=r["forecast_sha256"]
   or f["fixture"].get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE"
   or not (read_aware(f["created_at_utc"])<=now and
            now+timedelta(minutes=2)<read_aware(f["fixture"]["kickoff_utc"]))):
   raise Blocked("FORECAST_NOT_PREKICKOFF_AT_COMMIT")
 return True

def mobile(report):
 lines=["# 2.6.3 Sabah toplu — "+report["day_turkey"],"",
        "**"+report["cohort"]+"** · yeni kayıt "+str(report["new_forecasts"])+
        " · engelli "+str(report["blocked"])+
        " · önceki kayıt "+str(report["already_sealed"]),"",
        "S1/S2 onaylı değil. Pinnacle oranı henüz sorgulanmadı.",""]
 for x in report["outcomes"]:
  lines+=["## "+x["home"].replace("|","/")+" – "+x["away"].replace("|","/"),"",
          "Durum: "+x["status"]]
  if "forecast_sha256" in x:
   lines+=["Tahmin SHA: "+x["forecast_sha256"],
            "Başlama UTC: "+x["kickoff_utc"],
            "Karar: "+x.get("decision_status","MODEL_ONLY"),
            "Rotasyon: "+", ".join(x.get("rotation",{}).values())]
  else:lines.append("Neden: "+x.get("reason","Önceden kaydedilmiş olabilir"))
  lines.append("")
 return "\n".join(lines)

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--cohort",choices=sorted(DIRS),required=True)
 p.add_argument("--day",required=True);p.add_argument("--input",required=True)
 p.add_argument("--history",required=True);p.add_argument("--baseline",required=True)
 p.add_argument("--source-acceptance",required=True)
 p.add_argument("--m4-lock",default="experiments/263/m4_lock.json")
 p.add_argument("--dev-lock",default="experiments/263/forward_dev_calibration_lock_263.json")
 p.add_argument("--report",required=True);p.add_argument("--mobile",required=True)
 p.add_argument("--verify-precommit",action="store_true")
 a=p.parse_args()
 if a.verify_precommit:
  x=json.loads(Path(a.report).read_text(encoding="utf-8"))
  precommit(x);print("PRECOMMIT_OK",x["new_forecasts"]);return
 x=run(a.cohort,a.day,a.input,a.history,a.baseline,a.source_acceptance,a.m4_lock,dev_lock_path=a.dev_lock)
 save_new(a.report,x);save_new(a.mobile,mobile(x))
 print(json.dumps({"new":x["new_forecasts"],"blocked":x["blocked"],"already":x["already_sealed"]}))
if __name__=="__main__":main()
