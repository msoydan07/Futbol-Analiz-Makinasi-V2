"""Read-only aggregate inventory for audited xG CSV; never exports match-level rows."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

LEAGUES = ("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
SEASONS = ("2025-2026","2026-2027")
REQUIRED = {"fixture_id","league","season","match_date","home_id","away_id","home_xg","away_xg"}

def inventory(xg_path, audit_path, out_path):
    audit = json.loads(Path(audit_path).read_text(encoding="utf-8"))
    with Path(xg_path).open(encoding="utf-8-sig",newline="") as f:
        reader = csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError("Missing required audited xG columns")
        rows = list(reader)
    if audit.get("verified_xg_rows") != len(rows) or audit.get("prediction_engine_modified") is not False:
        raise ValueError("Audit count/read-only contract mismatch")
    seen=set();counts=Counter();bad=Counter()
    for r in rows:
        fid=r["fixture_id"]
        if not fid or fid in seen: raise ValueError("Duplicate/blank fixture ID")
        seen.add(fid)
        league,season=r["league"],r["season"]
        if league not in LEAGUES or season not in SEASONS: raise ValueError("Unexpected league or season")
        for key in ("home_xg","away_xg"):
            import math
            try: v=float(r[key])
            except (ValueError,TypeError): raise ValueError("Non-numeric xG") from None
            if not math.isfinite(v) or not 0<=v<=15: raise ValueError("Invalid xG")
        counts[(league,season)]+=1
    report={"status":"AUDITED_FILE_AGGREGATE_ONLY_NOT_LIVE_SOURCE_VERIFICATION",
            "total_verified_rows":len(rows),"audit_verified_rows":audit["verified_xg_rows"],
            "asof_rule":audit.get("prediction_asof_rule"),
            "league_season":[{"league":l,"season":s,"verified_rows":counts[(l,s)]} for l in LEAGUES for s in SEASONS],
            "raw_match_rows_exported":False,"m4_xg_test_performed":False,
            "model_modified":False}
    Path(out_path).parent.mkdir(parents=True,exist_ok=True)
    Path(out_path).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--xg",required=True);p.add_argument("--audit",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();inventory(a.xg,a.audit,a.output)
