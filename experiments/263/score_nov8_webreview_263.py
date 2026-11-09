"""Read-only 8 Nov 2026 WEB-REVIEW research scoreboard against real pre-KO SHA seals.

Not the official new100 human-attested results pipeline. No writes into any
forecast / score-attestation folders, no prediction refits, no odds/EV.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path
import hashlib,json,math,re

ROOT=Path(__file__).resolve().parents[2]
DAY="2026-11-08"
MODELS=("B","C2","C3","M4")
OVER=("OVER_1.5","OVER_2.5","OVER_3.5")
REPORTS=("new100_42469245388.json","new100_42469487639.json")
class AuditBlocked(ValueError): pass

def jload(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def aware(v):
    d=datetime.fromisoformat(v.replace("Z","+00:00"))
    if d.tzinfo is None: raise AuditBlocked("NAIVE_TIMESTAMP")
    return d.astimezone(timezone.utc)
def score_1x2(p,goals):
    if not isinstance(p,dict) or set(p)!={"H","D","A"} or any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) or not 0<=x<=1 for x in p.values()) or abs(sum(p.values())-1)>0.0001:
        raise AuditBlocked("INVALID_1X2_PROBABILITIES")
    h,a=goals
    target="H" if h>a else "D" if h==a else "A"
    return {"brier":sum((float(p[k])-int(k==target))**2 for k in ("H","D","A")),
            "logloss":-math.log(max(float(p[target]),1e-15)),
            "direction":int(max(("H","D","A"),key=lambda k:p[k])==target)}
def binary(p,y):
    if not isinstance(p,(int,float)) or isinstance(p,bool) or not math.isfinite(p) or not 0<=p<=1:
        raise AuditBlocked("INVALID_BINARY_PROBABILITY")
    return {"brier":(p-y)**2,"logloss":-(y*math.log(max(p,1e-15))+(1-y)*math.log(max(1-p,1e-15))),
            "direction":int((p>=0.5)==bool(y))}

def avg(items):
    return {"n":len(items),"direction_correct":sum(x["direction"] for x in items),
            "direction_pct":round(100*sum(x["direction"] for x in items)/len(items),2) if items else None,
            "brier":round(sum(x["brier"] for x in items)/len(items),6) if items else None,
            "logloss":round(sum(x["logloss"] for x in items)/len(items),6) if items else None}

def audit(root=ROOT):
    root=Path(root)
    data=jload(root/"experiments/263/nov8_webreview_results_263.json")
    rows=data["rows"]
    if data["schema"]!="263_NOV8_WEB_REVIEW_RESEARCH_ONLY_V1" or data["day_turkey"]!=DAY or len(rows)!=40 or data["new100_accepted_results"]!=0:
        raise AuditBlocked("RESEARCH_OVERLAY_SCHEMA_MISMATCH")
    key=lambda x:(x["league"],x["home"],x["away"])
    reviewed={}
    for row in rows:
        k=key(row)
        if k in reviewed or not row["source_url"].startswith("https://"):raise AuditBlocked("DUPLICATE_OR_BAD_SOURCE")
        if row["source_class"] not in ("PRIMARY_LEAGUE_OR_CLUB","MEDIA_CROSSCHECKED_NOT_LEAGUE_OFFICIAL"):
            raise AuditBlocked("BAD_SOURCE_CLASS")
        if row["source_class"]=="MEDIA_CROSSCHECKED_NOT_LEAGUE_OFFICIAL" and not str(row["crosscheck_url"]).startswith("https://"):
            raise AuditBlocked("MEDIA_REQUIRES_SECOND_SOURCE")
        if row["status"]=="FULL_TIME":
            if any(type(row[z]) is not int or not 0<=row[z]<=20 for z in ("home_goals","away_goals")):
                raise AuditBlocked("INVALID_SCORE")
        elif row["status"]=="POSTPONED" and row["home_goals"] is None and row["away_goals"] is None:
            pass
        else:raise AuditBlocked("INVALID_RESULT_STATUS")
        reviewed[k]=row
    registered={}
    for name in REPORTS:
        batch=jload(root/"experiments/263/sabah_batch_reports"/name)
        if batch.get("schema")!="SABAH_TOPLU_KAYIT_V1" or batch.get("cohort")!="new100" or batch.get("day_turkey")!=DAY:
            raise AuditBlocked("BATCH_RESEARCH_MISMATCH")
        for outcome in batch["outcomes"]:
            if outcome.get("status")!="REGISTERED_FOUR_MODELS_EXPERIMENTAL":continue
            k=key(outcome)
            if k in registered:raise AuditBlocked("DUPLICATE_FIXTURE_BETWEEN_BATCHES")
            rel=outcome["forecast_path"]
            if not re.fullmatch(r"forward_morning_263/2026-11-08/[0-9a-f]{24}\.json",rel):
                raise AuditBlocked("FORECAST_PATH_NOT_LOCKED")
            sealed=jload(root/rel)
            actual=digest({k:v for k,v in sealed.items() if k!="payload_sha256"})
            if actual!=sealed["payload_sha256"] or actual!=outcome["forecast_sha256"]:
                raise AuditBlocked("SEALED_FORECAST_SHA_MISMATCH")
            fixture=sealed["fixture"]
            if fixture["league"]!=outcome["league"] or fixture["match_local_date"]!=DAY or fixture.get("fixture_verification")!="VERIFIED_BY_LIVE_OFFICIAL_GATE":
                raise AuditBlocked("FIXTURE_PROVENANCE_MISMATCH")
            if fixture["kickoff_utc"]!=outcome["kickoff_utc"]:
                raise AuditBlocked("KICKOFF_MISMATCH")
            made=aware(sealed["created_at_utc"]);checked=aware(fixture["source_checked_at_utc"]);ko=aware(fixture["kickoff_utc"])
            if not(made<ko and checked<ko and checked<=made+timedelta(seconds=1)):
                raise AuditBlocked("NO_PROVEN_PREMATCH_SHA_SEAL")
            registered[k]=sealed
    if set(registered)!=set(reviewed) or len(registered)!=40:
        missing=list(set(registered)-set(reviewed));extra=list(set(reviewed)-set(registered))
        raise AuditBlocked("MATCH_IDENTITY_NOT_40_TO_40:"+repr([missing,extra]))
    grouped={c:defaultdict(list) for c in ("ALL_WEB_REVIEW","PRIMARY_ONLY","MEDIA_CROSSCHECK_ONLY")}
    paired=defaultdict(list);statuses=defaultdict(int);matches=[]
    for k in sorted(registered):
        f=registered[k];row=reviewed[k];statuses[row["status"]]+=1
        if row["status"]=="POSTPONED":
            matches.append({"match":" – ".join(k[1:]),"league":k[0],"status":"POSTPONED_NO_SCORE","source_url":row["source_url"]})
            continue
        y=(row["home_goals"],row["away_goals"])
        classification="MEDIA_CROSSCHECK_ONLY" if row["source_class"]=="MEDIA_CROSSCHECKED_NOT_LEAGUE_OFFICIAL" else "PRIMARY_ONLY"
        scores={}
        for name in MODELS:
            model=f.get("model_predictions",{}).get(name,{})
            if model.get("status")!="AVAILABLE":continue
            market=model["goals"]["markets"]
            scores[name]={"MS":score_1x2(market["1X2"],y),
                 "KG":binary(market["BTTS_YES"],int(min(y)>0)),
                 **{over:binary(market[over],int(sum(y)>float(over[5:]))) for over in OVER}}
            for cat in ("ALL_WEB_REVIEW",classification):
                for marketname,score in scores[name].items():
                    grouped[cat][(name,marketname)].append(score)
        if "M4" in scores:
            for other in ("B","C2","C3"):
                if other in scores:paired[other].append(scores[other]["MS"]["brier"]-scores["M4"]["MS"]["brier"])
        matches.append({"league":k[0],"match":" – ".join(k[1:]),"status":row["status"],
             "score":list(y),"source_class":row["source_class"],"source_url":row["source_url"],
             "models_available":list(scores)})
    overview={}
    for cat,agg in grouped.items():
        overview[cat]={model:{market:avg(agg[(model,market)]) for market in ("MS","KG",*OVER)} for model in MODELS}
    result={"schema":"263_NOV8_WEB_REVIEW_SCORED_RESEARCH_ONLY_V1","status":"EVIDENCE_GROUPED_DESCRIPTIVE_NO_MODEL_PROMOTION",
        "reviewed_date":"2026-11-09","sealed_registered":len(registered),
        "scored":statuses["FULL_TIME"],"postponed":statuses["POSTPONED"],
        "source_counts":{"primary_scored":sum(x["source_class"]=="PRIMARY_LEAGUE_OR_CLUB" and x["status"]=="FULL_TIME" for x in rows),
                         "media_crosschecked_scored":sum(x["source_class"]=="MEDIA_CROSSCHECKED_NOT_LEAGUE_OFFICIAL" and x["status"]=="FULL_TIME" for x in rows)},
        "model_scores":overview,"same_match_MS_Brier_other_minus_M4":{
             k:{"n":len(v),"mean":round(sum(v)/len(v),6) if v else None} for k,v in paired.items()},
        "matches":matches,"no_accepted_new100_attestations_written":True,
        "unmodified_preKO_SHA_forecasts":True,
        "no_refit_no_value_no_betting_claim":True,
        "caution":"Sources were assistant web-reviewed, NOT verified by live official network adapters in CI. Portugal four scores are media-crosschecked, not league official. No human-attested results were created. Counts do not imply 96 official pilot success."}
    return result

def markdown(r):
    lines=["# 2.6.3 — 8 Kasım sabah mühürleri gerçek skor araştırması","",
       "**Kaydedilmiş SHA:** "+str(r["sealed_registered"])+" · **Skoru bulunan:** "+str(r["scored"])+" · **Ertelenmiş:** "+str(r["postponed"]),
       "**Birincil lig/kulüp kaynaklı:** "+str(r["source_counts"]["primary_scored"])+
       " · **Medya çapraz kontrolü:** "+str(r["source_counts"]["media_crosschecked_scored"]),"",
       "**DİKKAT:** Bu salt okunur WEB araştırma karşılaştırmasıdır. Resmî new100 attestation kaydı değildir; eski mühürler değişmedi, eğitim/yeniden pilot yok.","",
       "## Dört model — aynı 8 Kasım kayıtları","",
       "| Model | MS N | MS yön | MS Brier | KG yön | 2,5 Üst/Alt yön |","---|---:|---:|---:|---:|---:|"]
    for name in MODELS:
        b=r["model_scores"]["ALL_WEB_REVIEW"][name]
        v=lambda p:"—" if p is None else str(p)
        lines.append(f"| {name} | {b['MS']['n']} | {v(b['MS']['direction_correct'])}/{b['MS']['n']} (%{v(b['MS']['direction_pct'])}) | {v(b['MS']['brier'])} | {v(b['KG']['direction_correct'])}/{b['KG']['n']} | {v(b['OVER_2.5']['direction_correct'])}/{b['OVER_2.5']['n']} |")
    lines+=["","## Birincil kaynaklı maçlarla sınırlı kontrol",
      "", "| Model | N | MS yön | MS Brier |","|---|---:|---:|---:|"]
    for name in MODELS:
        q=r["model_scores"]["PRIMARY_ONLY"][name]["MS"]
        lines.append(f"| {name} | {q['n']} | {q['direction_correct']}/{q['n']} | {q['brier']} |")
    lines+=["","## Tek tek araştırma sonuçları","","| Lig | Maç | Skor | Kaynak sınıfı |","|---|---|---:|---|"]
    for item in r["matches"]:
        lines.append(f"| {item['league']} | {item['match']} | {('-' if item['status']=='POSTPONED_NO_SCORE' else str(item['score'][0])+'-'+str(item['score'][1]))} | {item.get('source_class','POSTPONED')} |")
    lines+=["","Kaynak URL'leri ve karşılaşma kimliği JSON'dadır. M4 ana kullanım kararı değişmedi; maç başına tahmin sonuçları garanti etmez."]
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True);ap.add_argument("--mobile",required=True)
    args=ap.parse_args()
    r=audit()
    Path(args.out).write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    Path(args.mobile).write_text(markdown(r),encoding="utf-8")
    print(json.dumps({k:r[k] for k in ("status","sealed_registered","scored","postponed","source_counts","same_match_MS_Brier_other_minus_M4")},ensure_ascii=False,sort_keys=True))
    for scope in ("ALL_WEB_REVIEW","PRIMARY_ONLY"):
        print(scope,json.dumps({model:{m:r["model_scores"][scope][model][m] for m in ("MS","KG","OVER_2.5")} for model in MODELS},ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
