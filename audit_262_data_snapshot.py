"""One-run 2.6.2 data acceptance inventory; first-half corners excluded.
Read-only source inspection; writes only a JSON report. Missing xG is a gap, not fabricated.
"""
import csv
import json
from collections import Counter
from pathlib import Path

DATA = Path("data")
LEAGUES = ("ENG1","ENG2","GER1","ESP1","ITA1","FRA1","NED1","TUR1","POR1","BEL1")
SEASONS = ("2025-2026","2026-2027")
GROUPS = {
    "result": ("home_goals","away_goals","result"),
    "half_time_result": ("half_time_home_goals","half_time_away_goals","half_time_result"),
    "shots": ("home_shots","away_shots"),
    "shots_on_target": ("home_shots_on_target","away_shots_on_target"),
    "full_time_corners": ("home_corners","away_corners"),
    "fouls": ("home_fouls","away_fouls"),
    "yellow_cards": ("home_yellow_cards","away_yellow_cards"),
    "red_cards": ("home_red_cards","away_red_cards"),
}
def read(filename):
    path=DATA/filename
    if not path.exists():
        return None
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def build():
    history=read("historical_results.csv")
    xg=read("historical_verified_xg.csv")
    audit_path=DATA/"historical_results_audit.json"
    audit=json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else None
    source=read("source_audit.csv")
    groups=[]
    issues=[]
    ids=set()
    if history is None:
        issues.append("HISTORICAL_RESULTS_NOT_PRODUCED")
        history=[]
    if xg is None:
        issues.append("VERIFIED_XG_NOT_PRODUCED")
        xg=[]
    if not audit or audit.get("accepted") is not True:
        issues.append("HISTORICAL_AUDIT_NOT_ACCEPTED")
    if not source or len(source)!=20 or any(r.get("status")!="OK" for r in source):
        issues.append("SOURCE_COVERAGE_NOT_ACCEPTED")
    for r in history:
        fid=r.get("fixture_id")
        if not fid or fid in ids:
            issues.append("MISSING_OR_DUPLICATE_FIXTURE_ID")
        ids.add(fid)
    xg_ids=set()
    for r in xg:
        fid=r.get("fixture_id")
        if not fid or fid in xg_ids or fid not in ids:
            issues.append("INVALID_XG_FIXTURE_LINK")
        xg_ids.add(fid)
        try:
            import math
            if not all(math.isfinite(float(r[k])) and float(r[k])>=0 for k in ("home_xg","away_xg")):
                issues.append("INVALID_XG_VALUE")
        except (ValueError,KeyError,TypeError):
            issues.append("INVALID_XG_VALUE")
    for league in LEAGUES:
        for season in SEASONS:
            matches=[r for r in history if r.get("league")==league and r.get("season")==season]
            n=len(matches)
            if not n:
                issues.append("EMPTY_GROUP:"+league+"/"+season)
            coverage={}
            for name,fields in GROUPS.items():
                count=sum(all(r.get(k,"")!="" for k in fields) for r in matches)
                coverage[name]={"present":count,"missing":n-count}
            linked=sum(r.get("fixture_id") in xg_ids for r in matches)
            coverage["verified_xg"]={"present":linked,"missing":n-linked}
            groups.append({"league":league,"season":season,"matches":n,"coverage":coverage})
    totals={name:{"present":sum(g["coverage"][name]["present"] for g in groups),
                  "missing":sum(g["coverage"][name]["missing"] for g in groups)}
            for name in (*GROUPS,"verified_xg")}
    report={"version":"262_data_acceptance_snapshot_v1","league_season_groups":20,
            "historical_matches":len(history),"verified_xg_matches":len(xg),
            "coverage_totals":totals,"by_league_season":groups,
            "excluded_by_decision":["first_half_corners"],
            "not_yet_integrated":["injuries","suspensions","lineups","odds_and_timestamp","referee","tactical_context"],
            "issues":sorted(set(issues)),
            "status":"READY_FOR_DATA_REVIEW" if not issues else "INCOMPLETE",
            "note":"Coverage is not independent statistical accuracy; missing xG is never estimated as observed xG."}
    DATA.mkdir(exist_ok=True)
    (DATA/"262_data_acceptance_snapshot.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"historical_matches":len(history),
                      "verified_xg_matches":len(xg),"coverage_totals":totals,"issues":report["issues"]},ensure_ascii=False))
    return report
if __name__=="__main__":
    build()
