"""Export verified Understat xG joined to immutable fixture IDs.

Only MATCHED audit rows are included. No estimates, fuzzy matches or future data.
Outputs historical xG observations; prediction code must filter match_date < target_date.
"""
import csv
import json
import math
from collections import Counter
from pathlib import Path

ROOT=Path("data")
FIELDS=["fixture_id","league","season","match_date","home_id","away_id",
        "home_goals","away_goals","home_xg","away_xg","understat_source_url"]

def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def build():
    historical=read(ROOT/"historical_results.csv")
    sources=read(ROOT/"understat_matches.csv")
    audit=read(ROOT/"understat_xg_match_audit.csv")
    by_id={r["fixture_id"]:r for r in historical}
    if len(by_id)!=len(historical):
        raise ValueError("Duplicate historical fixture IDs")
    output=[]
    seen=set()
    rejected=Counter()
    for a in audit:
        if a["status"]!="MATCHED":
            rejected[a["status"]]+=1
            continue
        idx=int(a["source_row"])-2
        if idx<0 or idx>=len(sources):
            raise ValueError("Invalid source_row")
        s=sources[idx]
        h=by_id.get(a["fixture_id"])
        if h is None or a["fixture_id"] in seen:
            raise ValueError("Missing or duplicated matched fixture")
        if (s["league"],s["season"])!=(h["league"],h["season"]):
            raise ValueError("League/season mismatch")
        if (int(s["home_goals"]),int(s["away_goals"]))!=(int(h["home_goals"]),int(h["away_goals"])):
            raise ValueError("Score mismatch")
        values=[float(s["home_xg"]),float(s["away_xg"])]
        if not all(math.isfinite(v) and v>=0 for v in values):
            raise ValueError("Invalid xG")
        seen.add(a["fixture_id"])
        output.append({k:h[k] for k in FIELDS[:8]} | {
            "home_xg":s["home_xg"],"away_xg":s["away_xg"],
            "understat_source_url":s["source_url"]})
    output.sort(key=lambda r:(r["match_date"],r["league"],r["fixture_id"]))
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/"historical_verified_xg.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader();writer.writerows(output)
    report={"verified_xg_rows":len(output),"historical_rows":len(historical),
            "source_rows":len(sources),"audit_rows":len(audit),
            "rejected_by_status":dict(rejected),
            "prediction_asof_rule":"match_date strictly earlier than target match_date",
            "same_day_rule":"exclude all same-date observations unless verified kickoff timestamps exist",
            "prediction_engine_modified":False}
    (ROOT/"historical_verified_xg_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if len(output)!=sum(a["status"]=="MATCHED" for a in audit):
        raise ValueError("Audit matched count mismatch")

if __name__=="__main__":
    build()
