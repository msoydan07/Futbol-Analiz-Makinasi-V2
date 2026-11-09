"""Read-only research adapter: owner-accepted 2.6.3 scores -> XGBoost rows.

This is a SECOND training context (10 league canonical IDs), not the
previous 20-league OpenFootball-trained model. Do not mislabel evaluation
performance as transferable. No existing 2.6.3 file is modified.

Inputs are the immutable snapshot file and its accepted-source manifest.
The manifest says scores were accepted for limited experimental research;
it explicitly disclaims independent score verification. Preserve that.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json
from collections import Counter
from datetime import date,datetime,timezone
from pathlib import Path
from prospective_seal import KNOWN_LEAGUES,dt

SCHEMA="MC_263_RESEARCH_SNAPSHOT_BRIDGE_V1"
FIELDS=("league","season","date","home","away","home_goals",
        "away_goals","source_file","source_sha256")

def transform(csv_bytes,acceptance,*,asof):
    if (acceptance.get("schema")!="263_owner_accepted_research_source_v1"
       or acceptance.get("research_only") is not True
       or acceptance.get("betting_authorized") is not False
       or acceptance.get("review_scope")!="OWNER_READ_EVIDENCE_SUMMARY_AND_ACCEPTED_LIMITED_EXPERIMENTAL_RESEARCH_USE"):
        raise ValueError("not explicitly owner-accepted research history")
    reviewed=dt(acceptance["reviewed_at_utc"])
    asof=dt(asof.isoformat())
    if reviewed>asof:raise ValueError("source reviewed in future")
    rawsha=hashlib.sha256(csv_bytes).hexdigest()
    if rawsha!=acceptance.get("snapshot_sha256"):
        raise ValueError("accepted snapshot SHA does not match exact historical bytes")
    rows=list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
    required={"fixture_id","league","season","match_date",
              "home_id","away_id","home_goals","away_goals","result"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("invalid 2.6.3 history fields")
    seen=set();out=[];leagues=Counter()
    for r in rows:
        if r["league"] not in KNOWN_LEAGUES:
            raise ValueError("out of scope league")
        day=date.fromisoformat(r["match_date"])
        if day>=asof.date():raise ValueError("future or same-day score in archive")
        if r["home_id"]==r["away_id"] or not r["fixture_id"] or not r["home_id"] or not r["away_id"]:
            raise ValueError("invalid team/fixture identity")
        k=(r["league"],r["match_date"],r["home_id"],r["away_id"])
        if k in seen:raise ValueError("duplicated fixture")
        seen.add(k)
        try:h,a=int(r["home_goals"]),int(r["away_goals"])
        except (ValueError,TypeError) as exc:raise ValueError("bad goal value") from exc
        if min(h,a)<0 or max(h,a)>30 or r["result"]!=("H" if h>a else "A" if a>h else "D"):
            raise ValueError("score/result inconsistent")
        out.append({"league":r["league"],"season":r["season"],
             "date":r["match_date"],"home":r["home_id"],"away":r["away_id"],
             "home_goals":str(h),"away_goals":str(a),
             "source_file":"data/quad_accepted_263/extended_history.csv",
             "source_sha256":rawsha})
        leagues[r["league"]]+=1
    if len(out)<3000 or len(leagues)!=10 or min(leagues.values())<100:
        raise ValueError("owner accepted scores have insufficient coverage")
    return out,{"schema":SCHEMA,"history_sha256":rawsha,
        "history_count":len(out),"league_counts":dict(sorted(leagues.items())),
        "latest_result_date":max(r["date"] for r in out),
        "owner_accepted_manifest_snapshot_sha":acceptance["snapshot_sha256"],
        "accepted_for_limited_research":True,
        "independent_result_verification":False,
        "time_cutoff":asof.isoformat(),
        "model_not_yet_retrained_or_backtested_on_this_scope":True,
        "betting_authorized":False}

def build(history,acceptance,out,now=None):
    now=now or datetime.now(timezone.utc)
    rows,report=transform(Path(history).read_bytes(),
         json.loads(Path(acceptance).read_text(encoding="utf8")),asof=now)
    target=Path(out);target.mkdir(parents=True,exist_ok=True)
    with (target/"normalized_263_research.csv").open("w",encoding="utf8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    (target/"snapshot_bridge_audit.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps(report,ensure_ascii=False))
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",default="data/quad_accepted_263/extended_history.csv")
    p.add_argument("--acceptance",default="data/quad_accepted_263/source_acceptance.json")
    p.add_argument("--out",required=True)
    a=p.parse_args();build(a.history,a.acceptance,a.out)
if __name__=="__main__":main()
